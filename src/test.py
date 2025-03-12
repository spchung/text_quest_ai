## test

from game.npc.merchant.react.react_merchant_statemachine import MerchantStateMachine
from game.npc.merchant.react.agents.transition_detection import transition_detection_agent, IntentDetectionInputSchema

def main():
    machine = MerchantStateMachine()

    while True:
        msg = input("You: ")

        all_conditions = set()
        for transitions in machine.state_config.transitions:
            all_conditions.update(transitions.conditions)

        input_data = IntentDetectionInputSchema(
            player_message=msg,
            current_state=machine.states_map[machine.state],
            available_transition_conditions=list(all_conditions)
        )

        response = transition_detection_agent.run(input_data)
        
        # if condition detected - try to move state
        if response.detected_conditions != 'none':
            machine.transition(response.detected_conditions)
        
        print(f"[LOG]: Machine State: {machine.state}")


    
if __name__ == '__main__':
    main()