## test

from game.npc.merchant.react.react_merchant import ReActMerchant
from game.player.player import Player
from game.npc.merchant.react.sub_system.trade import TradeSystem

script = [
    'I want the staff'
]

def next_message(script):
    if script:
        msg = script.pop(0)
        print(f"You: {msg}")
        return msg
    else:
        return input("You: ")
    
def main():
    player = Player(gold=50)
    merchant = ReActMerchant()
    merchant.state_machine.transition('player_offer_bribe')
    trade_sys = TradeSystem(player, merchant)


    while trade_sys.completed == False:
        if not trade_sys.initiaited:
            print(trade_sys.greeting())
        else:
            res = trade_sys.process_input(next_message(script))
            print(res)
    
if __name__ == '__main__':
    main()