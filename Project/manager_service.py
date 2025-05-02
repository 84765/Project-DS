from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import xml.etree.ElementTree as ET
import threading
import datetime
import requests
import sys
import hashlib
import os

RECIPE_FILE = "recipe-book.xml"
USER_FILE = "users.xml"
PEERS = set()
FETCH_SERVICE_URL = "http://localhost:5001/fetch"

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def load_users():
    try:
        tree = ET.parse(USER_FILE)
        return tree
    except FileNotFoundError:
        root = ET.Element("users")
        tree = ET.ElementTree(root)
        tree.write(USER_FILE)
        return tree

def save_users(tree):
    tree.write(USER_FILE)

def signup(username, password):
    tree = load_users()
    root = tree.getroot()

    for user in root.findall("user"):
        if user.get("username") == username:
            return "Username already exists."
        
    hashed = hash_password(password)
    ET.SubElement(root, "user", username=username, password=hashed)

    save_users(tree)
    return "Signup successful."

def login(username, password):
    tree = load_users()
    root = tree.getroot()
    hashed = hash_password(password)

    for user in root.findall("user"):
        if user.get("username") == username and user.get("password") == hashed:
            return "SUCCESS"
        
    return "Login failed."

def load_recipes():
    try:
        tree = ET.parse(RECIPE_FILE)
        return tree
    
    except FileNotFoundError:
        root = ET.Element("recipes")
        tree = ET.ElementTree(root)
        tree.write(RECIPE_FILE)
        return tree

def save_recipes(tree):
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

    tree = load_recipes()
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
        save_recipes(tree)
        replicate_add(food, added, timestamp)

    return added if added else f"All recipes for '{food}' already exist."

def get_recipes(food):
    tree = load_recipes()
    root = tree.getroot()

    for item in root.findall("food"):
        if item.get("name") == food:
            return [r.text for r in item.findall("recipe")]

    return []

def add_recipe_remote(food, link, timestamp):
    tree = load_recipes()
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
        save_recipes(tree)
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
    server.register_function(signup)
    server.register_function(login)
    print(f"Server running on port {port}...")
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
# python fetch_service.py 
# python manager_service.py 4000 http://192.168.1.151:3000/
# python client.py 
# http://192.168.1.108:4000/

# Mine :
# python3 fetch_service.py 
# python3 manager_service.py 3000 http://192.168.1.108:4000/
# python3 client.py 
# http://192.168.1.151:3000/