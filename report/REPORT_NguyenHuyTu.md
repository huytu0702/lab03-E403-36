# Individual Report: Lab 3 - Nguyễn Huy Tú

- **Student Name**: Nguyễn Huy Tú
- **Student ID**: 2A202600170
- **Date**: 2026-04-06

---

## I. Technical Contribution

### Primary Responsibilities

Tôi phụ trách phần tích hợp và nền tảng dùng chung cho cả nhóm:

- sinh và hoàn thiện bộ tài liệu trong thư mục `docs/`
- dựng skeleton codebase ban đầu cho backend, frontend và cấu trúc module
- fix bug tích hợp, resolve merge conflict và ổn định codebase khi ghép phần việc của các thành viên
- viết cấu hình chạy và build Docker để nhóm có thể demo full stack

### Key Artifacts

- `README.md`
- `docs/README.md`
- `docs/architecture.md`
- `docs/api.md`
- `docs/flow.md`
- `docs/logging.md`
- `docs/test_cases.md`
- `docs/plan.md`
- `docs/todo.md`
- `Dockerfile`
- `docker-compose.yml`
- `scripts/run_postgres.ps1`
- `scripts/run_backend.ps1`
- `scripts/run_frontend.ps1`
- `scripts/run_stack.ps1`

### Contribution Details

Phần tôi tập trung là làm cho dự án có thể được hiểu, chạy và tích hợp nhất quán:

- tài liệu hóa rõ kiến trúc `v1` và `v2` để các thành viên code cùng một hướng
- chuẩn hóa quy trình bootstrapping, setup môi trường và chạy stack
- dựng nền tảng Docker để backend, frontend và PostgreSQL khởi động theo cùng một workflow
- xử lý các lỗi ghép code giữa nhiều phase để hệ thống vẫn chạy end-to-end

---

## II. Debugging Case Study

### Problem

Một lỗi tích hợp quan trọng là nguy cơ backend lên trước khi PostgreSQL sẵn sàng, khiến:

- API fail khi truy cập DB
- frontend không lấy được health check ổn định
- toàn bộ demo stack khó khởi động bằng một lệnh

### Diagnosis

Với hệ thống nhiều service, lỗi không nằm ở một function đơn lẻ mà ở thứ tự boot và khả năng chịu lỗi của cả stack:

- `postgres` cần thời gian để health check pass
- `api` phụ thuộc DB để đọc dữ liệu
- `frontend` phụ thuộc `api` để hiển thị compare mode

Nếu không có orchestration rõ, trải nghiệm chạy demo sẽ rất thiếu ổn định.

### Solution

Tôi hỗ trợ harden phần hạ tầng bằng:

- `depends_on` với `condition: service_healthy` trong `docker-compose.yml`
- tách riêng 3 service `postgres`, `api`, `frontend`
- thêm script chạy nhanh cho từng service và cho full stack
- giữ cơ chế `fallback-seed` để hệ thống vẫn demo được khi DB chưa sẵn sàng hoàn toàn

### Result

Nhờ đó, nhóm có thể:

- chạy full stack bằng Docker
- demo được UI và API theo cùng một cách trên máy các thành viên
- giảm đáng kể lỗi môi trường khi chuyển từ dev sang demo/report

---

## III. Personal Insights

Điều tôi rút ra rõ nhất từ phần việc của mình là một agent system không thể đánh giá công bằng nếu phần hạ tầng và tài liệu không ổn định. Muốn so sánh `v1` với `v2`, cả hai phải chạy trên cùng data, cùng API contract, cùng frontend và cùng bộ metrics. Nếu phần nền tảng thiếu chặt chẽ, kết quả compare sẽ mất ý nghĩa.

Tôi cũng thấy rằng công việc tài liệu và tích hợp không phải phần phụ. Trong bài lab này, chính `docs/`, Docker workflow và conflict resolution đã giúp các phần của nhóm ghép lại thành một sản phẩm có thể demo và viết report được, thay vì chỉ là các module rời rạc.

---

## IV. Future Improvements

- thêm CI để tự động check Docker build, `pytest` và lint mỗi khi merge code
- pin chặt hơn version dependency để tránh lệch môi trường giữa các máy
- bổ sung tài liệu vận hành ngắn cho bước demo cuối
- thêm script xuất artifact benchmark và screenshot vào một thư mục chuẩn để phục vụ nộp bài
