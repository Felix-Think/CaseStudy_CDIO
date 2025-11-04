# =============================================
# 📦 save.py — Lưu dữ liệu CaseStudy vào MongoDB
# =============================================
import sys
import json
from pathlib import Path

import certifi
from pymongo import MongoClient

# -------------------------
# ⚙️ Cấu hình MongoDB
# -------------------------
MONGO_URI = "mongodb+srv://nvt120205:thang1202@thangnguyen.8aiscbh.mongodb.net/"
DB_NAME = "case_study_db"

CASESTUDY_ROOT = Path(__file__).resolve().parents[1]
LOCAL_CASES_DIR = CASESTUDY_ROOT / "cases"


# -------------------------
# 💾 Hàm lưu case
# -------------------------
def save_case(case_folder):
    """
    Lưu dữ liệu từ thư mục chứa context/personas/skeleton vào MongoDB.
    Trả về tuple: (context, personas, skeleton)
    """
    try:
        data_dir = _resolve_data_dir(case_folder)
    except FileNotFoundError as exc:
        print(f"❌ Không tìm thấy dữ liệu trong thư mục '{case_folder}': {exc}")
        return None, None, None

    # Kết nối MongoDB
    client = MongoClient(
            MONGO_URI,
            tls=True,
            tlsCAFile=certifi.where(),
        )
    db = client[DB_NAME]

    # Đọc context.json
    with (data_dir / "context.json").open("r", encoding="utf-8") as f:
        context = json.load(f)
    case_id = context.get("case_id") or _infer_case_id(case_folder, data_dir)
    context["case_id"] = case_id

    # Xóa dữ liệu cũ trước khi ghi
    db.contexts.delete_many({"case_id": case_id})
    db.personas.delete_many({"case_id": case_id})
    db.skeletons.delete_many({"case_id": case_id})

    # Đọc personas.json
    personas_path = data_dir / "personas.json"
    with personas_path.open("r", encoding="utf-8") as f:
        personas_payload = json.load(f)
        personas = personas_payload["personas"] if isinstance(personas_payload, dict) else personas_payload
        for p in personas:
            p.pop("_id", None)
            p["case_id"] = case_id

    # Đọc skeleton.json
    skeleton_path = data_dir / "skeleton.json"
    with skeleton_path.open("r", encoding="utf-8") as f:
        skeleton = json.load(f)
    skeleton.pop("_id", None)
    skeleton["case_id"] = case_id

    # Ghi vào MongoDB
    db.contexts.insert_one(context)
    db.personas.insert_many(personas)
    db.skeletons.insert_one(skeleton)

    print(f"✅ Đã lưu case '{case_id}' vào MongoDB thành công!")
    return context, personas, skeleton


# -------------------------
# 🚀 Chạy từ terminal
# -------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❗Cách dùng: python save.py <tên_folder_case>")
        print("👉 Ví dụ: python save.py electric_shock_001")
    else:
        case_folder = sys.argv[1]
        save_case(case_folder)


def _resolve_data_dir(case_folder: str) -> Path:
    """
    Trả về Path tới thư mục chứa context/personas/skeleton.
    Hỗ trợ truyền trực tiếp đường dẫn logic_memory hoặc thư mục case.
    """
    raw_path = Path(case_folder)
    candidates = []

    bases = {
        raw_path,
        LOCAL_CASES_DIR / raw_path,
        LOCAL_CASES_DIR / raw_path.name,
    }

    if not raw_path.is_absolute():
        bases.add((Path.cwd() / raw_path).resolve())
        bases.add((CASESTUDY_ROOT / raw_path).resolve())

    for base in bases:
        if not base.exists():
            continue
        for candidate in (base, base / "logic_memory"):
            if candidate.is_dir() and (candidate / "context.json").exists():
                return candidate.resolve()

    raise FileNotFoundError("Thiếu context.json trong các đường dẫn dự phòng.")


def _infer_case_id(original_input: str, data_dir: Path) -> str:
    """
    Lấy case_id từ context.json, fallback theo tên thư mục.
    """
    if data_dir.name != "logic_memory":
        return data_dir.name
    parent = data_dir.parent
    if parent and parent.name:
        return parent.name
    return Path(original_input).stem
