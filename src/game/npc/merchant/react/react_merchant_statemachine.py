from transitions import Machine, MachineError
from collections import defaultdict
from typing import List

from game.npc.merchant.react.models import *

class MerchantStateMachine:

    init_state = 'trusting'
    
    states_map = {
        "untrusting": State(
            name="untrusting",
            trait="Distant and cold. Greeting the player with limited enthusiasm.",
            available_actions=[
                Action(
                    name="basic_info",
                    description="Provide simple, non-sensitive information about topics you know about."
                ),
                Action(
                    name="question_player",
                    description="Ask the player questions to determine their intentions"
                ),
                Action(
                    name="take_bribe",
                    description="Accept money for information"
                ),
            ]
        ),
        "trusting": State(
            name="trusting",
            trait="Courteous but calculating. Primary objective is to trade items with profit.",
            available_actions=[
                Action(
                    name="basic_info",
                    description="Provide simple, non-sensitive information about topics you know about."
                ),
                Action(
                    name="trade",
                    description="Offer to buy/sell items with player."
                ),
                Action(
                    name="give_quest",
                    description="Offer the player quests from your quest log."
                ),
                Action(
                    name="take_bribe",
                    description="Accept money for information"
                ),
            ]
        ),
        "helpful": State(
            name="helpful",
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
                source=states_map['untrusting'],
                destination=states_map['trusting'],
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
                source=states_map['untrusting'],
                destination=states_map['helpful'],
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
                source=states_map['trusting'],
                destination=states_map['helpful'],
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
                source=states_map['trusting'],
                destination=states_map['untrusting'],
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
                source=states_map['helpful'],
                destination=states_map['untrusting'],
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
    
    def _get_all_conditions(self):
        all_conditions = set()
        for transitions in self.state_config.transitions:
            all_conditions.update(transitions.conditions)
        return all_conditions

    
    def transition(self, incoming_condition_name) -> None:
        try:
            getattr(self, incoming_condition_name)()
        except (AttributeError, MachineError):
            print(f"[ERROR]: {incoming_condition_name} is not a valid transition on state: {self.state}")



        
