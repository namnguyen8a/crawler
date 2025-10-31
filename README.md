# Web Scraper Nâng cao cho Thông báo của Quận Dương Phố, Thượng Hải

## Giới thiệu

Đây là một script Python mạnh mẽ được thiết kế để thu thập dữ liệu quy mô lớn từ trang web công bố các phương án quy hoạch của Quận Dương Phố, Thượng Hải. Script có khả năng tự động duyệt qua toàn bộ 251 trang, phân tích và bóc tách thông tin từ các định dạng tiêu đề không đồng nhất, và lưu kết quả vào file Excel một cách an toàn và bền bỉ.

Nó được trang bị các tính năng chuyên nghiệp như khả năng phục hồi sau lỗi (resume from checkpoint) và cơ chế thử lại (retry), đảm bảo quá trình thu thập dữ liệu dài hơi diễn ra một cách đáng tin cậy.

## Chức năng chính

-   **Thu thập đa trang (Multi-page Crawling):** Tự động tạo URL và duyệt qua toàn bộ 251 trang của danh sách thông báo.
-   **Khả năng phục hồi (Checkpointing):** Tự động lưu lại tiến trình vào file `checkpoint.log` sau mỗi trang. Nếu script bị gián đoạn, lần chạy tiếp theo sẽ **tự động tiếp tục** từ trang chưa hoàn thành, tiết kiệm thời gian và tài nguyên.
-   **Cơ chế thử lại (Retry Mechanism):** Tự động thử lại vài lần nếu gặp lỗi kết nối mạng tạm thời, tăng cường sự ổn định của quá trình thu thập.
-   **Phân tích tiêu đề thông minh (Intelligent Parsing):**
    -   Sử dụng logic "Hybrid" (kết hợp Regex và danh sách từ khóa) để bóc tách thông tin từ các định dạng tiêu đề phức tạp và đa dạng.
    -   Có khả năng xử lý cả thông báo về nhà ở dân dụng và các dự án công trình công cộng.
-   **Tách ngày tháng chi tiết:** Tự động tách chuỗi ngày tháng thành 3 cột riêng biệt: `年` (Năm), `月` (Tháng), và `日` (Ngày).
-   **Ghi dữ liệu an toàn vào Excel:**
    -   Thêm dữ liệu đã được trích xuất vào sheet có tên `shanghai` trong file `模版.xlsx`.
    -   Đảm bảo dữ liệu được ghi bắt đầu từ **cột B**, giữ nguyên cột A trống.
    -   **An toàn tuyệt đối:** Quá trình ghi file được thiết kế để **không bao giờ làm ảnh hưởng, thay đổi hay xóa** bất kỳ sheet nào khác có trong file Excel.
-   **Lưu trữ dữ liệu thô:** Ghi nối tiếp tất cả các tiêu đề gốc đã thu thập được vào file `crawled_titles.txt`.

## Cài đặt và Hướng dẫn sử dụng

### Yêu cầu

-   Python 3.9+ (khuyến nghị để có hàm `removesuffix`)

### Các bước cài đặt

Bạn có thể chọn một trong hai cách sau để cài đặt môi trường. **Cách 1 (dùng `uv`) được khuyến khích vì tốc độ nhanh.**

#### Cách 1: Sử dụng `uv` (Nhanh và hiện đại)

