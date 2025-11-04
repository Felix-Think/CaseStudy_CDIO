# CaseStudy Agent API

Service FastAPI độc lập chuyên xử lý semantic store **và** điều phối agent hội thoại cho từng case.

## Cấu trúc chính

- `main.py`: FastAPI app factory.
- `core/config.py`: Cấu hình (Mongo URI, embedding model, thư mục lưu vector).
- `db/database.py`: Mongo client tái sử dụng.
- `pipelines/builder.py`: Chuyển dữ liệu case thành `langchain` documents.
- `services/semantic_service.py`: Nghiệp vụ build/query semantic store.
- `services/agent_service.py`: Quản lý session, wrap LangGraph agent.
- `routers/semantic.py`: Endpoint `/api/semantic/*`.
- `routers/agent.py`: Endpoint `/api/agent/*`.

## Endpoint

### Semantic

| Method | Path                  | Mô tả                                           |
|--------|-----------------------|------------------------------------------------|
| POST   | `/api/semantic/build` | Đồng bộ lại vector store cho `case_id`.        |
| POST   | `/api/semantic/query` | Truy vấn semantic store với câu hỏi đầu vào.   |

### Agent

| Method | Path                             | Mô tả                                                             |
|--------|----------------------------------|------------------------------------------------------------------|
| POST   | `/api/agent/sessions`            | Khởi tạo session mới cho một `case_id` và trả về trạng thái ban đầu. |
| POST   | `/api/agent/sessions/{id}/turn`  | Gửi hành động người dùng, nhận phản hồi từ agent và state cập nhật. |
| DELETE | `/api/agent/sessions/{id}`       | Kết thúc session, giải phóng cache in-memory.                    |

### Ví dụ payload

```json
POST /api/semantic/build
{
  "case_id": "electric_shock_001",
  "force_rebuild": true
}
```

```json
POST /api/semantic/query
{
  "case_id": "electric_shock_001",
  "question": "Những nguồn lực hiện trường nào có sẵn?",
  "top_k": 4
}
```

```json
POST /api/agent/sessions
{
  "case_id": "electric_shock_001",
  "user_action": "Tôi kiểm tra an toàn hiện trường.",
  "start_event": "CE1"
}
```

```json
POST /api/agent/sessions/{session_id}/turn
{
  "session_id": "{session_id}",
  "user_input": "Tôi yêu cầu đồng đội gọi cấp cứu và lấy AED."
}
```

## Chạy thử

```bash
poetry run uvicorn api_casestudy.main:app --reload --port 9000
```

> Lưu ý: service sử dụng OpenAI embeddings (`text-embedding-3-small`) giống pipeline hiện có. Thiết lập biến môi trường `OPENAI_API_KEY` trước khi build/query hoặc gọi agent.
