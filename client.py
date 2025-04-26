import xmlrpc.client

server = xmlrpc.client.ServerProxy("http://localhost:3000/")

def main():
    while True:
        print("\n1. Search for recipe")
        print("2. Get recipes")
        print("3. Exit")
        option = input("Choose an option: ")

        if option == "1":
            food = input("Enter food: ")
            response = server.add_recipe(food)
            print(response)

        elif option == "2":
            food = input("Saved recipes for food: ")
            response = server.get_recipes(food)
            print(response if isinstance(response, list) else response)

        elif option == "3":
            print("Exiting program...")
            break

        else:
            print("Not a valid choice, choose something else")

if __name__ == "__main__":
    main()
