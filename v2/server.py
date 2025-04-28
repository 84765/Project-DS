from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import xml.etree.ElementTree as ET
import threading
import datetime
import requests
import sys

RECIPE_FILE = "recipe-book.xml"
API_KEY = "e37b51667add46c585347e30a76a4768"
PEERS = []  

def load():
    try:
        tree = ET.parse(RECIPE_FILE)
        return tree
    except FileNotFoundError:
        root = ET.Element("recipes")
        tree = ET.ElementTree(root)
        tree.write(RECIPE_FILE)
        return tree

def save(tree):
    tree.write(RECIPE_FILE)

def fetch_recipe(food):
    try:
        if not food.strip():
            return []

        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "query": food,
            "number": 3,  
            "apiKey": API_KEY
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        recipes = []
        for result in data.get("results", []):
            recipe_id = result.get("id")
            if recipe_id:
                link = f"https://spoonacular.com/recipes/{food.replace(' ', '-')}-{recipe_id}"
                recipes.append(link)

        return recipes

    except requests.exceptions.RequestException as e:
        return f"Error fetching recipes for {food}: {e}"

    except Exception as e:
        return f"Unexpected error for {food}: {e}"

def add_recipe(food):
    recipe_links = fetch_recipe(food)
    if isinstance(recipe_links, str):  
        return recipe_links
    if not recipe_links:
        return f"No recipes found for '{food}'."

    tree = load()
    root = tree.getroot()

    food_element = None
    for recipe in root.findall("food"):
        if recipe.get("name") == food:
            food_element = recipe
            break

    if food_element is None:
        food_element = ET.SubElement(root, "food", name=food)

    existing_recipes = {r.text.split(' (')[0] for r in food_element.findall("recipe")}

    timestamp = datetime.datetime.now().strftime("%m/%d/%y - %H:%M:%S")
    added_links = []

    for link in recipe_links:
        if link not in existing_recipes:
            entry = ET.SubElement(food_element, "recipe")
            entry.text = f"{link} ({timestamp})"
            added_links.append(link)

    if not added_links:
        return f"\nAll fetched recipes for '{food}' already exist."

    save(tree)

    for peer in PEERS:
        try:
            proxy = xmlrpc.client.ServerProxy(peer)
            for link in added_links:
                proxy.add_recipe_remote(food, link, timestamp)
        except Exception as e:
            print(f"Could not sync with {peer}: {e}")

    return added_links  

def add_recipe_remote(food, recipe_link, timestamp):
    tree = load()
    root = tree.getroot()

    food_element = None
    for recipe in root.findall("food"):
        if recipe.get("name") == food:
            food_element = recipe
            break

    if food_element is None:
        food_element = ET.SubElement(root, "food", name=food)

    entry = ET.SubElement(food_element, "recipe")
    entry.text = f"{recipe_link} ({timestamp})"

    save(tree)
    return f"Recipe '{recipe_link}' synced for '{food}'."

def get_recipes(food):
    tree = load()
    root = tree.getroot()

    for item in root.findall("food"):
        if item.get("name") == food:
            recipes = [recipe.text for recipe in item.findall("recipe")]
            return recipes

    return f"No recipes found for '{food}'."

def start_server(port, peers):
    global PEERS
    PEERS = peers

    server = SimpleXMLRPCServer(("0.0.0.0", port), allow_none=True)
    server.register_function(add_recipe, "add_recipe")
    server.register_function(add_recipe_remote, "add_recipe_remote")
    server.register_function(get_recipes, "get_recipes")

    print(f"Server running on port {port}...")
    server.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server.py <port> [peer1_url] [peer2_url] ...")
        sys.exit(1)

    port = int(sys.argv[1])
    peers = sys.argv[2:]

    server_thread = threading.Thread(target=start_server, args=(port, peers))
    server_thread.start()


# 192.168.1.151

# python3 server.py 3000 http://192.168.1.5:3001 http://192.168.1.8:3002
# http://192.168.1.2:3000/