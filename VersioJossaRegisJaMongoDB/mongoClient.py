from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["recipe_db"]
recipes_collection = db["recipes"]

def load_recipes(user_id):
    user_recipes = recipes_collection.find_one({"user_id": user_id})
    
    if user_recipes:
        return user_recipes
    else:
        return {"user_id": user_id, "recipes": []}


def save_recipes(user_id, recipes_data):
    
    recipes_collection.update_one(
        {"user_id": user_id},
        {"$set": {"recipes": recipes_data["recipes"]}},
        upsert=True
    )