## test

from game.npc.merchant.react.react_merchant import ReActMerchant
from game.player.player import Player
from game.npc.merchant.react.sub_system.trade import TradeSystem

script = [
    # "Hello there, I am Stephen the Great!", 
    # "I come from the east and is eager to help.",
    # "I am looking for some adventure"
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
    trade_sys = TradeSystem(player, merchant)


    while trade_sys.completed == False:
        if not trade_sys.initiaited:
            print(trade_sys.greeting())
        else:
            res = trade_sys.process_input(next_message(script))
            print(res)
    
if __name__ == '__main__':
    main()