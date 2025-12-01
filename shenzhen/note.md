## 1. Cơ Chế Crawl (Thu thập dữ liệu)

### 1.1. Giao thức kết nối
*   **Target:** API Search của chính quyền Quảng Đông (`https://search.gd.gov.cn/api/search/all`).
*   **Method:** `POST` Request với payload JSON.
*   **Headers:** Giả lập trình duyệt (User-Agent Chrome) để tránh bị chặn.
*   **Timeout:** Thiết lập `timeout=30s` để xử lý các phản hồi chậm từ server (tránh lỗi `ReadTimedOut`).

### 1.2. Chiến lược Vòng lặp (Loop Strategy)
Script hoạt động theo mô hình 2 vòng lặp lồng nhau:
1.  **Vòng lặp Từ khóa:** Duyệt qua danh sách `["加装电梯", "增设电梯"]` (Lắp đặt/Gắn thêm thang máy). Việc dùng 2 từ khóa giúp bao phủ cả văn bản cũ và mới.
2.  **Vòng lặp Phân trang:** Với mỗi từ khóa, script chạy từ `page=1` đến hết.
    *   Tự động tính tổng số trang dựa trên `total_items` trả về ở request đầu tiên.
    *   Cơ chế `time.sleep(1)` giữa các lần chuyển trang để tránh quá tải server.

---

## 2. Quy Trình Xử Lý Dữ Liệu (Data Pipeline)

Dữ liệu thô (Raw Title) đi qua **4 lớp lọc và xử lý** nghiêm ngặt trước khi được chấp nhận.

### Lớp 1: Bộ Lọc Thô (Pre-filtering)
Loại bỏ ngay lập tức các kết quả không liên quan dựa trên tiêu đề gốc.
*   **Input:** Tiêu đề gốc (Raw Title).
*   **Logic:** Kiểm tra sự tồn tại của từ khóa trong **Blacklist** (`IRRELEVANT_KEYWORDS`).
*   **Các nhóm bị loại bỏ:**
    *   **Thương mại/Đấu thầu:** `采购` (Mua sắm), `招标` (Đấu thầu), `公司` (Công ty), `有限公司` (TNHH).
    *   **Hạ tầng kỹ thuật:** `供电` (Điện lực), `地铁` (Tàu điện), `大桥` (Cầu).
    *   **Công trình công cộng:** `学校` (Trường học), `医院` (Bệnh viện), `派出所` (Đồn công an).
    *   **Tin tức/Họp hành:** `会议` (Hội nghị), `调研` (Khảo sát), `代表` (Đại biểu).
    *   **Văn bản chính sách:** `印发` (Ban hành), `导则` (Hướng dẫn), `通知` (Thông báo).

### Lớp 2: Làm Sạch Chuỗi (Smart Cleaning)
Mục tiêu: Gọt bỏ các thành phần hành chính để lộ ra tên địa chỉ cốt lõi. Hàm `clean_title_smart` thực hiện các bước:

1.  **Cắt mốc "Về việc" (`关于`):**
    *   Nếu tiêu đề có chữ `关于`, script cắt bỏ toàn bộ phần phía trước, chỉ lấy phần phía sau.
    *   *Ví dụ:* `Sở Quy hoạch Nam Sơn Về việc [Chung cư A]...` -> `[Chung cư A]...`
    *   Nếu không có `关于`, dùng Regex xóa tên cơ quan (`管理局`, `委员会`, `政府`) ở đầu chuỗi.

2.  **Xóa Tiền tố (Prefix Loop):**
    *   Sử dụng vòng lặp `while` để cắt liên tục các từ thừa ở đầu chuỗi cho đến khi sạch.
    *   **Từ khóa xóa:** `公布` (Công bố), `举行` (Tổ chức), `深圳市`, `南山区`... (Tên địa danh lặp lại).
    *   *Ví dụ:* `Công bố Quận Nam Sơn Chung cư B...` -> `Chung cư B...`

