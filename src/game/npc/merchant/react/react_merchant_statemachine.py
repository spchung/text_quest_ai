from transitions import Machine, MachineError
from collections import defaultdict
from typing import List
from enum import Enum
from game.npc.merchant.react.models import *
class MerchantStateEnum(Enum):
    UNTRUSTING = 'untrusting'
    TRUSTING = 'trusting'
    HELPFUL = 'helpful'
class MerchantStateMachine:
    state_enum = MerchantStateEnum

    init_state = state_enum.UNTRUSTING.value
    
    states_map = {
        state_enum.UNTRUSTING.value: State(
            name=state_enum.UNTRUSTING.value,
            trait="Distant and cold. Greeting the player with limited enthusiasm. You love to keep secrets and trade them for profit.",
            available_actions=[
                Action(
                    name="basic_info",
                    description="Provide simple, non-sensitive information from your knowledge base"
                ),
                Action(
                    name="question_player",
                    description="Ask the player questions to determine their intentions."
                ),
                Action(
                    confirmation_required=True,
                    name="take_bribe",
                    description="Accept money for information only when the player explicitly offers gold."
                ),
            ]
        ),
        state_enum.TRUSTING.value: State(
            name=state_enum.TRUSTING.value,
            trait="Courteous but calculating. Primary objective is to trade items with profit.",
            available_actions=[
                Action(
                    name="basic_info",
                    description="Provide simple, non-sensitive information from your knowledge base"
                ),
                Action(
                    name="trade",
                    description="Offer to buy/sell items with player."
                ),
                Action(
                    confirmation_required=True,
                    name="give_quest",
                    description="Offer the player quests from your quest log."
                ),
                Action(
                    confirmation_required=True,
                    name="take_bribe",
                    description="Accept money for information"
                ),
            ]
        ),
        state_enum.HELPFUL.value: State(
            name=state_enum.HELPFUL.value,
            trait="Friendly and enthusiastic to help. Tries to offer player quest and secrets that might help the player.",
            available_actions=[
                Action(
                    name="share_secret",
                    description='Share secrets from your hidden secrets log.'
                ),
                Action(
                    name="trade",
                    description="Offer to buy/sell items with player."
                ),
                Action(
                    confirmation_required=True,
                    name="give_quest",
                    description="Offer the player quests from your quest log."
                )
            ]
        )
    }

    state_config = NpcConfig(
        states = list(states_map.values()),
        transitions=[
            StateTransition(
                source=states_map[state_enum.UNTRUSTING.value],
                destination=states_map[state_enum.TRUSTING.value],
                conditions=[
                    FewShotIntent(
                        name="player_shared_personal_info",
                        examples=[
                            "My name is ___.",
                            "I am a traveller from the far west. They call me ___"
                        ],
                    )
                ]
            ),
            StateTransition(
                source=states_map[state_enum.UNTRUSTING.value],
                destination=states_map[state_enum.HELPFUL.value],
                conditions=[
                    FewShotIntent(
                        name="player_offer_bribe",
                        examples=[
                            "Some gold for some information?",
                            "Will some gold change your mind?",
                            "I will offer you some gold for information."
                        ],
                    )
                ]
            ),
            StateTransition(
                source=states_map[state_enum.TRUSTING.value],
                destination=states_map[state_enum.HELPFUL.value],
                conditions=[
                    FewShotIntent(
                        name="player_offer_bribe",
                        examples=[
                            "Some gold for some information?",
                            "Will some gold change your mind?",
                            "I will offer you some gold for information."
                        ],
                    )
                ]
            ),
            StateTransition(
                source=states_map[state_enum.TRUSTING.value],
                destination=states_map[state_enum.UNTRUSTING.value],
                conditions=[
                    FewShotIntent(
                        name="player_threaten_npc",
                        examples=[
                            "I will hurt you if you don't comply",
                            "Don't you dare thinking about lying to me.",
                            "You do not want me as your enemy."
                        ],
                    )
                ]
            ),
            StateTransition(
                source=states_map[state_enum.HELPFUL.value],
                destination=states_map[state_enum.UNTRUSTING.value],
                conditions=[
                    FewShotIntent(
                        name="player_threaten_npc",
                        examples=[
                            "I will hurt you if you don't comply",
                            "Don't you dare thinking about lying to me.",
                            "You do not want me as your enemy."
                        ],
                    )
                ]
            ),
        ]
    )

    def __init__(self):
        self.machine = Machine(
            model=self, 
            states=[state.name for state in MerchantStateMachine.state_config.states], 
            initial=MerchantStateMachine.init_state
        )

        # build state transition map
        self.transition_map = defaultdict(List[StateTransition]) ## src_state_name - List[Transitions]
        for transition in MerchantStateMachine.state_config.transitions:
            # register in transition map
            self.transition_map[transition.source.name] = self.transition_map.get(transition.source.name, []) + [transition]
            # register transition in state machine
            for condition in transition.conditions:
                self.machine.add_transition(
                    trigger=condition.name,
                    source=transition.source.name,
                    dest=transition.destination.name
                )
        
        self.all_transition_conditions = self._get_all_conditions()
        self.transition_map = {condition.name: condition for condition in self.all_transition_conditions}
        print(f"Transition map: {self.transition_map}")
        self.action_map = self._get_action_map()
    
    def _get_all_conditions(self):
        all_conditions = set()
        for transitions in self.state_config.transitions:
            all_conditions.update(transitions.conditions)
        return list(all_conditions)

    def _get_action_map(self):
        action_map = {}
        for state in self.state_config.states:
            for action in state.available_actions:
                if not action.name in action_map:
                    action_map[action.name] = action
        return action_map

    def action_lookup(self, action_name):
        return self.action_map.get(action_name, None)

    def transition_lookup(self, transition_name):
        return self.transition_map.get(transition_name, None)

    def transition(self, incoming_condition_name) -> None:
        try:
            getattr(self, incoming_condition_name)()
        except (AttributeError, MachineError):
            print(f"[ERROR]: {incoming_condition_name} is not a valid transition on state: {self.state}")



        
