# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Trương Minh Phước
- **Student ID**: 2A202600330
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/agent/agent.py`, `src/agent/parser.py`, `src/agent/prompts.py`
- **Code Highlights**:
  - Xây dựng vòng lặp **ReAct loop** tự động thay thế quá trình thực thi code cứng (deterministic): sử dụng vòng lặp `while steps < self.max_steps` gọi đến `self.llm.generate()`.
  - Bổ sung hàm `parse_react_response(text: str)` tích hợp Regex linh hoạt nhằm trích xuất chính xác `Thought`, `Action`, `Action Input` (với hỗ trợ bóc tách JSON), và `Final Answer`.
  - Tích hợp logic **chữa lỗi tự động (Automated Fallback)**: Nếu LLM liên tục gọi sai Tool hoặc parse JSON bị lỗi, Agent sẽ trả ngược Observation mang thông báo lỗi (`System Error parsing your response...`) để LLM tự chẩn đoán và điều chỉnh lại định dạng.
- **Documentation**: Thông qua tiến trình trên, tôi chịu trách nhiệm chính trong **Phase 5**, hiện thực hoá mô hình Agent v2 trên thực tế thay vì mock data, qua đó tích hợp LLM làm controller điều khiển luồng tool của backend.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Trong những vòng thử nghiệm đầu, Agent thường xuyên rơi vào loop hỏng do gọi sai định dạng Tool (ví dụ: in ra `Action: tool_name({"arg":"value"})` khiến Parser không xử lý được các dấu ngoặc khép kín lồng nhau).
- **Log Source**: Trace Logs hiển thị báo lỗi Regex không tìm thấy Action Name hoặc `JSONDecodeError` ở vòng lặp thực thi `_execute_tool`.
- **Diagnosis**: Agent bị bối rối vì format cũ trong System Prompt quá nguyên khối. String do Regex cung cấp không chuẩn hoá được do ảnh hưởng khi mô hình tuỳ hứng xuất ra Markdown code blocks (\`\`\`json).
- **Solution**: Tôi đã đại tu lại Prompt trong `src/agent/prompts.py`. Chia tách rạch ròi `Action:` và một field mới tên là `Action Input:`. Bên trong `parser.py`, tôi bổ sung regex ignore markdown backticks để trích xuất sạch sẽ Payload JSON. Kết quả là 100% LLM gọi tool đúng format.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Khối `Thought` hoạt động như một kỹ thuật Chain-of-Thought (CoT). Việc bắt buộc tác tử phải phân tích tình huống hiện tại trước, sau đó mới chỉ định `Action` giúp LLM không bị ảo giác dữ liệu hay đưa ra quyết định vội vàng khi chưa đủ thông tin.
2.  **Reliability**: Đối với những câu hỏi FAQ quá đơn giản (vd: "Shop bạn ở đâu?"), Agent v2 lại hoạt động "quá tải" (overkill). Nó có thể mất thời gian sinh ra Thought hoặc cố gắng tìm một tool không cần thiết, dẫn đến độ trễ (latency) cao hơn đáng kể so với Chatbot v1 giải quyết trong 1 single pass.
3.  **Observation**: Dữ liệu Observation đóng vai trò grounding (neo thực tế). Ví dụ, khi LLM dự định tính thành tiền, nhưng Observation từ tool báo `in_stock: False`, nó ngay lập tức bẻ lái Thought tiếp theo thành lời xin lỗi hết hàng thay vì tiếp tục tính tiền mù quáng.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Nâng cấp từ manual loop sang sử dụng framework thiết kế chuyên dụng cho Agent Workflow như **LangGraph** hoặc **CrewAI** để quản lý State tốt hơn ở các context lớn.
- **Safety**: Dùng Pydantic validation áp đặt vào từng function input. Nếu LLM nhét tham số nguy hiểm, Pydantic sẽ filter ngay lập tức ở tầng parse chứ không đợi JSON throw error.
- **Performance**: Tạo kiến trúc chạy đồng thời (Concurrent/Async) cho các lệnh gọi Tool độc lập. Nếu cần lấy giá và check tồn kho cùng lúc, ta có thể spawn Async jobs cho 2 công cụ đó và trả về chung 1 chuỗi Observation.
