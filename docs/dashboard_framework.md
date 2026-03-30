# Khung Báo Cáo Theo Dõi Giá (Price Intelligence Framework)

Chào bạn, đây là hướng dẫn từng bước để bạn dựng một Dashboard hoàn chỉnh, giải quyết triệt để 2 mục tiêu: "Khi nào mua rẻ nhất" và "Mua ở sàn nào hời nhất".

## 1. Chuẩn bị dữ liệu (Dưới góc độ dbt)
Trong bảng `fact_price_snapshots` đã có sẵn cột `unit_price` (Giá trên từng đơn vị). 
*   **Lưu ý:** Hiện tại tôi đang để công thức mẫu là `sale_price / 10`. Để chính xác 100%, sau này bạn nên cập nhật `unit_count` (số miếng/ml) từ Scraper.

---

## 2. Các biểu đồ then chốt (Key Visuals)

### Biểu đồ A: Lịch sử giá theo đơn vị (Question 1)
*   **Mục tiêu:** Trả lời câu hỏi "Giá bỉm này đang tăng hay giảm?"
*   **Cách làm:**
    1.  New -> Question -> Chọn `fact_price_snapshots`.
    2.  **Filter:** Chọn `Product Name` (thông qua Join với `dim_product`).
    3.  **Summarize:** Chọn `Average of Unit Price`.
    4.  **Group by:** Chọn `Scraped At` -> chọn `Day`.
    5.  **Visualization:** Chọn `Line Chart`.
    *   *Mẹo:* Vào phần Settings của biểu đồ, bật "Show dots" để thấy rõ từng thời điểm cào.

### Biểu đồ B: Heatmap Giờ Vàng (Question 2) - Cực quan trọng cho PM
*   **Mục tiêu:** Trả lời câu hỏi "Trong ngày thì mấy giờ hay có Flash Sale?"
*   **Cách làm:**
    1.  New -> Question -> Chọn `fact_price_snapshots`.
    2.  **Summarize:** Chọn `Min of Unit Price`.
    3.  **Group by:** 
        - Cột 1: `Scraped At` -> chọn `Hour of day`.
        - Cột 2: `Scraped At` -> chọn `Day of week`.
    4.  **Visualization:** Chọn `Grid` (Heatmap).
    *   *Insight:* Nhìn vào đây, bạn sẽ thấy các ô màu đậm nhất (giá thấp nhất) thường rơi vào 0h hoặc 12h trưa.

### Biểu đồ C: So sánh giá liên sàn (Question 3)
*   **Mục tiêu:** Trả lời câu hỏi "Shopee hay Lazada đang rẻ hơn?"
*   **Cách làm:**
    1.  New -> Question -> Chọn `fact_price_snapshots`.
    2.  **Summarize:** Chọn `Min of Unit Price`.
    3.  **Group by:** Chọn `Platform Name` (Join với `dim_platform`).
    4.  **Visualization:** Chọn `Bar Chart`.
    *   *Mẹo:* Chọn "Display" -> "Stacking: None" để các cột đứng cạnh nhau dễ so sánh.

---

## 3. Dựng Dashboard và Bộ lọc (Orchestration)

1.  **Tạo Dashboard mới:** Đặt tên là `Dashboard Tình Báo Giá - Mom & Baby`.
2.  **Thêm Questions:** Kéo 3 biểu đồ trên vào Dashboard.
3.  **Thêm Bộ lọc (Filters) - Đây là linh hồn của Dashboard:**
    *   **Filter 1 (Product):** Add Filter -> Text or Category -> Dropdown. Kết nối với cột `Product Name` của tất cả các Question.
    *   **Filter 2 (Time):** Add Filter -> Time -> Date Range. Kết nối với cột `Scraped At`.

---

## 4. Cách khai thác Dashboard (Dành cho PM)

*   **Sáng sớm:** Mở Dashboard, lọc theo sản phẩm "Bỉm Moony". Nhìn vào biểu đồ **Heatmap Giờ Vàng**. Nếu thấy khung 12h trưa thường xuyên có giá hời -> Lên lịch nhắc người dùng săn sale.
*   **Trước khi chạy chiến dịch:** Nhìn biểu đồ **So sánh giá liên sàn**. Nếu thấy đối thủ đang rẻ hơn 20% -> Cần điều chỉnh ngay chính sách giá hoặc ưu đãi ship.
*   **Cuối tháng:** Nhìn biểu đồ **Lịch sử giá đơn vị** để thấy chu kỳ sale. Thường các sàn sẽ sale mạnh vào ngày đôi (9/9, 10/10) hoặc ngày giữa tháng (15).

Với khung báo cáo này, bạn không chỉ "xem dữ liệu" mà thực sự đang "đọc vị thị trường"!
