from game.npc.merchant import Merchant
from game.player.player import Player

def main():
    merchant = Merchant()
    player = Player()

    while True:
        user_input = input("You: ")
        result = merchant.process_input(user_input, player)
        print(f"Merchant: {result}")
        print()


if __name__ == '__main__':
    main()