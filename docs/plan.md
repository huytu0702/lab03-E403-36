# Implementation Plan

## Mục tiêu

Hoàn thành MVP full stack cho Smart E-commerce Assistant với:

- PostgreSQL bằng Docker
- FastAPI backend
- Streamlit frontend
- `v1` chatbot
- `v2` ReAct agent
- logging và trace đầy đủ

## Team 4 người

### Person A: Database and Infra

Phụ trách:

- `docker-compose.yml`
- PostgreSQL
- init schema
- seed data
- `.env.example` cho DB

Deliverables:

- DB chạy local bằng 1 lệnh
- seed data ổn định cho toàn team

### Person B: Backend FastAPI

Phụ trách:

- API routes
- services
- repositories
- error handling
- response schema thống nhất

Deliverables:

- `POST /chat`
- product APIs
- tool APIs
- trace APIs

### Person C: Chatbot v1 and Agent v2

Phụ trách:

- chatbot baseline
- ReAct agent loop
- prompts
- parser
- tool registry
- stopping condition

Deliverables:

- `.env VERSION=v1|v2`
- 2 mode chạy được
- logs chi tiết từng bước

### Person D: Streamlit and Evaluation

Phụ trách:

- Streamlit UI
- mode switch
- metrics display
- test harness manual
- report artifacts

Deliverables:

- giao diện demo
- bảng kết quả 5 test cases
- screenshot và figure cho báo cáo

## Phase 0. Chốt thiết kế

Mục tiêu:

- chốt use case
- chốt schema
- chốt API contract
- chốt 5 test cases

Đầu ra:

- hoàn thiện bộ docs trong thư mục `docs/`

## Phase 1. Cài đặt môi trường

Mục tiêu:

- toàn team chạy được project local

Tasks:

- tạo `.env` từ `.env.example`
- cài Python dependencies
- chạy `docker compose up -d`
- kiểm tra Postgres lên
- chạy FastAPI skeleton
- chạy Streamlit skeleton

Done khi:

- backend mở được
- frontend mở được
- DB connect thành công

## Phase 2. Database và seed data

Mục tiêu:

- có dữ liệu cố định cho test

Tasks:

- tạo schema SQL
- insert seed data
- validate query cơ bản

Done khi:

- query được products
- query được coupons
- query được shipping rules
- query được FAQs

## Phase 3. Backend business APIs

Mục tiêu:

- expose các API cần cho frontend và tools

Tasks:

- products routes
- FAQs routes
- tools routes
- error model
- trace endpoints

Done khi:

- Postman hoặc Swagger test qua tất cả endpoint chính

## Phase 4. Chatbot `v1`

Mục tiêu:

- có baseline đơn giản nhưng sạch

Tasks:

- viết prompt `v1`
- lấy context FAQ hoặc product snippet
- 1 LLM call
- trả response schema chuẩn
- log step của chatbot

Done khi:

- `v1` trả lời tốt 2 FAQ cases
- trace `v1` có thể đọc được

## Phase 5. ReAct agent `v2`

Mục tiêu:

- giải được case nhiều bước bằng tools

Tasks:

- system prompt
- parse `Thought`, `Action`, `Final Answer`
- tool registry
- tool execution
- observation append
- `max_steps`
- fallback path

Done khi:

- `v2` giải được ít nhất 2 case multi-step
- trace thể hiện rõ Thought -> Action -> Observation

## Phase 6. Frontend Streamlit

Mục tiêu:

- có demo trực quan

Tasks:

- input box
- version switch
- render answer
- render metrics
- render tool calls
- show trace id

Done khi:

- có thể demo cùng một câu hỏi cho cả `v1` và `v2`

## Phase 7. Logging, metrics, and evaluation

Mục tiêu:

- có dữ liệu để viết report

Tasks:

- JSON logs
- trace files
- metrics summary
- bảng expected vs actual cho 5 case

Done khi:

- có bảng so sánh `v1` và `v2`
- có ít nhất 1 failed trace để phân tích

## Phase 8. Hardening and submission

Mục tiêu:

- hoàn thiện bài nộp

Tasks:

- xử lý edge case
- rà error codes
- rà flowchart
- chụp screenshots
- hoàn thiện group report
- phân chia individual report

Done khi:

- demo end-to-end ổn
- tài liệu và logs đầy đủ

## Timeline ngắn gọn

### Day 1

- Phase 0
- Phase 1
- Phase 2

### Day 2

- Phase 3
- Phase 4

### Day 3

- Phase 5
- Phase 6

### Day 4

- Phase 7
- Phase 8

## Rủi ro chính và cách giảm rủi ro

### 1. Agent loop mãi không dừng

Giảm rủi ro:

- thêm `max_steps`
- detect `Final Answer`
- log rõ từng step

### 2. Tool parse lỗi

Giảm rủi ro:

- ép format output
- parser robust
- log raw output trước khi parse

### 3. `v1` quá mạnh, khó so sánh

Giảm rủi ro:

- giữ `v1` chỉ 1 pass
- không cho `v1` orchestration nhiều bước

### 4. Data seed không ổn định

Giảm rủi ro:

- chốt seed cố định
- commit file SQL vào repo
