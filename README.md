# CaseStudy Project

Dự án này sử dụng **Conda (Python 3.12)** và **Poetry** để quản lý thư viện.

---

### 1. Clone repository

```bash
git clone https://github.com/Felix-Think/CaseStudy
cd CaseStudy
```

---

### 2. Cài Poetry nếu chưa có

#### Cài poetry toàn cục:

```bash
pip install poetry
```

#### Kiểm tra:

```bash
poetry --version
```

---

### 3. Liên kết Poetry với Conda environment

#### Lấy đường dẫn python trong Conda:

```bash
which python     # Linux / macOS
where python     # Windows
```

#### Ví dụ:

```
/home/username/anaconda3/envs/casestudy/bin/python
```

#### Chạy lệnh liên kết:

```bash
poetry env use /home/username/anaconda3/envs/casestudy/bin/python
```

---

### 4. Cài dependencies từ `pyproject.toml`

Nếu chưa có `pyproject.toml`, khởi tạo:

```bash
poetry init
```

Sau đó cài thư viện:

```bash
poetry install
```

---

### 💡 Lưu ý khi cài thư viện

Khi muốn thêm thư viện vào project, hãy dùng:

```bash
poetry add <package_name>
```

❌ **Không sử dụng** `pip install` hay `conda install` vì sẽ làm lệch môi trường.

---

## Chạy local (Poetry)

```bash
poetry run uvicorn casestudy.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Mặc định cần các biến môi trường trong file `.env`:

```
SECRET_KEY=your-random-secret
MONGO_URI=...
MONGO_DB=case_study_db
OPENAI_API_KEY=...
PINECONE_API_KEY=...
ALLOW_PINECONE_FALLBACK=1
```

Lưu ý cookie:
- Trình duyệt sẽ chặn cookie nếu chạy trên HTTP kèm `secure=true`. Để test cookie, hãy dùng HTTPS hoặc deploy cùng Render.

---

## Deploy Render

Build Command:
```
poetry install --no-interaction --no-ansi
```

Start Command (khuyên dùng):
```
poetry run gunicorn -k uvicorn.workers.UvicornWorker casestudy.app.main:app --bind 0.0.0.0:$PORT --log-level info --access-logfile - --error-logfile -
```

Biến Môi Trường bắt buộc:
- `SECRET_KEY` (bắt buộc cho SessionMiddleware)
- `MONGO_URI`, `MONGO_DB`
- `OPENAI_API_KEY`
- `PINECONE_API_KEY` (hoặc bật `ALLOW_PINECONE_FALLBACK=1`)
- `FRONTEND_ORIGINS` (tùy chọn, ví dụ: `https://your-frontend.onrender.com`; mặc định `*`)
- `COOKIE_DOMAIN` (tùy chọn, nếu muốn set domain cho cookie)
- `APP_LOG_LEVEL=DEBUG` (tạm thời khi debug), `APP_DEBUG_ERRORS=1`

HTTPS/Cookie trên Render:
- Phải bật Force HTTPS trên Render.
- Cookie đăng nhập được set với `secure=true` và `samesite=none` để hoạt động cross-site.

Health check:
```
GET /api/health
```

Tạo session agent:
```
POST /api/agent/agent/sessions
{
	"case_id": "electric_shock_001"
}
```
Hoặc nếu đã gọn prefix `/api/agent/sessions` theo cấu hình của bạn.
