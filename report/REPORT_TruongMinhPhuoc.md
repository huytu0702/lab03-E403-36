# Individual Report: Lab 3 - Trương Minh Phước

- **Student Name**: Trương Minh Phước
- **Student ID**: 2A202600330
- **Date**: 2026-04-06

---

## I. Technical Contribution

### Scope of Work

Tôi phụ trách **Phase 5** và hỗ trợ **Phase 6-9**:

- triển khai ReAct agent `v2`
- hỗ trợ hardening cho frontend compare, metrics, tests và provider-related validation

### Main Modules

- `src/agent/agent.py`
- `src/agent/parser.py`
- `src/agent/prompts.py`
- `src/agent/tools_registry.py`
- `tests/test_agent_grounding.py`
- `tests/test_api_compare.py`
- `docs/compare_v1_v2_result.md`

### Contribution Details

Phần tôi tập trung là biến skeleton agent thành một ReAct loop có thể chạy được trên bài toán thương mại điện tử:

- parse `Thought`, `Action`, `Action Input`, `Final Answer`
- thực thi tool thật thay vì deterministic flow cứng
- append observation quay lại scratchpad
- dừng khi có đủ grounding hoặc chạm stopping condition
- giữ trace chi tiết để có thể debug theo từng step

### Technical Highlights

Một số điểm kỹ thuật quan trọng tôi tập trung hoàn thiện:

- suy ra `required_tools` từ user input
- từ chối `Final Answer` khi chưa đủ grounding
- tự động tổng hợp câu trả lời grounded khi đã đủ observation
- robust parser cho output pha trộn hoặc format không sạch
- fallback khi parse lỗi hoặc tool lỗi

Nhờ các điểm này, `v2` không chỉ “gọi được tool” mà còn hành xử gần đúng với tinh thần của một agent có kiểm soát.

---

## II. Debugging Case Study

### Problem

Một lỗi khó chịu của ReAct agent là model có thể:

- phát `Final Answer` quá sớm
- lặp lại tool đã gọi thành công
- trộn cả `Action` và `Final Answer` trong cùng output

Khi đó agent dễ:

- kết luận thiếu dữ liệu
- bỏ sót coupon hoặc shipping
- tạo ra trace khó tin cậy

### Diagnosis

Vấn đề không chỉ nằm ở prompt mà nằm ở orchestration:

- model không phải lúc nào cũng tuân thủ format sạch
- nếu code agent tin tuyệt đối vào output của model thì hệ thống sẽ rất dễ gãy
- cần một lớp điều phối phía code để ép agent grounding đúng hướng

### Solution

Tôi tập trung harden `v2` bằng các cơ chế:

- `required_tools` để xác định các tool bắt buộc theo từng truy vấn
- `insufficient_grounding` để chặn final answer sớm
- `Forced next missing tool` khi model lặp lại tool cũ
- bỏ qua `Final Answer` nếu output vẫn còn `Action`
- `auto_final_answer` khi đã đủ observation từ tools

Các cơ chế này được bảo vệ bằng test trong `tests/test_agent_grounding.py`.

### Result

Sau khi hoàn thiện, `v2` xử lý đúng các case quan trọng:

- quote nhiều bước cho iPhone 15 với coupon và shipping
- stock + price + shipping cho MacBook Air M3
- coupon sai `SAVE999` nhưng vẫn trả tổng grounded

Đây là phần khác biệt lớn nhất giữa chatbot và agent trong bài lab.

---

## III. Personal Insights

Làm agent khiến tôi thấy rất rõ rằng chất lượng của một agent system không nằm riêng ở model. Prompt tốt là cần thiết nhưng chưa đủ. Những phần như parser, stopping condition, guardrail và grounding enforcement mới là thứ quyết định agent có “production-like” hay không.

Tôi cũng nhận ra rằng ReAct mạnh hơn chatbot ở bài toán nhiều bước, nhưng cái giá phải trả là latency cao hơn, token nhiều hơn và engineering effort lớn hơn rất nhiều. Nếu không có test và telemetry, rất khó biết agent đang tạo giá trị thật hay chỉ tạo thêm độ phức tạp.

---

## IV. Future Improvements

- chuyển parser sang schema chặt hơn để giảm phụ thuộc vào text parsing
- thêm retry policy có kiểm soát khi model trả format lỗi
- tối ưu prompt để giảm số vòng lặp và token usage
- nghiên cứu tách planner và executor nếu muốn mở rộng thêm tool hoặc use case
