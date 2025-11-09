# 🧠 CaseStudy Cloud & Pinecone Deployment Guide

Hướng dẫn chi tiết triển khai dự án **CaseStudy App** và **Agent API** lên **Render Cloud**, đồng thời tích hợp với **Pinecone** để quản lý vector database.

---

## 🚀 Cấu trúc ứng dụng

Dự án có **2 service chính**:

1. **App chính (Case List)**  
   Chạy ứng dụng chính cho người dùng cuối.  
   ```bash
   poetry run uvicorn casestudy.app.main:app --reload --port 8000
   ```

2. **Agent API (Docs / Pinecone Integration)**  
   Chạy API phụ trợ hỗ trợ truy vấn Pinecone.  
   ```bash
   poetry run uvicorn api_casestudy.main:app --reload --port 9000
   ```

Khi deploy, cần thay đổi thành:
```bash
poetry run uvicorn casestudy.app.main:app --host 0.0.0.0 --port $PORT
poetry run uvicorn api_casestudy.main:app --host 0.0.0.0 --port $PORT
```

---

## 🔑 Cấu hình Pinecone

1. **Tạo tài khoản tại [https://www.pinecone.io](https://www.pinecone.io)**  
   → Lưu lại API Key được cung cấp.

2. **Tạo Index mới**  
   - Chọn loại **Custom**  
   - Sử dụng model `text-3-small`  
   - Tham số:
     ```
     Dimension: 1536
     Metric: cosine
     ```
   - Ví dụ index name: `casestudy-index`

3. **File quản lý Pinecone**  
   Tạo file `pinecone-manager.py` để xử lý thao tác với Pinecone (file này đã được push lên GitHub).

---

## ☁️ Deploy lên Render Cloud

Truy cập: [https://render.com](https://render.com)

---

### 🧩 Service #1 – App chính (Case List)

1. **Tạo Web Service mới**
   - `New +` → `Web Service`
   - Chọn repo GitHub của bạn

2. **Thông tin cài đặt**
   - **Name:** `casestudy-app`  
   - **Region:** gần Việt Nam (chọn *Singapore* nếu có)

3. **Cấu hình Build & Start**
   ```bash
   Build Command:
   pip install poetry && poetry install --no-root

   Start Command:
   poetry run uvicorn casestudy.app.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Environment Variables**
   ```env
   OPENAI_API_KEY=sk-xxxx
   PINECONE_API_KEY=xxxx
   PINECONE_INDEX=casestudy-index
   PINECONE_REGION=us-east-1
   ```

5. **Health Check Path**
   ```
   /health
   ```

6. **Kết quả sau khi deploy**
   ```
   https://casestudy-app.onrender.com
   ```

---

### 🤖 Service #2 – API Agent (Docs)

Lặp lại các bước trên, chỉ thay đổi:

- **Name:** `casestudy-agent`  
- **Start Command:**
  ```bash
  poetry run uvicorn api_casestudy.main:app --host 0.0.0.0 --port $PORT
  ```

Sử dụng **cùng Environment Variables** như service #1.

**Kết quả sau khi deploy:**
```
App chính: https://casestudy-app.onrender.com/case-list
API Agent: https://casestudy-agent.onrender.com/docs
```

---

## 🔗 Liên kết giữa 2 service

Nếu **App chính** cần gọi đến **Agent API**,  
hãy sử dụng endpoint:
```
https://casestudy-agent.onrender.com
```

Trong file cấu hình hoặc code, cập nhật URL này cho phần tích hợp API Agent.

---

## 🧾 Ghi chú thêm

- Toàn bộ cấu hình `poetry`, dependencies, và Pinecone cần được đồng bộ giữa 2 service.  
- Kiểm tra kỹ `PINECONE_REGION` (thường là `us-east-1`).  
- Nên dùng môi trường `.env` trong local để test trước khi deploy.

---

## ✅ Kết quả mong đợi

Sau khi triển khai thành công:
- `https://casestudy-app.onrender.com/case-list` sẽ hiển thị giao diện chính.
- `https://casestudy-agent.onrender.com/docs` cung cấp API docs để tương tác với Pinecone.
