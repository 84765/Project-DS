from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import requests

API_KEY = "e37b51667add46c585347e30a76a4768"

class RecipeServiceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path != "/recipes":
            self.send_error(404, "Not found")
            return

        query = urllib.parse.parse_qs(parsed_path.query)
        food = query.get("food", [""])[0]

        if not food:
            self.send_error(400, "Missing 'food' parameter")
            return

        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {"query": food, "number": 3, "apiKey": API_KEY}

        try:
            response = requests.get(url, params=params)
            data = response.json()
            results = data.get("results", [])
            recipes = []
            for r in results:
                recipe_id = r.get("id")
                if recipe_id:
                    link = f"https://spoonacular.com/recipes/{food.replace(' ', '-')}-{recipe_id}"
                    recipes.append(link)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(recipes).encode())
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")

def run(server_class=HTTPServer, handler_class=RecipeServiceHandler, port=8081):
    server = server_class(("", port), handler_class)
    print(f"Microservice running on port {port}...")
    server.serve_forever()

if __name__ == "__main__":
    run()