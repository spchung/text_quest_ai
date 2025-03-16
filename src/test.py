## test

from game.npc.merchant.react.react_merchant import ReActMerchant
from game.player.player import Player

script = [
    "Hello there, I am Stephen the Great!", 
    "I come from the east and is eager to help.",
    "I am looking for some adventure"
]

script2 = [
    "Hello there, I am Stephen the Great!", 
    "I will offer you gold for any information",
]

trade_script = [
    "Hello there, I am Stephen the Great!", 
    "I would like to trade with you",
]

def next_message(script):
    if script:
        msg = script.pop(0)
        print(f"You: {msg}")
        return msg
    else:
        return input("You: ")
    
def main():
    player = Player()
    merchant = ReActMerchant()

    while True:
        player_message = next_message(trade_script)

        merchant.process_input(player_message, player)
    
if __name__ == '__main__':
    main()