3.  **Cắt Hậu tố & Hành động (Truncate):**
    *   Tìm vị trí các từ khóa hành động: `加装`, `增设`, `电梯` (Thang máy), `工程` (Công trình).
    *   Cắt bỏ toàn bộ nội dung từ từ khóa đó trở về sau.
    *   *Ví dụ:* `Chung cư C Lắp đặt thang máy số 1` -> `Chung cư C`.

### Lớp 3: Trích Xuất Thông Tin (Extraction)
Sử dụng 2 chiến lược Regex để tách tên chung cư (`xiaoqu`), số tòa (`dongshu`) và đơn nguyên (`danyuan`).

*   **Chiến lược 1 (Ưu tiên - Strict):** Tìm mẫu `Tên` + `Số` + `Đơn vị`.
    *   Regex: `(.+?)(\d+[栋号幢楼座])(\d*单元)?`
    *   *Giải thích:* Tìm chuỗi bất kỳ, theo sau là số + (Đống/Hào/Lầu), theo sau là số + (Đơn nguyên).
*   **Chiến lược 2 (Dự phòng - Suffix Check):**
    *   Nếu Chiến lược 1 thất bại (không có số tòa), script kiểm tra xem tên còn lại có kết thúc bằng từ khóa nhà ở không (`花园`, `小区`, `苑`, `大厦`...).
    *   Nếu có, chấp nhận lấy tên đó làm `xiaoqu` (các cột số tòa để trống).

### Lớp 4: Kiểm Tra Hợp Lệ (Validation)
Hàm `is_valid_xiaoqu` kiểm tra lần cuối tên `xiaoqu` vừa tách được.
*   **Chặn tên chung chung:** Loại bỏ nếu tên là `既有住宅` (Nhà ở hiện hữu), `老旧小区` (Khu phố cũ).
*   **Chặn tên cơ quan sót:** Nếu tên vẫn còn chữ `局` (Cục), `委` (Sở), `规划` (Quy hoạch) -> Loại bỏ.
*   **Chặn ký tự lạ:** Nếu tên bắt đầu bằng số hoặc ký tự đặc biệt -> Loại bỏ.

---

## 3. Các Logic Phụ Trợ

### 3.1. Xác định Quận (`get_district`)
*   Quét tiêu đề và nội dung bài viết.
*   Đối chiếu với danh sách tên quận (`SHENZHEN_DISTRICTS`) và các địa danh nổi tiếng (Keyword Mapping) để gán quận tương ứng.

### 3.2. Cơ chế Lưu trữ (Storage)
*   **Reset:** Trước khi chạy, script kiểm tra file Excel đích. Nếu tồn tại -> **Xóa vĩnh viễn** (`os.remove`) để đảm bảo dữ liệu mới không bị trộn lẫn với dữ liệu cũ.
*   **Write:** Tạo Workbook mới và ghi toàn bộ dữ liệu sạch vào một lần duy nhất khi kết thúc quá trình crawl.

---

## 4. Tóm tắt Luồng Dữ Liệu (Flowchart dạng Text)

```text
[START] 
  |--> Xóa Excel cũ
  |--> Loop Keywords:
        |--> Loop Pages:
              |--> Request API
              |--> Loop Items (Titles):
                    |
                    |--> [FILTER] Tiêu đề có chứa từ khóa Rác/Quảng cáo/Tin tức?
                    |       |-- YES --> Bỏ qua
                    |       |-- NO  --> Tiếp tục
                    |
                    |--> [CLEAN] Cắt 'Về việc', Cắt Tên Cơ quan, Cắt 'Công bố/Tổ chức'
                    |            Cắt đuôi 'Lắp thang máy/Công trình'
                    |
                    |--> [EXTRACT] Regex tìm Tên + Số tòa + Đơn nguyên
                    |       |-- Tìm thấy Số tòa --> OK
                    |       |-- Không thấy --> Check đuôi 'Garden/Village' --> OK
                    |
                    |--> [VALIDATE] Tên có phải là 'Nhà ở hiện hữu' hay 'Cục'?
                    |       |-- YES --> Bỏ qua
                    |       |-- NO  --> Lưu vào List
                    |
[END] --> Ghi List vào Excel
```