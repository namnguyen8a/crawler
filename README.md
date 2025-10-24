# Web Scraper cho Thông báo của Quận Dương Phố, Thượng Hải

## Giới thiệu

Đây là một script Python được thiết kế để tự động thu thập dữ liệu từ trang web công bố các phương án quy hoạch của Quận Dương Phố, Thượng Hải. Script sẽ trích xuất thông tin về các dự án lắp đặt thang máy, bao gồm quận, địa chỉ và ngày công bố, sau đó lưu kết quả vào file một cách có tổ chức.

## Chức năng chính

-   **Thu thập dữ liệu (Crawling):** Tự động truy cập vào URL được chỉ định và tải về nội dung HTML của trang web.
-   **Lưu trữ dữ liệu thô:** Lưu lại tất cả các tiêu đề gốc đã thu thập được vào file `crawled_titles.txt` để tham chiếu và kiểm tra.
-   **Trích xuất thông tin:** Phân tích từng tiêu đề để bóc tách ra 3 trường thông tin quan trọng:
    -   `区` (Quận)
    -   `地址` (Địa chỉ)
    -   `公告日期` (Ngày công bố)
-   **Ghi dữ liệu an toàn vào Excel:**
    -   Thêm dữ liệu đã được trích xuất vào sheet có tên `shanghai` trong file `模版.xlsx`.
    -   **Đặc biệt:** Dữ liệu được ghi bắt đầu từ **cột B**, giữ nguyên cột A trống.
    -   **An toàn:** Quá trình ghi file được thiết kế để **không làm ảnh hưởng, thay đổi hay xóa** bất kỳ sheet nào khác có trong file Excel.

## Cài đặt và Hướng dẫn sử dụng

### Yêu cầu

-   Python 3.8+
-   `uv` (Một trình quản lý gói và môi trường ảo cực nhanh cho Python)

### Các bước cài đặt

1.  **Cài đặt `uv`:**
    Nếu bạn chưa có `uv`, hãy cài đặt nó.
    ```bash
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows (Powershell)
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

2.  **Tạo môi trường ảo:**
    Mở terminal trong thư mục dự án và chạy lệnh sau để tạo một môi trường ảo có tên là `.venv`.
    ```bash
    uv venv
    ```

3.  **Kích hoạt môi trường ảo:**
    ```bash
    # macOS / Linux
    source .venv/bin/activate

    # Windows (Command Prompt)
    .venv\Scripts\activate
    ```
    Sau khi kích hoạt, bạn sẽ thấy `(.venv)` ở đầu dòng lệnh.

4.  **Cài đặt các thư viện phụ thuộc:**
    Sử dụng `uv` để cài đặt các thư viện cần thiết một cách nhanh chóng.
    ```bash
    uv pip install requests beautifulsoup4 pandas openpyxl
    ```

5.  **Chuẩn bị file Excel mẫu:**
    -   Đây là một bước **bắt buộc**. Hãy tạo một file Excel trong cùng thư mục và đặt tên chính xác là `模版.xlsx`.
    -   Mở file lên và tạo các sheet bạn cần. Ví dụ: tạo một sheet tên `shenzhen` với định dạng bạn muốn và một sheet tên `shanghai` (có thể để trống hoặc có sẵn tiêu đề). Script sẽ tìm đến sheet `shanghai` để làm việc.

6.  **Chạy script:**
    Sau khi đã hoàn tất các bước trên, chạy script bằng lệnh sau:
    ```bash
    python main.py
    ```
    Script sẽ bắt đầu kết nối, thu thập dữ liệu và cập nhật file `模版.xlsx` của bạn.

## Cách hoạt động

Script hoạt động theo một quy trình gồm 2 phần chính:

1.  **Phần 1: Thu thập và Xử lý dữ liệu**
    -   Script sử dụng thư viện `requests` để gửi một yêu cầu HTTP GET đến URL, giả mạo một `User-Agent` của trình duyệt để tránh bị chặn.
    -   `BeautifulSoup4` được dùng để phân tích cú pháp HTML trả về.
    -   Nó tìm đến tất cả các thẻ `<li>` dựa trên một bộ chọn CSS (`selector`) được định nghĩa sẵn.
    -   Với mỗi mục tìm thấy, nó trích xuất tiêu đề đầy đủ và ngày công bố.
    -   Logic phân tích chuỗi đơn giản được áp dụng để tách Quận và Địa chỉ từ tiêu đề, dựa trên việc tìm ký tự `区` và loại bỏ một chuỗi hậu tố chung.

2.  **Phần 2: Ghi file an toàn bằng `openpyxl`**
    -   Đây là phần quan trọng nhất để đảm bảo tính toàn vẹn của file Excel.
    -   Script sử dụng `openpyxl` để tải toàn bộ file `模版.xlsx` vào bộ nhớ **một cách nguyên bản**.
    -   Nó chỉ thao tác trên sheet `shanghai`. Nếu sheet chưa tồn tại, nó sẽ được tạo mới.
    -   Script xác định hàng trống cuối cùng trong sheet và bắt đầu ghi dữ liệu mới từ đó, **ghi vào từng ô cụ thể (cell)** để đảm bảo dữ liệu bắt đầu chính xác từ cột B.
    -   Cuối cùng, nó lưu lại toàn bộ file. Vì script không hề đọc hay chỉnh sửa các sheet khác, chúng được giữ nguyên 100%.

## Hạn chế hiện tại

-   **Cấu hình được hard-coded:** Các thông tin quan trọng như URL, tên file, tên sheet, và đặc biệt là chuỗi hậu tố (`common_suffix`) để loại bỏ khỏi tiêu đề đều đang được định nghĩa trực tiếp trong code. Nếu chúng thay đổi, bạn phải sửa lại code.
-   **Chỉ thu thập trang đầu tiên:** Script hiện tại không xử lý phân trang (pagination). Nó chỉ lấy dữ liệu từ trang đầu tiên của danh sách.
-   **Logic phân tích tiêu đề còn đơn giản:** Logic phân tích tiêu đề để lấy `Quận` và `Địa chỉ` khá đơn giản (dựa vào ký tự `区` và một chuỗi cố định). Nó có thể thất bại nếu định dạng tiêu đề thay đổi hoặc có các trường hợp ngoại lệ.
-   **Phụ thuộc vào cấu trúc HTML:** Bộ chọn CSS (`ul.uli16...`) rất cụ thể cho cấu trúc hiện tại của trang web. Nếu trang web thay đổi layout (dù là một thay đổi nhỏ về class), script sẽ không tìm thấy dữ liệu và ngừng hoạt động.