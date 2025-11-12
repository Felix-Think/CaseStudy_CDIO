import certifi
from pymongo import MongoClient


DB_NAME = 'case_state_store' # Tên database bạn muốn tạo
MONGO_URI = "mongodb+srv://nvt120205:thang1202@thangnguyen.8aiscbh.mongodb.net/"

def create_database(DB_NAME = DB_NAME):
    """
    Tạo kết nối đến MongoDB và trả về đối tượng database.
    """
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
    )
    db = client[DB_NAME]
    return db

if __name__ == "__main__":
    db = create_database()
    print(f"Database '{DB_NAME}' created successfully.")