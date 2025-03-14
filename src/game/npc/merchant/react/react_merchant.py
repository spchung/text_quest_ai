from typing import List
from game.player.player import Player
from game.npc.merchant.react.models import ChatHistory, KnowledgeBase, Inventory, \
    NameDescriptionModel, Quest, Item, StateProtectedResource, \
    ResonResult, ObservationResult, PlanResult
from game.npc.merchant.react.react_merchant_statemachine import MerchantStateMachine, MachineError
from game.npc.merchant.react.agents.transition_detection import transition_detection_agent, TransitionDetectionInputSchema
from game.npc.merchant.react.agents.action_detection import action_detection_agent, ActionDetectionInputSchema
from game.npc.merchant.react.agents.knowledge_base_worker import knowledge_base_worker_agent, KnowledgeBaseWorkerInputSchema, KnowledgeBaseWorkerOutputSchema
from game.npc.merchant.react.agents.reflection_reason import reflection_reason_agent, ReflectionReasonInputSchema, ReflectionReasonOutputSchema


class ReActMerchant:
    def __init__(self):
        self.conversation_history = []
        self.state_machine = MerchantStateMachine()
        self.knowledge_base = self.__init_knowledge_base()
        self.chat_history = ChatHistory()
        self.inventory = self.__init_inventory()
    
    def __init_inventory(self):
        # Load inventory from file or database
        return Inventory(
            items=[
                Item(name="Sword", type="weapon", price=50),
                Item(name="Potion of Healing", type="potion", price=10),
                Item(name="Leather Armor", type="armour", price=30),
                Item(name="Ice Staff", type="weapon", price=100),
            ],
            gold=100
        )

    def __init_knowledge_base(self):
        # Load knowledge base from file or database
        return KnowledgeBase(
            quests = StateProtectedResource[List[Quest]](
                allowed_states=[
                    self.state_machine.state_enum.HELPFUL.value, 
                    self.state_machine.state_enum.TRUSTING.value
                ],
                data=[
                    Quest(name="Defeat Evil Dragon", description="Defeat the ancient evil dragon that slumbers beneath the mountain.", reward=1000),
                ],
            ),
            secrets = StateProtectedResource[List[NameDescriptionModel]](
                allowed_states=[
                    self.state_machine.state_enum.TRUSTING.value
                ],
                data=[
                    NameDescriptionModel(name="Secret Passage", description="There is a secret passage behind the waterfall that leads to the dragon's lair."),
                    NameDescriptionModel(name="Dragon Weakness", description="The dragon is vulnerable to ice magic.")
                ],
            ),
            generic_info = StateProtectedResource[List[NameDescriptionModel]](
                allowed_states=[
                    self.state_machine.state_enum.HELPFUL.value, 
                    self.state_machine.state_enum.TRUSTING.value,
                    self.state_machine.state_enum.UNTRUSTING.value,
                ],
                data=[
                    NameDescriptionModel(name="Town History", description="The town was founded by the legendary hero Sir Percival. It was first settled over 500 years ago."),
                    NameDescriptionModel(name="Local Tavern", description="The tavern is a popular spot for adventurers to gather and share stories."),
                ]
            )
        )
    
    def process_input(self, player_msg, player):

        # ADD user message
        self.chat_history.add_player(player_msg)

        # observation
        ## possible state transitions
        ## possible actions to take
        observ_res = self.__observe(player_msg)
        print(f"[LOG] - observation: {observ_res}")

        # reason
        ## consider context 
        ### previous conversation
        ## consider actions
        reason_res = self.__reason(observ_res, player)
        print(f"[LOG] - Reason: {reason_res}")

        # plan
        ## decide on actions to take
        ## decide on state transitions
        ## consider next response possibilities
        plan_res = self.__plan(player_msg, observ_res, reason_res)
        print(f"[LOG] - Plan: {plan_res}")

        # act
        ## if actions - call tools
        ## if state transition - iterate state
        res = self.__action(plan_res)

        # response
        ## consider action results
        ## consider context
        ## formulate response

    def __observe(self, msg, confidence_threshold=0.7) -> ObservationResult:
        """Extract relevant information from player message and game state"""
        # - Possible State transitions
        # - Possible actions to take
        # - Sentiment (friendly, hostile, neutral)
        transition_resp = transition_detection_agent.run(
            TransitionDetectionInputSchema(
                player_message=msg,
                current_state=self.state_machine.states_map[self.state_machine.state],
                available_transition_conditions=self.state_machine.all_transition_conditions
            )
        )
        ## sentiment analysis (TODO)
        print("[WARN] - Sentiment analysis not implemented yet")

        ## actions (maybe move to plan?)
        action_resp = action_detection_agent.run(
            ActionDetectionInputSchema(
                player_message=msg,
                current_state=self.state_machine.states_map[self.state_machine.state],
            )
        )

        condition = None if (
            transition_resp.detected_condition == 'none' or 
            transition_resp.confidence_score < confidence_threshold
        ) else transition_resp.detected_condition
        
        action = None if (
            action_resp.detected_action == 'none' or 
            action_resp.confidence_score < confidence_threshold
        ) else action_resp.detected_action

        return ObservationResult(
            condition=condition,
            action=action,
            sentiment=None ## TODO
        )

    def __reason(self, observe_res: ObservationResult, player: Player):
        '''All context and reasoning'''
        ## condiser state attributes
        current_state = self.state_machine.states_map[self.state_machine.state]
        
        ### emption/attitude
        npc_traits = current_state.trait

        # ## consider chat history
        # prev_convo = self.chat_history.get_last_k_turns()

        ## consider knowledge base
        relevant_knowledge = self.__collect_relevant_knowledge(observe_res)

        return ResonResult(
            information=relevant_knowledge.information if relevant_knowledge else None,
            reasoning=relevant_knowledge.reasoning if relevant_knowledge else None,
        )

    def __collect_relevant_knowledge(self, observe_res: ObservationResult) -> KnowledgeBaseWorkerOutputSchema:
        """Collect relevant knowledge from the knowledge base"""
        if not observe_res.action or observe_res.action =='none':
            return None
        
        # check if is allowed action in current state
        current_state = self.state_machine.states_map[self.state_machine.state]
        if observe_res.action not in [action.name for action in current_state.available_actions]:
            return None
        
        # find condition
        condition = None

        for cond in self.state_machine.all_transition_conditions:
            if cond.name == observe_res.condition:
                condition = cond
                break
        
        ## get the protected knowledge on this state
        protected_knowledge = self.knowledge_base.get_protected_knowledge(current_state)
        
        ## Call knowledge base worker agent to get relevant knowledge
        knowledge_resp = knowledge_base_worker_agent.run(
            KnowledgeBaseWorkerInputSchema(
                current_state=current_state,
                detected_condition=condition,
                detected_action=observe_res.action,
                npc_knowledge_base=protected_knowledge,
                npc_inventory=self.inventory
            )
        )

        return knowledge_resp
        
    def __plan(
            self, 
            player_msg: str, 
            observation_res: ObservationResult, 
            reason_res: ResonResult, 
        ):
        """Decide on actions to take based on observation and reasoning"""

        # transitions
        state_transition_name = None
        if observation_res.condition:
            state_transition_name = observation_res.condition
        
        # action
        action_name = None
        if observation_res.action:
            action_name = observation_res.action

        print("[WARN] - PLAN llm logic not implemented yet")
        
        reflection_res = reflection_reason_agent.run(
            ReflectionReasonInputSchema(
                player_input=player_msg,
                current_state=self.state_machine.states_map[self.state_machine.state],
                detected_transition_condition=self.state_machine.transition_lookup(state_transition_name),
                detected_action=self.state_machine.action_lookup(action_name),
                previous_step_reasoning=reason_res.reasoning,
                npc_knowledge_base=self.knowledge_base.get_protected_knowledge(self.state_machine.states_map[self.state_machine.state]),
                previous_conversation=self.chat_history.get_last_k_turns()
            )
        )

        ## cancel action and transition if not approved
        if not reflection_res.transition_condition_approval.approved:
            state_transition_name = None
        
        if not reflection_res.action_approval.approved:
            action_name = None

        # return result
        return PlanResult(
            player_message=player_msg,
            action=self.state_machine.action_lookup(action_name),
            transition_condition=self.state_machine.transition_lookup(state_transition_name),
            reasoning=reflection_res.reasoning,
        )
    

    def __action(self, plan_res: PlanResult):
        """Perform actions and collect results"""
        action = plan_res.action
        if action.confirmation_required:
            is_confirmed = self.__handle_action_confirmation(action)
            if not is_confirmed:
                print("[LOG] - Action rejected.")
            else: 
                print("[LOG] - Action confirmed.")
        pass


    def __handle_action_confirmation(self, action):
        """ ask for user confirmation """
        if action.name == 'take_bribe':
            price = 5
            res = input(f"[CONFIRM]: The NPC is requesting {price} gold for action {action.name}. Do you accept? (y/n) ")

            if res.lower() == 'yes' or res.lower() == 'y':
                return True
        
        return False


