Trang web mới này (`zwgk.shmh.gov.cn`) có một API rất khác so với trang cũ. Dưới đây là những thay đổi **quan trọng nhất** trong script mới để nó có thể "nói chuyện" được với API này.

### 1. Thay đổi Phương thức Giao tiếp: Từ `POST` sang `GET` (Quan trọng nhất)

-   **Script cũ (Lỗi):** Dùng phương thức `POST`. Tưởng tượng như bạn gửi một lá thư kín (payload JSON) đến API.
-   **Script mới (Đúng):** Dùng phương thức `GET`. Giống như bạn viết thẳng yêu cầu lên một tấm bưu thiếp (các tham số trên URL) và gửi đi.
-   **Tại sao lại thay đổi?** Vì "nhà bếp" của trang này chỉ chấp nhận "bưu thiếp" (`GET`), nó sẽ từ chối và báo lỗi nếu bạn gửi "thư kín" (`POST`).

### 2. Thay đổi Cách gửi Yêu cầu: Không còn `payload` mà là `params`

-   **Script cũ:** Đóng gói tất cả thông tin (từ khóa, số trang...) vào một `dictionary` tên là `payload` và gửi đi trong body của request `POST`.
    ```python
    # Cách cũ
    requests.post(api_url, json=payload) 
    ```
-   **Script mới:** Tạo một `dictionary` tên là `params`. Thư viện `requests` sẽ tự động chuyển đổi `params` này thành một chuỗi tham số và gắn nó vào cuối URL.
    ```python
    # Cách mới
    requests.get(base_api_url, params=current_params)
    ```
    Nó sẽ tự tạo ra URL trông như thế này: `https://.../searchByDB?keyword=...&pageindex=2&...`

### 3. Cập nhật "Địa chỉ Nhà bếp" và "Thực đơn"

-   **`api_url`:** Đã được đổi thành `https://zwgk.shmh.gov.cn/mh-xxgk-cms/searchindex/searchByDB`, là địa chỉ chính xác của API mới.
-   **`base_params`:** Đây là "thực đơn" mà API mới yêu cầu. Các tên tham số đã thay đổi hoàn toàn:
    -   `query` -> đổi thành `keyword`
    -   `current` -> đổi thành `pageindex`
    -   `size` -> đổi thành `pagesize`
    -   Bổ sung thêm `sitecode` và `sitename` là những tham số bắt buộc mà API này cần.
    -   Đặc biệt, tham số `t` (timestamp) được tạo mới cho **mỗi lần request** để giả lập hành vi của trình duyệt.

### 4. Thay đổi Cách "Đọc Hóa đơn" (Xử lý Dữ liệu trả về)

-   **Script cũ:** Dữ liệu trả về nằm trong `data['result']['items']` và tổng số trang nằm trong `data['result']['_meta']['page']['total_pages']`.
-   **Script mới:** Cấu trúc JSON đã thay đổi hoàn toàn:
    -   Dữ liệu trả về nằm trong `data['list']`.
    -   Tổng số **kết quả** (không phải tổng số trang) nằm trong `data['totalcount']`. Script phải tự tính toán lại tổng số trang dựa trên `totalcount` và `pagesize`.
    -   Tiêu đề nằm trong `item['title']` (thay vì `item['title']['raw']`).
    -   Ngày tháng nằm trong `item['startTime']` (thay vì `item['date']['raw']`).

### 5. Xử lý "Rác" trong Tiêu đề

-   **Vấn đề mới:** API này trả về tiêu đề có chứa các thẻ HTML, ví dụ: `...<span style="color:#d70000;">加装电梯工程</span>...`.
-   **Giải pháp:** Script mới phải thêm một bước làm sạch bằng Biểu thức chính quy (Regex) để loại bỏ các thẻ HTML này trước khi phân tích.
    ```python
    # Dòng code mới để xóa thẻ HTML
    full_title = re.sub('<[^>]+>', '', full_title_html)
    ```

**Tóm lại:** Việc chuyển sang crawl trang mới không chỉ là thay đổi một dòng URL. Nó đòi hỏi chúng ta phải "điều tra" lại toàn bộ quy trình giao tiếp của trang web đó và viết lại script để tuân thủ chính xác các quy tắc mới, từ phương thức request, tên tham số, cho đến cách đọc dữ liệu trả về. Script mới đã làm tất cả những điều này.