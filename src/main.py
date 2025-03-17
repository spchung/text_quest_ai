from game.npc.merchant.react.react_merchant import ReActMerchant
from game.player.player import Player
from game.npc.quest_master.quest_master import answer_agent, AnswerAgentInputSchema

def main():
    merchant = ReActMerchant()
    player = Player()

    while True:
        user_input = input("You: ")
        result = merchant.process_input(user_input, player)
        print(f"Merchant: {result}")
        print()
        user_input = input("You: ")
        answer_agent.run()