from pymongo import MongoClient
import datetime
import requests
from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn

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

def add_recipe(user_id, food):
    recipe_link = fetch_recipe(food)

    if recipe_link.startswith("Error") or recipe_link.startswith("No recipe found"):
        return f"No recipe found for {food}."

    recipes_data = load_recipes(user_id)

    for recipe in recipes_data["recipes"]:
        if recipe["food"].lower() == food.lower():
            return f"Recipe for {food} already exists!\nLink: {recipe['recipe_link']}"

    timestamp = datetime.datetime.now().strftime("%m/%d/%y - %H:%M:%S")
    new_recipe = {
        "food": food,
        "recipe_link": recipe_link,
        "timestamp": timestamp
    }

    recipes_data["recipes"].append(new_recipe)
    save_recipes(user_id, recipes_data)

    return f"Recipe for {food} added!\nLink: {recipe_link}"

def get_recipes(user_id):
    recipes_data = load_recipes(user_id)
    if not recipes_data["recipes"]:
        return "No recipes found."
    return recipes_data["recipes"]

def fetch_recipe(food):
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={food}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data["meals"]:
            meal = data["meals"][0]
            return meal["strSource"] or meal["strYoutube"] or f"https://www.google.com/search?q={food}+recipe"
        else:
            return f"No recipe found for {food}."
    except requests.exceptions.RequestException as e:
        return f"Error fetching recipe for {food}: {e}"

def delete_recipe(user_id, food):
    recipes_data = load_recipes(user_id)
    recipes = recipes_data["recipes"]

    for recipe in recipes:
        if recipe["food"].lower() == food.lower():
            recipes.remove(recipe)
            save_recipes(user_id, recipes_data)
            return f"Recipe for {food} deleted!"

    return f"No recipe found for {food}."

class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

def start_server():
    server = SimpleXMLRPCServer(("localhost", 3001), allow_none=True)
    server.register_function(add_recipe, "add_recipe")
    server.register_function(get_recipes, "get_recipes")
    print("Recipe Service is running on port 3001...")
    server.serve_forever()

if __name__ == "__main__":
    start_server()