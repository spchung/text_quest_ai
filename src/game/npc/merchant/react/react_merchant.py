from typing import List, Optional
from game.player.player import Player
from game.npc.merchant.react.models import *
from game.npc.merchant.react.react_merchant_statemachine import MerchantStateMachine, MachineError
from game.npc.merchant.react.agents.transition_detection import transition_detection_agent, TransitionDetectionInputSchema
from game.npc.merchant.react.agents.action.action_detection import action_detection_agent, ActionDetectionInputSchema
from game.npc.merchant.react.agents.knowledge_base_worker import knowledge_base_worker_agent, KnowledgeBaseWorkerInputSchema, KnowledgeBaseWorkerOutputSchema
from game.npc.merchant.react.agents.reflection_reason import reflection_reason_agent, ReflectionReasonInputSchema
from game.npc.merchant.react.agents.npc_response import response_agent, NpcResponseInputSchema
from game.npc.merchant.react.agents.action.action_confirmation import action_confirm_agent, ActionConfirmationInputSchema

## utility functions
def inventory_transaction(from_inventory: Inventory, to_inventory: Inventory, transaction_value: int, item: Optional[Item] = None) -> TransactionResult:
    """ on way transaction """
    result = TransactionResult(is_successful=False)
    ## check if item is in inventory
    if item and item not in from_inventory.items:
        result.reasoning = "Item not found in inventory."
        return result

    ## check if enough gold
    if transaction_value > from_inventory.gold:
        result.reasoning = "Not enough gold."
        return result
    
    ## perform transaction
    if item:
        from_inventory.items.remove(item)
        to_inventory.items.append(item)
    
    from_inventory.gold -= transaction_value
    to_inventory.gold += transaction_value

    result.is_successful = True
    return result
    
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
                    Quest(
                        name="Defeat Evil Dragon", 
                        description="Defeat the ancient evil dragon that slumbers beneath the mountain.", 
                        npc_dialog_option="Prompt the player towards giving the npc a bribe to reveal the dragon's weakness.",
                        reward=1000
                    ),
                ],
            ),
            secrets = StateProtectedResource[List[NameDescriptionModel]](
                allowed_states=[
                    self.state_machine.state_enum.HELPFUL.value
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
        # print(f"[LOG] - observation: {observ_res}")

        # reason
        ## consider context 
        ### previous conversation
        ## consider actions
        reason_res = self.__reason(observ_res, player)
        print(f"[REASON]: {reason_res.reasoning}")

        # plan
        ## decide on actions to take
        ## decide on state transitions
        ## consider next response possibilities
        plan_res = self.__plan(player_msg, observ_res, reason_res)
        print(f"[PLAN]: {plan_res.reasoning}")

        # act
        ## if actions - call tools
        ## if state transition - iterate state
        action_phase_res = self.__action(plan_res, player)
        print(f"[ACTION]: {action_phase_res.reasoning}")

        # response
        npc_response_res = response_agent.run(
            NpcResponseInputSchema(
                # if overide player message then use that
                player_input=action_phase_res.overridden_player_message if action_phase_res.overridden_player_message else player_msg,
                current_state=self.state_machine.states_map[self.state_machine.state],
                previous_conversation=self.chat_history.get_last_k_turns(),
                npc_knowledge_base=self.knowledge_base.get_protected_knowledge(self.state_machine.states_map[self.state_machine.state]),
                observationStepResult=observ_res,
                reasonStepResult=reason_res,
                planStepResult=plan_res,
                actionStepResult=action_phase_res
            )
        )

        self.chat_history.add_npc(npc_response_res.npc_response)

        print("\n==============================================")
        print(f"[LOG] - NPC State: {self.state_machine.state}")
        print(f"[LOG] - NPC Action: {action_phase_res.action.name if action_phase_res.action else 'None'}")
        print(f"[LOG] - NPC Transition: {action_phase_res.transition_condition.name if action_phase_res.transition_condition else 'None'}")
        print(f"[LOG] - NPC Plan Reasoning: {plan_res.reasoning}")
        print("==============================================\n")
        
        print(f"{self.state_machine.name}: {npc_response_res.npc_response}\n")

    def __observe(self, msg, confidence_threshold=0.7) -> ObservationResult:
        """Extract relevant information from player message and game state"""
        # - Possible State transitions
        # - Possible actions to take
        # - Sentiment (friendly, hostile, neutral)

        transition_resp = transition_detection_agent.run(
            TransitionDetectionInputSchema(
                previous_conversation=self.chat_history.get_last_k_turns(),
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
                previous_conversation=self.chat_history.get_last_k_turns(),
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

        return ReasonResult(
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
        
    def __plan(self, player_msg: str, observation_res: ObservationResult, reason_res: ReasonResult):
        """Decide on actions to take based on observation and reasoning"""

        # transitions
        state_transition_name = None
        if observation_res.condition:
            state_transition_name = observation_res.condition
        
        # action
        action_name = None
        if observation_res.action:
            action_name = observation_res.action
        
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
    
    def __action(self, plan_res: PlanResult, player:Player) -> ActionResult:
        """Perform actions and collect results"""
        result = ActionResult(
            action=plan_res.action,
            transition_condition=plan_res.transition_condition,
            action_is_successful=False,
            transition_condition_is_successful=False,
        )

        action = plan_res.action
        
        # try perform action
        perf_action_result = self.__perform_action(action, player)
        if not perf_action_result.is_successful:
            result.action_is_successful = False
            result.reasoning = perf_action_result.reasoning
            return result
        
        # try perform state transition
        if plan_res.transition_condition:
            perf_transition_result = self.__handle_state_transition(plan_res.transition_condition, perf_action_result)
            if not perf_transition_result.is_successful:
                result.transition_condition_is_successful = False
                result.reasoning = perf_transition_result.reasoning
                return result
        
        result.action_is_successful = True
        result.transition_condition_is_successful = True
        result.reasoning = perf_action_result.reasoning
        result.overridden_player_message = perf_action_result.overridden_player_message
        return result

    def __handle_state_transition(self, transition_condition: FewShotIntent, action_result: PerformActionResult) -> PerformTransitionConditionResult:
        ''' handle specific actions only '''
        result = PerformTransitionConditionResult(
            transition_condition=transition_condition,
            is_successful=True,
            reasoning=None
        )

        if action_result.action.name == 'take_bribe' and not action_result.is_successful:
            result.is_successful = False
            result.reasoning = "Bribe declined. State transition failed."
            return result

        # run state transition
        try:
            self.state_machine.transition(transition_condition.name)
            result.is_successful = True
        except MachineError as e:
            result.is_successful = False
            result.reasoning = str(e)
        
        return result

    def __perform_action(self, action: Action, player: Player) -> PerformActionResult:
        """ ask for user confirmation """
        result = PerformActionResult(
            action=action,
            is_successful=False,
            reasoning=None
        )
        if action is None:
            result.is_successful = True
            result.reasoning = "No action to perform."
            return result


        if action.name == 'take_bribe':
            bribe_price = 5
            prompt = action_confirm_agent.run(
                ActionConfirmationInputSchema(
                    current_state=self.state_machine.states_map[self.state_machine.state],
                    action=action,
                    npc_knowledge_base=self.knowledge_base.get_protected_knowledge(self.state_machine.states_map[self.state_machine.state]),
                    context={"bribe_price": "5 gold coins"}
                )
            ).response

            res = input(f"{prompt} (y/n) ")
            if res.lower() == 'yes' or res.lower() == 'y':
                # perform gold transation
                transaction_res = inventory_transaction(self.inventory, player.inventory, bribe_price)
                result.is_successful = transaction_res.is_successful
                result.reasoning = transaction_res.reasoning
                result.overridden_player_message = "I have paid the bribe."
            else:
                result.reasoning = "Bribe declined"
                result.overridden_player_message = "I have declined the bribe."

        elif action.name == 'give_quest':
            state_knowledge = self.knowledge_base.get_protected_knowledge(self.state_machine.states_map[self.state_machine.state]),
            prompt = action_confirm_agent.run(
                ActionConfirmationInputSchema(
                    current_state=self.state_machine.states_map[self.state_machine.state],
                    action=action,
                    npc_knowledge_base=state_knowledge[0] if state_knowledge else None,
                    context=state_knowledge[0].quests if state_knowledge else None,
                )
            ).response

            res = input(f"{prompt} (y/n) ")

            if res.lower() == 'yes' or res.lower() == 'y':
                ## TODO: dynamicly get quest
                self.__give_quest(state_knowledge[0].quests[0], player)
                
                result.is_successful = True
                result.reasoning = "The player has accepted the quest. Assume the quest has been added to the player's quest log."
                result.overridden_player_message = "I have accepted the quest."
            else:
                result.reasoning = "Quest declined."
                result.overridden_player_message = "I have declined the quest."

        elif action.name == "trade":
            state_knowledge = self.knowledge_base.get_protected_knowledge(self.state_machine.states_map[self.state_machine.state]),
            prompt = action_confirm_agent.run(
                ActionConfirmationInputSchema(
                    current_state=self.state_machine.states_map[self.state_machine.state],
                    action=action,
                    npc_knowledge_base=state_knowledge[0] if state_knowledge else None,
                    context=self.inventory,
                )
            ).response

            res = input(f"{prompt} (y/n) ")
            if res.lower() == 'yes' or res.lower() == 'y':
                ### TODO: TRADE AGENT
                ## ENTER TRADE MODE
                '''
                1. provide list of items
                2. user input what they want
                3. try to trade (perform transaction)
                4. complete or retry
                '''
                ##
                result.is_successful = True
                result.reasoning = "Trade accepted."
            else:
                result.reasoning = "Trade offer declined."
                result.overridden_player_message = "I have declined the trade offer."

        else:
            result.is_successful = True

        return result

    def __give_quest(self, quest: Quest, player: Player) -> None:
        # add quest to player quest log
        player.quest_log.append(quest)

        # mark quest as given
        quest.is_given = True
        