1.  **Cài đặt `uv`:**
    Nếu bạn chưa có, hãy cài đặt trình quản lý gói cực nhanh này.
    ```bash
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows (Powershell)
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

2.  **Tạo và kích hoạt môi trường ảo:**
    Mở terminal trong thư mục dự án và chạy các lệnh sau.
    ```bash
    # Tạo môi trường ảo
    uv venv
    
    # Kích hoạt môi trường
    # macOS / Linux
    source .venv/bin/activate
    # Windows (Command Prompt)
    .venv\Scripts\activate
    ```

3.  **Cài đặt các thư viện:**
    `uv` sẽ cài đặt các gói cần thiết một cách nhanh chóng.
    ```bash
    uv pip install requests beautifulsoup4 pandas openpyxl
    ```

#### Cách 2: Sử dụng `pip` (Thân thiện với người mới)

1.  **Tạo và kích hoạt môi trường ảo:**
    Mở terminal trong thư mục dự án.
    ```bash
    # Tạo môi trường ảo
    python -m venv .venv

    # Kích hoạt môi trường
    # macOS / Linux
    source .venv/bin/activate
    # Windows (Command Prompt)
    .venv\Scripts\activate
    ```

2.  **Cài đặt các thư viện:**
    Sử dụng `pip` để cài đặt các gói.
    ```bash
    pip install requests beautifulsoup4 pandas openpyxl
    ```

### Chuẩn bị và Chạy Script

1.  **Chuẩn bị file Excel mẫu:**
    -   Đây là một bước **bắt buộc**. Hãy tạo một file Excel trong cùng thư mục và đặt tên chính xác là `模版.xlsx`.
    -   Mở file lên và tạo các sheet bạn cần. Ví dụ: tạo một sheet tên `shenzhen` với định dạng bạn muốn và một sheet tên `shanghai` với các tiêu đề sau bắt đầu từ ô `B1`: `区`, `地址`, `年`, `月`, `日`.

2.  **Chạy script:**
    Sau khi đã hoàn tất các bước trên, chạy script bằng lệnh sau:
    ```bash
    python main.py
    ```
    Script sẽ bắt đầu quá trình thu thập. Nếu bị gián đoạn, chỉ cần chạy lại lệnh trên, nó sẽ tự động tiếp tục.

3.  **Để thu thập lại từ đầu:**
    Nếu bạn muốn xóa toàn bộ tiến trình và bắt đầu lại, hãy **xóa file `checkpoint.log`** một cách thủ công và chạy lại script.

## Giải thích các hàm quan trọng

Script được xây dựng dựa trên một vài hàm cốt lõi để đảm bảo sự chính xác và ổn định:

-   `parse_title_hybrid(title_text)`
    -   **Mục đích:** Đây là "bộ não" xử lý logic bóc tách thông tin từ các tiêu đề phức tạp.
    -   **Cách hoạt động:** Nó thực hiện một quy trình làm sạch đa tầng. Đầu tiên, nó dùng Regex để tìm và tách `杨浦区` (Quận). Sau đó, nó tìm vị trí của "từ khóa nhiễu" đầu tiên (như `项目`, `工程`, `方案`...) trong chuỗi còn lại và cắt bỏ mọi thứ từ vị trí đó trở về sau. Phần còn lại chính là tên địa chỉ/dự án đã được làm sạch. Cách tiếp cận này vừa thông minh vừa đảm bảo tốc độ cao.

-   `find_last_row_with_data(sheet)`
    -   **Mục đích:** Tìm chính xác hàng cuối cùng có chứa dữ liệu trong một sheet Excel.
    -   **Cách hoạt động:** Thay vì tin vào thuộc tính `sheet.max_row` (vốn có thể bị sai nếu người dùng đã xóa hàng), hàm này quét ngược từ dưới lên và dừng lại ở hàng đầu tiên nó tìm thấy có chứa bất kỳ dữ liệu nào. Điều này đảm bảo script luôn ghi dữ liệu mới vào đúng vị trí.

-   `read_checkpoint()` và `write_checkpoint(page_num)`
    -   **Mục đích:** Quản lý cơ chế phục hồi (resume).
    -   **Cách hoạt động:** `read_checkpoint` sẽ đọc số trang cuối cùng đã hoàn thành từ file `checkpoint.log`. `write_checkpoint` sẽ cập nhật số trang này sau mỗi lần thu thập thành công. Script sẽ không bao giờ tự động xóa file này, đặt toàn quyền kiểm soát vào tay người dùng.

## Hạn chế hiện tại

-   **Cấu hình được hard-coded:** Các thông tin như URL, tên file, và đặc biệt là danh sách các "từ khóa nhiễu" (`BOUNDARY_KEYWORDS`) đều đang được định nghĩa trực tiếp trong code.
-   **Phụ thuộc vào cấu trúc HTML:** Bộ chọn CSS (`ul.uli16...`) rất cụ thể cho cấu trúc hiện tại của trang web. Nếu trang web thay đổi layout, script sẽ cần được cập nhật.