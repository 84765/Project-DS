from xmlrpc.server import SimpleXMLRPCServer
import xml.etree.ElementTree as ET
import threading
import datetime
import requests


RECIPE = "recipe-book.xml"

def load():
    try:
        tree = ET.parse(RECIPE)
        return tree
    except FileNotFoundError:
        root = ET.Element("recipes")
        tree = ET.ElementTree(root)
        tree.write(RECIPE)
        return tree

def save(tree):
    tree.write(RECIPE)

def add_recipe(food):
    recipe_link = fetch_recipe(food)
    if "http" not in recipe_link:
        return f"No recipe found for '{food}'."

    tree = load()
    root = tree.getroot()

    food_element = None
    for recipe in root.findall("food"):
        if recipe.get("name") == food:
            food_element = recipe
            break

    if food_element is None:
        food_element = ET.SubElement(root, "food", name=food)

    timestamp = datetime.datetime.now().strftime("%m/%d/%y - %H:%M:%S")
    entry = ET.SubElement(food_element, "recipe")
    entry.text = f"{recipe_link} ({timestamp})"

    save(tree)
    return f"Recipe '{recipe_link}' added to '{food}'."

def get_recipes(food):
    tree = load()
    root = tree.getroot()

    for item in root.findall("food"):
        if item.get("name") == food:
            recipes = [recipe.text for recipe in item.findall("recipe")]
            return recipes

    return f"No recipes found for '{food}'."

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

def start_server():
    server = SimpleXMLRPCServer(("localhost", 3000), allow_none=True)
    server.register_function(add_recipe, "add_recipe")
    server.register_function(get_recipes, "get_recipes")

    print("Server running on port 3000...")
    server.serve_forever()

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
