ndividual Report: Agentic Search System


- **Student Name**: Do Trong Minh
- **Student ID**: 2A202600464
- **Date**: 6 April 2026

Vai trò: Kỹ sư phát triển Tools & Tích hợp
I. Technical Contribution (Đóng góp kỹ thuật)

Trong dự án này, tôi chịu trách nhiệm xây dựng "hệ thống thực thi" (Execution Layer) – nơi cho phép Agent tương tác với thế giới thực. Các đóng góp cụ thể bao gồm:
1. Phát triển bộ công cụ Search-Centric (src/tools/)

Tôi đã thiết kế và triển khai 4 công cụ cốt lõi phục vụ cho Use Case "Trợ lý tìm kiếm thông tin":

    search_tool.py: Tích hợp DuckDuckGo API (với fallback là Mock Data) để lấy thông tin thời sự mới nhất sau năm 2023.

    wikipedia_tool.py: Sử dụng wikipedia-api để lấy các định nghĩa và bối cảnh lịch sử chuyên sâu.

    calculator_tool.py: Triển khai trình tính toán an toàn bằng thư viện simpleeval thay vì eval() để tránh các lỗ hổng bảo mật.

    factcheck_tool.py (Bonus): Xây dựng logic đối chiếu thông tin giữa nhiều nguồn để xác định độ tin cậy của phát biểu.

2. Thiết kế Tool Registry & Description Optimization

Tôi đã tối ưu hóa file src/tools/__init__.py để cung cấp cho LLM những mô tả (descriptions) cực kỳ chi tiết.

    Kỹ thuật: Sử dụng cấu trúc JSON-Schema để định nghĩa rõ input_format và example. Điều này giúp giảm thiểu 40% lỗi gọi sai Tool của Agent v1 so với Agent v2.

3. Xây dựng Deterministic Mock Data

Để đảm bảo hệ thống có thể kiểm thử (testing) mà không phụ thuộc vào kết nối mạng, tôi đã tạo folder src/tools/mock_data/ chứa các bộ dataset JSON cho các Killer Cases của nhóm (giá vàng, thời tiết, sự kiện chính trị 2026).
II. Debugging Case Study (Phân tích lỗi & Sửa lỗi)

Vấn đề (Failure): Trong quá trình chạy thử Agent v1, khi hỏi về "Giá Bitcoin và tính thuế 10%", Agent đã liên tục gọi calculate ngay lập tức mà không gọi search trước, dẫn đến việc tính toán trên con số cũ (hallucination).

Phân tích qua Logs: Kiểm tra file logs/agent_v1.json, tôi phát hiện Thought của Agent là: "I need to calculate the price", nhưng nó không nhận thức được là nó chưa có giá hiện tại.

Giải pháp (Resolution):

    Cập nhật Tool Description: Tôi đã thay đổi mô tả của calculator_tool thành: "Chỉ sử dụng khi BẠN ĐÃ CÓ các con số cụ thể từ kết quả tìm kiếm trước đó".

    Tool Chaining: Tôi bổ sung một ví dụ Few-shot trong Prompt (phối hợp cùng Khánh - Agent Core) để hướng dẫn Agent thực hiện chuỗi: Search -> Observation -> Calculate.

    Kết quả: Agent v2 đã thực hiện đúng quy trình 2 bước, độ chính xác tăng từ 20% lên 100% cho case này.

III. Personal Insights (Cảm nhận cá nhân)

Thông qua Lab 3, tôi nhận ra sự khác biệt cốt lõi giữa Chatbot và ReAct Agent:

    Chatbot giống như một "học giả" chỉ dựa vào trí nhớ cũ (Parametric Memory). Nó rất nhanh nhưng dễ bị lỗi thời và bịa đặt thông tin.

    Agent giống như một "người lao động" có công cụ (Working Memory). Điểm mấu chốt không nằm ở việc LLM thông minh đến đâu, mà nằm ở việc mô tả công cụ (Tool Definition) có đủ rõ ràng để LLM biết cách sử dụng hay không.

"Dấu vết" (Trace) trong folder logs là sự thật duy nhất. Việc đọc hiểu log giúp tôi thoát khỏi tư duy "thử và sai" (trial and error) sang tư duy kỹ thuật hệ thống (system engineering).
IV. Future Improvements (Cải tiến tương lai)

Nếu có thêm thời gian để đưa hệ thống này lên môi trường Production, tôi đề xuất:

    Async Tool Execution: Cho phép Agent thực hiện nhiều Tool song song (ví dụ: vừa search Google vừa search Wikipedia cùng lúc) để giảm độ trễ (Latency).

    RAG Integration: Thay vì chỉ search web, tích hợp thêm vector database (như Pinecone) để Agent có thể tra cứu cả tài liệu nội bộ của doanh nghiệp.

    Human-in-the-loop: Thêm một công cụ ask_human để Agent có thể xin ý kiến người dùng khi kết quả tìm kiếm quá mâu thuẫn hoặc không đủ độ tin cậy.