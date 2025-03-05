from game.npc.merchant import Merchant


def main():
    merchant = Merchant()

    while True:
        user_input = input("You: ")
        result = merchant.process_full_chain(user_input, [])
        print(f"Merchant: {result}")
        print()


if __name__ == '__main__':
    main()