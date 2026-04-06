# Use Case

## Chủ đề được chọn

**Smart E-commerce Assistant**

Một trợ lý bán hàng cho cửa hàng điện tử, hỗ trợ:

- trả lời FAQ
- tra cứu giá
- kiểm tra tồn kho
- áp mã giảm giá
- tính phí ship
- tổng hợp báo giá cuối cùng

## Vì sao chủ đề này phù hợp lab

### 1. Dễ tạo khác biệt rõ giữa chatbot và agent

Chatbot mạnh ở:

- câu hỏi đơn giản
- FAQ
- câu hỏi 1 bước

Agent mạnh ở:

- câu hỏi nhiều bước
- bước sau phụ thuộc observation bước trước
- cần grounding từ dữ liệu thật trong DB

### 2. Dễ làm MVP đủ full stack

- DB nhỏ, seed data dễ làm
- backend dễ viết service
- frontend chat đơn giản là đủ demo

### 3. Dễ xây 5 test cases đúng rubric

- 2 case chatbot thắng
- 2 case agent thắng
- 1 edge case

## Phạm vi MVP

### In scope

- tra cứu sản phẩm theo tên
- lấy giá sản phẩm
- kiểm tra còn hàng
- kiểm tra coupon
- tính shipping theo thành phố
- trả lời FAQ
- so sánh `v1` và `v2`
- lưu log và trace

### Out of scope

- thanh toán thật
- user authentication
- quản lý giỏ hàng phức tạp
- recommendation nâng cao
- web scraping
- RAG ngoài hệ thống

## Định nghĩa `v1`

`v1` là chatbot baseline:

- nhận user query
- trả lời trực tiếp bằng model
- có thể nhúng FAQ và product context ngắn trong prompt
- không chạy ReAct loop
- không có multi-step tool orchestration

Use tốt nhất:

- "Chính sách đổi trả là gì?"
- "Shop có giao cuối tuần không?"

Điểm yếu:

- khó tính giá nhiều bước chính xác
- dễ hallucinate nếu prompt tự suy luận về stock hoặc coupon

## Định nghĩa `v2`

`v2` là ReAct agent:

- lặp theo chu trình `Thought -> Action -> Observation`
- chọn tool dựa trên câu hỏi
- mỗi observation được đưa lại vào prompt
- dừng khi đủ thông tin để đưa final answer

Use tốt nhất:

- "Mua 2 iPhone 15, dùng WINNER10, ship Hà Nội thì tổng bao nhiêu?"
- "MacBook Air còn hàng không, nếu mua 1 cái ship TP.HCM hết bao nhiêu?"

Điểm mạnh:

- có grounding từ DB
- trả lời nhiều bước ổn định hơn
- trace rõ ràng để phân tích lỗi

## Các persona người dùng chính

### 1. Khách mua hàng

Nhu cầu:

- hỏi giá
- hỏi ship
- hỏi khuyến mãi
- hỏi còn hàng không

### 2. Giảng viên / người chấm bài

Nhu cầu:

- xem sự khác biệt giữa `v1` và `v2`
- xem trace và logs
- xem flowchart và test results

### 3. Thành viên nhóm

Nhu cầu:

- debug nhanh
- benchmark 2 phiên bản
- chứng minh agent có giá trị ở đâu

## Use cases chính

### UC1. FAQ

Ví dụ:

- "Chính sách đổi trả là gì?"

Kỳ vọng:

- `v1` trả lời nhanh, ít token, không cần tool
- `v2` cũng trả lời được, nhưng không nhất thiết tốt hơn

### UC2. Tính báo giá nhiều bước

Ví dụ:

- "Tôi muốn mua 2 iPhone 15, dùng mã WINNER10, ship Hà Nội."

Kỳ vọng:

- `v2` phải gọi nhiều tool
- `v1` dễ sai hoặc không chắc chắn

### UC3. Kiểm tra hàng + ship

Ví dụ:

- "MacBook Air còn hàng không, mua 1 cái ship TP.HCM hết bao nhiêu?"

Kỳ vọng:

- `v2` thắng nhờ gọi stock + price + shipping

### UC4. Edge case

Ví dụ:

- "Mua 3 AirPods với mã SAVE999 ship Đà Nẵng"

Kỳ vọng:

- hệ thống phải trả lỗi rõ
- `v2` có graceful degradation tốt hơn

## Tiêu chí thành công của MVP

- Frontend chat được với cả `v1` và `v2`
- Backend FastAPI chạy ổn
- PostgreSQL chạy qua Docker
- Có tối thiểu 2 tool thực sự dùng trong `v2`
- Có 5 test cases cố định
- Có trace chi tiết cho từng request
- Có flowchart mô tả agent tạo giá trị ở đâu
