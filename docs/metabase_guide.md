# Hướng dẫn Kết nối Metabase và Xây dựng Báo cáo

Chào bạn, đây là tài liệu cấu hình Metabase. Để tối ưu hóa triết lý "Semantic Layer" (Tầng Ngữ Nghĩa) mà chúng ta đã xây dựng, Metabase của dự án này sẽ **không đọc thẳng từ Postgres**, mà sẽ lấy số liệu đã xào nấu hoàn chỉnh từ **Cube**.

## 1. Cách kết nối Metabase với Cube Semantic Layer
Sau khi kiến trúc Docker khởi động xong, hãy truy cập vào `http://localhost:3000`. Cấu hình kết nối Database như sau:

*   **Database type**: **PostgreSQL** *(Cube ảo hóa thành giao thức Postgres)*
*   **Name**: `Mom Baby Semantic Layer` *(Tên hiển thị)*
*   **Host**: `cube_semantic_layer` *(Tên container của Cube)*
*   **Port**: `15432` *(Cổng SQL API của Cube)*
*   **Database name**: `gold_layer`
*   **Username**: `admin`
*   **Password**: `tambui123`

Lúc này, Metabase sẽ tự động khám phá các "Siêu View" (như `market_intelligence_unified`) đã được cấu hình trong file YAML của Cube.

---

## 2. Ý tưởng dựng Dashboard "Chi tiêu Mẹ & Bé thông minh"
Dựa trên tầng Semantic Layer chúng ta đã dựng (đặc biệt là tính năng tự giải nén số combo để tìm Giá Đơn vị - Unit Price), dưới đây là 4 ý tưởng biểu đồ thực chiến bạn nên tạo trong Metabase:

### 👶 Biểu đồ 1: Bảng Xếp Hạng "Đáy Giá" (Biến động theo Measures)
*   **Mục tiêu**: Theo dõi sát sao mức giá thấp nhất và trung bình của thị trường để săn sale. Bảng này khai thác triệt để các **Measure** (Hàm tổng hợp) mà bạn đã cất công định nghĩa ở tầng Cube.
*   **Nguồn Cube**: `market_intelligence_unified`
*   **Cách dựng**: Dùng bảng (Table)
    *   **Data (Dimension)**: Kéo cột `Product Name` hoặc `Brand`.
    *   **Metrics (Measure)**: Gắn 3 measure này vào:
        1.  `Min Sale Price` (Giá rổ thấp nhất từng ghi nhận)
        2.  `Average Unit Price` (Giá Đơn vị trung bình trên thị trường, đã trừ lốc combo)
        3.  `Average Sale Price` (Giá bán giỏ hàng trung bình)

### 📉 Biểu đồ 2: Lịch sử Đáy giá Tiki (Price Trend)
*   **Mục tiêu**: Theo dõi xu hướng giá theo thời gian để trả lời câu hỏi "Đợi thêm vài ngày liệu có rẻ hơn?".
*   **Cách dựng**: Biểu đồ Đường (Line Chart)
    *   **Trục X (X-axis)**: `Date Day` (Ngày)
    *   **Nhóm (Series/Breakout)**: `Brand`
    *   **Trục Y (Measure)**: Dùng Measure `Average Unit Price`.

### 🚨 Biểu đồ 3: Radar Bùng nổ Deal (Deals Count Tracker)
*   **Mục tiêu**: Theo dõi xem trong ngày hoặc trong tuần, có bao nhiêu sản phẩm chạm "Đáy" (Giá rẻ nhất tháng). Biểu đồ này dùng riêng Measure `Deals Count`.
*   **Cách dựng**: Biểu đồ miền (Area Chart) hoặc Biểu đồ đường (Line Chart).
    *   **Trục X**: `Date Day`
    *   **Metric (Measure)**: `Deals Count` (Tổng số lượng deal hot)
    *   Nhìn biểu đồ này, Mẹ bỉm sẽ biết ngay "Ngày Sale Giữa Tháng" hay "Thứ 6 Đen Tối" số lượng deal bùng nổ khủng khiếp nhường nào!

### 🕒 Biểu đồ 4: Khung giờ xả hàng Mẹ & Bé (Săn deal bằng Heatmap)
*   **Mục tiêu**: Tìm ma trận giờ vàng. Các sàn TMĐT xả hàng xả láng nhất vào 0h đêm hay 12h trưa?
*   **Cách dựng**: Biểu đồ lưới chênh lệch nhiệt (Heatmap)
    *   **Trục ngang (X)**: `Hour 24` (từ 0h đến 23h)
    *   **Trục dọc (Y)**: `Day of Week` (Từ Thứ 2 đến Chủ Nhật)
    *   **Color Value (Measure)**: Kéo Measure `Deals Count` vào đây. Chỗ nào màu đậm (Đỏ lựng), chỗ đó là giờ hoàng đạo săn sale!

## 3. Lời khuyên vận hành
Sự ưu việt của thiết kế này nằm ở chỗ: Bất kỳ khi nào phía Data Engineer nảy ra logic tính toán mới (Ví dụ thêm logic tích hợp tiền Phí Vận Chuyển vào giá đơn vị). Họ chỉ cần sửa code Python/DBT ở phía dưới. Trên Metabase của bạn biểu đồ sẽ tự động đúng mà không cần mất công tạo lại Question đồ thị.
