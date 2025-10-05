from werkzeug.security import generate_password_hash
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["ride_db"]

username = "admin"
password = "admin123"

# check if already exists
if db.admins.find_one({"username": username}):
    print("Superuser already exists")
else:
    db.admins.insert_one({
        "username": username,
        "password": generate_password_hash(password)
    })
    print(f"Superuser '{username}' created with password '{password}'")
