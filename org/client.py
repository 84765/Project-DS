import xmlrpc.client

def main():
    server_url = input("Enter server : ")
    server = xmlrpc.client.ServerProxy(server_url)

    token = None

    while True:
        if not token:
            print("1. Login")
            print("2. Sign up")
            option = input("Choose an option: ")
            if option == "1":
                username = input("Enter username: ")
                password = input("Enter password: ")

                token = server.login(username, password)
                if ("failed" in token.lower()):
                    print("Login failed.")
                    token = None
                    break
            elif option == "2":
                username = input("Enter username: ")
                password = input("Enter password: ")
                response = server.signup(username, password)
                print(response)
                
            else:
                print("Invalid option.")
                continue
        print("\n1. Search for recipe")
        print("2. Get recipes")
        print("3. Exit")
        option = input("Choose an option: ")

        if option == "1":
            food = input("Enter food: ")
            response = server.add_recipe(token, food)
            if isinstance(response, list):
                print("\nFetched recipes:")
                for link in response:
                    print(link)
            else:
                print(response)

        elif option == "2":
            food = input("Saved recipes for food: ")
            response = server.get_recipes(token, food)
            if isinstance(response, list):
                for r in response:
                    print(r)
                if not response:
                    print(f"No recipes found for '{food}'.")
            else:
                print(response)

        elif option == "3":
            print("Exiting program...")
            break

        else:
            print("Not a valid choice, choose something else")

if __name__ == "__main__":
    main()
