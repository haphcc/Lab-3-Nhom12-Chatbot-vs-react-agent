# Báo Cáo Cá Nhân: Lab 3 - Chatbot vs ReAct Agent

- **Họ và tên**: Pham Thi Hoai
- **MSSV**: 2A202600269
- **Ngày**: 06/04/2026

---

## I. Đóng Góp Kỹ Thuật (15 điểm)

Em đã triển khai luồng Chatbot baseline hoàn chỉnh và bộ test mini tự động để đánh giá theo các nhóm câu hỏi.

- **Các module đã thực hiện**:
  - `src/chatbot.py`
  - `tests/search_test_suite.py`
  - `tests/test_cases.json`
  - `tests/run_search_tests.py`
- **Điểm nổi bật trong code**:
  - `src/chatbot.py`: xây dựng lớp `Chatbot` sử dụng `OpenAIProvider` và hàm `ask()` theo hướng trả lời trực tiếp.
  - `tests/test_cases.json`: thiết kế 5 nhóm test (`factual`, `current`, `reasoning`, `calculation`, `verification`) để kiểm tra nhiều dạng năng lực.
  - `tests/search_test_suite.py`: cài đặt `SearchTestSuite` để đọc test JSON, gọi `Chatbot.ask()`, và gom kết quả theo cấu trúc.
  - `tests/run_search_tests.py`: tạo file chạy test độc lập, in so sánh từng case (`question`, `expected`, `answer`), nạp `.env`, và xử lý output UTF-8 trên terminal.
- **Mô tả tương tác hệ thống**:
  - Phần em làm tạo pipeline đánh giá baseline cho Chatbot trả lời trực tiếp.
  - Kết quả đầu ra có thể dùng làm mốc để so sánh với hành vi của ReAct Agent trên cùng bộ câu hỏi.
  - Luồng chạy: JSON test cases -> test suite -> chatbot suy luận -> in báo cáo có cấu trúc trên console.

---

## II. Phân Tích Một Lỗi Debug Thực Tế (10 điểm)

- **Mô tả vấn đề**:
  - Khi chạy `tests/run_search_tests.py` ban đầu bị lỗi `ModuleNotFoundError: No module named 'dotenv'`.
  - Sau khi cài thư viện, chạy trên Windows PowerShell tiếp tục lỗi `UnicodeEncodeError` khi in tiếng Việt.
- **Nguồn log/lỗi**:
  - Output terminal trong quá trình chạy test (`python tests/run_search_tests.py`).
  - Các lỗi chính ghi nhận:
    - `ModuleNotFoundError: No module named 'dotenv'`
    - `UnicodeEncodeError: 'charmap' codec can't encode character ...`
- **Chẩn đoán nguyên nhân**:
  - Môi trường Python dùng để chạy test chưa cài `python-dotenv`.
  - Encoding mặc định của terminal Windows (cp1252) không hiển thị được ký tự tiếng Việt từ `test_cases.json`.
- **Cách khắc phục**:
  - Cài thư viện còn thiếu và đảm bảo nạp biến môi trường ở mức script.
  - Cập nhật `tests/run_search_tests.py`:
    - Thêm `from dotenv import load_dotenv` và gọi `load_dotenv()` trước khi chạy test.
    - Thêm `sys.stdout.reconfigure(encoding="utf-8")` (kèm `try/except`) để in Unicode an toàn.
  - Kết quả: script chạy thành công và in đủ 5 test case.

---

## III. Nhận Xét Cá Nhân: Chatbot vs ReAct (10 điểm)

1. **Về suy luận**:
   - Chatbot trả lời trực tiếp nhanh và mượt, nhưng quá trình suy luận thường ẩn, khó kiểm chứng.
   - ReAct với chuỗi `Thought -> Action -> Observation` giúp lộ rõ từng bước trung gian, dễ phân tích và audit hơn.
2. **Về độ tin cậy**:
   - ReAct có thể cho kết quả kém hơn nếu gọi tool không cần thiết, mô tả tool chưa tốt, hoặc dữ liệu trả về bị nhiễu.
   - Với các câu hỏi đơn giản (kiến thức cơ bản/tính toán), Chatbot trực tiếp thường nhanh hơn và đôi khi ổn định hơn.
3. **Về vai trò của Observation**:
   - Trong ReAct, phản hồi từ môi trường (kết quả tool) ảnh hưởng mạnh đến quyết định bước kế tiếp và giúp sửa giả định sai.
   - Ở Chatbot trực tiếp, không có vòng phản hồi ngoài một cách tường minh nên khả năng tự hiệu chỉnh thấp hơn.

---

## IV. Hướng Cải Tiến Trong Tương Lai (5 điểm)

- **Khả năng mở rộng**:
  - Thêm cơ chế chạy batch/asynchronous cho test suite và tool calls.
  - Lưu kết quả test dạng có cấu trúc (JSON/CSV) để theo dõi chất lượng theo từng phiên bản model.
- **An toàn hệ thống**:
  - Bổ sung luật kiểm tra đầu ra và policy check trước khi trả kết quả cuối.
  - Thêm cơ chế fallback khi thiếu API key, tool lỗi, hoặc timeout.
- **Hiệu năng**:
  - Cache các prompt lặp lại và tri thức dùng thường xuyên.
  - Thêm cơ chế retrieval/indexing (vector DB) khi số tool/tài liệu tăng.

---

