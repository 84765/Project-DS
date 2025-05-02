from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
API_KEY = "4a42850c2b6f403abc43ee9eeb74f0da"

@app.route("/fetch", methods=["GET"])
def fetch():
    food = request.args.get("food", "")
    if not food:
        return jsonify({"error": "Food query missing"}), 400

    try:
        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {"query": food, "number": 3, "apiKey": API_KEY}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        recipes = []
        for result in data.get("results", []):
            recipe_id = result.get("id")
            if recipe_id:
                link = f"https://spoonacular.com/recipes/{food.replace(' ', '-')}-{recipe_id}"
                recipes.append(link)

        return jsonify({"recipes": recipes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5001)
