from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import xml.etree.ElementTree as ET
import datetime
import requests
import sys
import threading

RECIPE_FILE = "recipe-book.xml"
PEERS = set()
FETCH_SERVICE_URL = "http://localhost:5001/fetch"  

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
        res = requests.get(FETCH_SERVICE_URL, params={"food": food}, timeout=5)
        return res.json().get("recipes", [])
    except Exception as e:
        return f"Error: {e}"

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

    existing = {r.text.split(" (")[0] for r in food_element.findall("recipe")}
    timestamp = datetime.datetime.now().strftime("%m/%d/%y - %H:%M:%S")
    added = []

    for link in recipe_links:
        if link not in existing:
            entry = ET.SubElement(food_element, "recipe")
            entry.text = f"{link} ({timestamp})"
            added.append(link)

    if added:
        save(tree)
        replicate_add(food, added, timestamp)

    return added if added else f"All recipes for '{food}' already exist."

def get_recipes(food):
    tree = load()
    root = tree.getroot()

    for item in root.findall("food"):
        if item.get("name") == food:
            return [r.text for r in item.findall("recipe")]

    return []

def add_recipe_remote(food, link, timestamp):
    tree = load()
    root = tree.getroot()

    food_element = None
    for recipe in root.findall("food"):
        if recipe.get("name") == food:
            food_element = recipe
            break

    if food_element is None:
        food_element = ET.SubElement(root, "food", name=food)

    existing = {r.text.split(" (")[0] for r in food_element.findall("recipe")}
    if link not in existing:
        entry = ET.SubElement(food_element, "recipe")
        entry.text = f"{link} ({timestamp})"
        save(tree)
    return "Synced"

def replicate_add(food, links, timestamp):
    for peer in list(PEERS):
        try:
            proxy = xmlrpc.client.ServerProxy(peer)
            for link in links:
                proxy.add_recipe_remote(food, link, timestamp)
        except:
            pass  

def register_peer(url):
    PEERS.add(url)
    return "Peer registered"

def start_server(port):
    server = SimpleXMLRPCServer(("0.0.0.0", port), allow_none=True)
    server.register_function(add_recipe)
    server.register_function(get_recipes)
    server.register_function(add_recipe_remote)
    server.register_function(register_peer)
    print(f"Manager server running on port {port}...")
    server.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1])
    peers = sys.argv[2:]

    for p in peers:
        PEERS.add(p)
    threading.Thread(target=start_server, args=(port,), daemon=True).start()
    while True:
        pass


# Ammi :
# python3 server.py 4000 http://192.168.1.151:3000/
# http://192.168.1.108:4000/

# Mine :
# python3 server.py 3000 http://192.168.1.108:4000/
# http://192.168.1.151:3000/