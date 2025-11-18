# CaseStudy Agent API

Service FastAPI độc lập chuyên điều phối agent hội thoại cho từng case. Dữ liệu semantic được đồng bộ lên Pinecone thông qua script `casestudy/utils/semantic_extract.py`, API chỉ cần load lại để vận hành phiên trò chuyện.

## Cấu trúc chính

- `main.py`: FastAPI app factory.
- `core/config.py`: Cấu hình kết nối MongoDB, version app.
- `db/database.py`: Mongo client tái sử dụng.
- `services/agent_service.py`: Quản lý session, wrap LangGraph agent (bao gồm logic load Pinecone retriever).
- `routers/agent.py`: Endpoint `/api/agent/*`.

## Endpoint

### Agent

| Method | Path                             | Mô tả                                                             |
|--------|----------------------------------|------------------------------------------------------------------|
| POST   | `/api/agent/sessions`            | Khởi tạo session mới cho một `case_id` và trả về trạng thái ban đầu. |
| POST   | `/api/agent/sessions/{id}/turn`  | Gửi hành động người dùng, nhận phản hồi từ agent và state cập nhật. |
| DELETE | `/api/agent/sessions/{id}`       | Kết thúc session, giải phóng cache in-memory.                    |

### Ví dụ payload
1. Chạy server `uvicorn api_casestudy.main:app --reload --port 9000`.
2. Vào http://127.0.0.1:9000/docs → mục `/api/agent/sessions`.
3. Payload mẫu:

```json
POST /api/agent/sessions
{
  "case_id": "electric_shock_001",
  "user_action": "Tôi kiểm tra an toàn hiện trường.",
  "start_event": "CE1"
}
```

Các lượt tiếp theo dùng endpoint `/api/agent/sessions/{session_id}/turn`:

```json
POST /api/agent/sessions/{session_id}/turn
{
  "session_id": "{session_id}",
  "user_input": "Tôi yêu cầu đồng đội gọi cấp cứu và lấy AED."
}
```

Khi muốn kết thúc phiên nhưng vẫn giữ API chạy: `DELETE /api/agent/sessions/{session_id}`.

> Lưu ý: đảm bảo dữ liệu semantic đã được push lên Pinecone (thông qua `python -m casestudy.utils.semantic_extract <case_id>`) trước khi khởi tạo session, đồng thời cung cấp `OPENAI_API_KEY` cho backend agent.
