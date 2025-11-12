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

def add_virtual_data(db):
    """
    Thêm dữ liệu ảo vào database để kiểm tra.
    """
    sample_collection = db['sample_collection']
    sample_data = {
        "name": "Test Data",
        "value": 12345
    }
    result = sample_collection.insert_one(sample_data)
    print(f"Inserted document id: {result.inserted_id}")
    
if __name__ == "__main__":
    db = create_database(DB_NAME=DB_NAME)
    add_virtual_data(db)
    print(db.client.list_database_names())
    db1 = MongoClient("mongodb+srv://nvt120205:thang1202@thangnguyen.8aiscbh.mongodb.net/",
        tls=True,
        tlsCAFile=certifi.where())["User"]
    collections = db1.list_collection_names()
    print(collections)
