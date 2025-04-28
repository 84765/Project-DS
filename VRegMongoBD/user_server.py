from pymongo import MongoClient
import datetime
import requests
from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn

client = MongoClient("mongodb://localhost:27017/")
db = client["recipe_db"]
users_collection = db["users"]

def register_user(username, password):
    
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        return "User already exists!"
    
    user_id = f"user{users_collection.count_documents({}) + 1}"
    
    new_user = {"user_id": user_id, "username": username, "password": password}
    users_collection.insert_one(new_user)
    return f"User {username} registered successfully!"

def login_user(username, password):
    
    existing_user = users_collection.find_one({"username": username})
    if existing_user and existing_user["password"] == password:
        return existing_user["user_id"]
    else:
        return "Invalid credentials!"

class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

def start_server():
    server = SimpleXMLRPCServer(("localhost", 3000), allow_none=True)
    server.register_function(register_user, "register_user")
    server.register_function(login_user, "login_user")
    print("User Service is running on port 3000...")
    server.serve_forever()

if __name__ == "__main__":
    start_server()