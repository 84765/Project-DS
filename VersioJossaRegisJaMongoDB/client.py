from xmlrpc.client import ServerProxy

def main():
    print("Welcome to the Recipe Management System!")
    
    user_server = ServerProxy("http://localhost:3000")
    recipe_server = ServerProxy("http://localhost:3001")

    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Choose an option: ")
        
        if choice == "1":
            username = input("Enter username: ")
            password = input("Enter password: ")
            print(user_server.register_user(username, password))
        
        elif choice == "2":
            username = input("Enter username: ")
            password = input("Enter password: ")
            user_id = user_server.login_user(username, password)
            if user_id != "Invalid credentials!":
                print(f"Welcome {username}!")
                while True:
                    print("\n1. Add Recipe")
                    print("2. View Recipes")
                    print("3. Delete Recipe")
                    print("4. Logout")

                    sub_choice = input("Choose an option: ")

                    if sub_choice == "1":
                        food = input("Enter food name: ")
                        print(recipe_server.add_recipe(user_id, food))
                    elif sub_choice == "2":
                        recipes = recipe_server.get_recipes(user_id)
                        if isinstance(recipes, list):
                            for recipe in recipes:
                                print(f"\nFood: {recipe['food']}\nLink: {recipe['recipe_link']}\nTimestamp: {recipe['timestamp']}\n" + "-" * 40)
                        else:
                            print(recipes)
                    elif sub_choice == "3":
                        food = input("Enter food name to delete: ")
                        print(recipe_server.delete_recipe(user_id, food))
                    elif sub_choice == "4":
                        print("Logging out...")
                        break
            else:
                print(user_id)
        
        elif choice == "3":
            print("Exiting program...")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()