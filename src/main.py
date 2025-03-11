from game.npc.merchant.merchant import Merchant
from game.player.player import Player
from game.npc.quest_master.quest_master import answer_agent, AnswerAgentInputSchema

def main():
    merchant = Merchant()
    player = Player()

    while True:
        user_input = input("You: ")
        result = merchant.process_input(user_input, player)
        print(f"Merchant: {result}")
        print()
        user_input = input("You: ")
        answer_agent.run()

# Sample context for the agent
# context = "The atomic_agents library is a framework for building AI agents with structured inputs and outputs."

# # Function to run the agent
# def run_agent(question, context_info):
#     # Create the input for the agent
#     agent_input = AnswerAgentInputSchema(question=question)
    
#     # Run the agent
#     result = answer_agent.run(agent_input)
    
#     # Return the result
#     return result

# # Main loop for continuous interaction
# def main():
#     print("Welcome to the Q&A Assistant! Type 'exit' to quit.")
#     print("Ask questions about: " + context)
    
#     while True:
#         # Get user input
#         user_question = input("\nYour question: ")
        
#         # Check if user wants to exit
#         if user_question.lower() in ['exit', 'quit', 'bye']:
#             print("Goodbye!")
#             break
        
#         # Process the question and get response
#         try:
#             response = run_agent(user_question, context)
            
#             # Print the response
#             print("\nAnswer:")
#             print(response.text_output)
#             print(f"\nConfidence: {response.confidence_score}")
            
#         except Exception as e:
#             print(f"Error: {e}")

if __name__ == "__main__":
    main()

