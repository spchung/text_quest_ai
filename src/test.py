## test

from game.npc.merchant.react.react_merchant import ReActMerchant

def main():
    merchant = ReActMerchant()

    while True:
        player_message = input("You: ")

        oversrve_res = merchant._observe(player_message)
        print("OBS: ",oversrve_res)
        
        knowledge = merchant._collect_relevant_knowledge(oversrve_res)

        print("KNS: ",knowledge)

    
if __name__ == '__main__':
    main()