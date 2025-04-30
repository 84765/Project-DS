from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import xml.etree.ElementTree as ET
import threading
import datetime
import requests
import sys
import time
import hashlib
import secrets

RECIPE_FILE = "recipe-book.xml"
API_KEY = "e37b51667add46c585347e30a76a4768"
PEERS = set()
USER_FILE = "users.xml"
SECRET_CODE ="bE9nNXKIAQcWJqU"

def hash_password(password):
    salt = "randomsaltvalue5231"
    hashed_password = hashlib.sha256(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()
    return hashed_password

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
            return "Username already exists"
    hashed = hash_password(password)
    user_element = ET.SubElement(root, "user", username=username, password=hashed)
    save_users(tree)
    return "Signup successfull"

def login(username, password):
    tree = load_users()
    root = tree.getroot()
    hash1 = hash_password(password)
    for user in root.findall("user"):
        if user.get("username") == username and user.get("password") == hash1:
            return SECRET_CODE
    return "Login failed"

def authenticate_with_secret(secret_code):
    return secret_code == SECRET_CODE

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
        params = {"query": food, "number": 3, "apiKey": API_KEY}
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

def add_recipe(secret_code, food):
    if not authenticate_with_secret(secret_code):
        return "Authentication failed"
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

    if added_links:
        save(tree)
        replicate_add(food, added_links, timestamp)

    if not added_links:
        return f"\nAll fetched recipes for '{food}' already exist."

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

    existing_recipes = {r.text.split(' (')[0] for r in food_element.findall("recipe")}
    if recipe_link not in existing_recipes:
        entry = ET.SubElement(food_element, "recipe")
        entry.text = f"{recipe_link} ({timestamp})"
        save(tree)

    return f"Recipe '{recipe_link}' synced for '{food}'."

def get_recipes(secret_code, food):
    if not authenticate_with_secret(secret_code):
        return "Authentication failed"

    tree = load()
    root = tree.getroot()

    for item in root.findall("food"):
        if item.get("name") == food:
            recipes = [recipe.text for recipe in item.findall("recipe")]
            return recipes

    return []

def replicate_add(food, added_links, timestamp):
    for peer in list(PEERS):
        try:
            proxy = xmlrpc.client.ServerProxy(peer)
            for link in added_links:
                proxy.add_recipe_remote(food, link, timestamp)
        except Exception as e:
            print(f"Could not sync with {peer}: {e}")

def register_peer(peer_url):
    if peer_url not in PEERS:
        PEERS.add(peer_url)
        print(f"Peer registered: {peer_url}")
    return "Peer registration successful."

def get_all_data():
    """Send entire XML data to new peers."""
    tree = load()
    root = tree.getroot()
    data = {}
    for food_element in root.findall("food"):
        food_name = food_element.get("name")
        recipes = [r.text for r in food_element.findall("recipe")]
        data[food_name] = recipes
    return data

def sync_from_peer(peer_url):
    """Pull recipes from a peer."""
    try:
        proxy = xmlrpc.client.ServerProxy(peer_url)
        data = proxy.get_all_data()
        for food, recipes in data.items():
            for r in recipes:
                link, timestamp = r.rsplit(' (', 1)
                timestamp = timestamp.strip(')')
                add_recipe_remote(food, link, timestamp)
        print(f"Synced data from {peer_url}")
    except Exception as e:
        print(f"Could not sync from {peer_url}: {e}")

def start_server(port, peers):
    global PEERS
    PEERS = set(peers)

    server = SimpleXMLRPCServer(("0.0.0.0", port), allow_none=True)
    server.register_function(add_recipe, "add_recipe")
    server.register_function(add_recipe_remote, "add_recipe_remote")
    server.register_function(get_recipes, "get_recipes")
    server.register_function(register_peer, "register_peer")
    server.register_function(get_all_data, "get_all_data")
    server.register_function(signup, "signup")
    server.register_function(login, "login")

    print(f"Server running on port {port}...")

    for peer in list(PEERS):
        try:
            proxy = xmlrpc.client.ServerProxy(peer)
            proxy.register_peer(f"http://localhost:{port}/")
            sync_from_peer(peer)
        except Exception as e:
            print(f"Could not connect to {peer}: {e}")

    server.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server.py <port> [peer1_url] [peer2_url] ...")
        sys.exit(1)

    port = int(sys.argv[1])
    peers = sys.argv[2:]

    server_thread = threading.Thread(target=start_server, args=(port, peers))
    server_thread.start()
