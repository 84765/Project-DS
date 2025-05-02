import xmlrpc.client

def main():
    server_url = input("Enter server URL: ")
    server = xmlrpc.client.ServerProxy(server_url, allow_none=True)

    while True:
        print("\n1. Login")
        print("2. Sign up")
        option = input("Choose an option: ")

        if option == "1":
            username = input("Username: ")
            password = input("Password: ")
            response = server.login(username, password)

            if response == "SUCCESS":
                print("Login successful.")
                break
            else:
                print("Login failed.")

        elif option == "2":
            username = input("Username: ")
            password = input("Password: ")
            response = server.signup(username, password)
            print(response)

        else:
            print("Invalid option.")

    while True:
        print("\n1. Search for recipe")
        print("2. Get saved recipes")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            food = input("Enter food name: ")
            res = server.add_recipe(food)

            if isinstance(res, list):
                print("\nRecipes added:")
                for r in res:
                    print(r)
            else:
                print(res)

        elif choice == "2":
            food = input("Enter food name: ")
            res = server.get_recipes(food)

            if isinstance(res, list) and res:
                print("\nSaved Recipes:")
                for r in res:
                    print(r)
            else:
                print(f"No recipes found for '{food}'.")

        elif choice == "3":
            print("Exiting program...")
            break

        else:
            print("Invalid choice. Choose something else.")

if __name__ == "__main__":
    main()
