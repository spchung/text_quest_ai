## test

from game.npc.merchant.react.react_merchant import ReActMerchant
from game.player.player import Player

def main():
    player = Player()
    merchant = ReActMerchant()

    while True:
        player_message = input("You: ")

        merchant.process_input(player_message, player)
    
if __name__ == '__main__':
    main()