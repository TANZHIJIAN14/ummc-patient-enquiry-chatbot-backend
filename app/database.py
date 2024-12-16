from pymongo import MongoClient
from app.config import config

client = MongoClient(config("MONGO_URI"))  # Replace with your MongoDB URI
db = client[config("MONGO_DB_NAME")]
users_collection = db.get_collection("users")
chat_room_collection = db.get_collection("chat_room")
uploaded_file_collection = db.get_collection("uploaded_file")
feedback_collection = db.get_collection("feedback")
