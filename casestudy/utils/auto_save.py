from load import load_case
from save import save_case

cases = "drowning_pool_001"

# # Save
# context, personas, skeleton = save_case(f"casestudy/cases/{cases}")

# print("🏷️ Case:", context["case_id"])
# print("👥 Số nhân vật:", len(personas))
# print("🎬 Số sự kiện:", len(skeleton["canon_events"]))

#Load dữ liệu từ MongoDB
context, personas, skeleton = load_case(f"{cases}", save_to_disk=False)

# --- Bây giờ bạn có thể xử lý trực tiếp ---
print("🏷️ Chủ đề:", context["topic"])
print("👥 Nhân vật:", [p["name"] for p in personas])
print("🎬 Sự kiện đầu:", skeleton["canon_events"][0]["title"])