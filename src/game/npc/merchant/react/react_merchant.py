from game.npc.merchant.react.react_merchant_statemachine import MerchantStateMachine, MachineError

class ReActMerchant:
    def __init__(self, knowledge_base, personality_traits):
        self.knowledge = knowledge_base
        self.personality = personality_traits
        self.conversation_history = []
        self.state_machine = MerchantStateMachine()
        
    def process_player_input(self, player_message, game_state):
        # OBSERVE
        observation = self._observe(player_message, game_state)
        
        # Detect state transition triggers
        triggers_detected = self._detect_state_triggers(observation)
        
        # Apply any detected triggers to state machine
        self._apply_triggers(triggers_detected)
        
        # test state transition
        response = f"The current state is: {self.state_machine.state}"
        
        # REASON (incorporating current state)
        # current_state = self.state_machine.state
        # state_traits = MerchantStateMachine.state_detail[current_state]['trait']
        # available_actions = MerchantStateMachine.state_detail[current_state]['available_actions']
        
        # reasoning = self._reason(observation, current_state, state_traits)
        
        # # PLAN (constrained by available actions)
        # response_plan = self._plan(reasoning, available_actions)
        
        # # ACT
        # response = self._act(response_plan)
        
        # # Update conversation history
        # self.conversation_history.append({
        #     "player": player_message,
        #     "npc": response,
        #     "state": current_state
        # })
        
        return response
    
    def _observe(self, player_message, game_state):
        """Extract relevant information from player message and game state"""
        # Use NLP/intent recognition to identify:
        # - Player's intent (question, demand, offer, etc.)
        # - Entities mentioned (items, locations, people)
        # - Emotional tone (friendly, hostile, neutral)
        # - References to previous conversations
        return {
            "intent": self._detect_intent(player_message),
            "entities": self._extract_entities(player_message),
            "tone": self._analyze_tone(player_message),
            "game_context": game_state
        }
    
    def _detect_state_triggers(self, observation):
        """Identify if any state transition triggers are present"""
        triggers = []
        
        # Check for specific trigger conditions based on observation
        if "personal_info" in observation["entities"]:
            triggers.append("player_shared_personal_info")
            
        if "bribe" in observation["entities"] or "gold" in observation["entities"] and observation["intent"] == "offer":
            triggers.append("player_offer_bribe")
            
        if observation["tone"] == "threatening":
            triggers.append("player_threaten_npc")
            
        # Add more trigger detection logic as needed
            
        return triggers
    
    def _apply_triggers(self, triggers):
        """Apply detected triggers to the state machine"""
        for trigger in triggers:
            try:
                # Call the trigger method dynamically on the state machine
                trigger_method = getattr(self.state_machine, trigger)
                trigger_method()
            except (AttributeError, MachineError):
                # Trigger not applicable in current state
                pass
    
    def _reason(self, observation, current_state, state_traits):
        """Process information and determine meaning based on current state"""
        # Consider the NPC's current state traits when determining how to respond
        # Different reasoning strategies based on state
        reasoning = {
            "response_type": None,
            "relevant_knowledge": [],
            "emotional_response": None
        }
        
        if current_state == "untrusting":
            # More cautious reasoning, focused on self-protection
            reasoning["emotional_response"] = "cautious"
            if observation["intent"] == "question":
                reasoning["response_type"] = "deflect" if self._is_sensitive_topic(observation) else "basic_info"
                
        elif current_state == "trusting":
            # Business-oriented reasoning
            reasoning["emotional_response"] = "neutral"
            if observation["intent"] == "trade_request":
                reasoning["response_type"] = "trade"
                reasoning["relevant_knowledge"] = self._get_trade_knowledge()
                
        elif current_state == "helpful":
            # More generous reasoning, looking to assist
            reasoning["emotional_response"] = "friendly"
            if observation["intent"] == "question":
                reasoning["response_type"] = "share_secret" if self._knows_secret_about(observation) else "basic_info"
                reasoning["relevant_knowledge"] = self._get_relevant_secrets(observation)
        
        return reasoning
    
    def _plan(self, reasoning, available_actions):
        """Generate response plan based on reasoning and available actions"""
        # Ensure the response type from reasoning is allowed in current state
        if reasoning["response_type"] not in available_actions:
            # Fall back to an available action
            if "basic_info" in available_actions:
                response_type = "basic_info"
            else:
                response_type = available_actions[0]
        else:
            response_type = reasoning["response_type"]
        
        # Plan the specific response
        response_content = self._generate_response_content(response_type, reasoning)
        
        return {
            "response_type": response_type,
            "content": response_content,
            "emotional_tone": reasoning["emotional_response"]
        }
    
    def _act(self, plan):
        """Execute the response plan"""
        # Generate final dialogue text based on the plan
        dialogue = self._format_dialogue(plan["content"], plan["emotional_tone"])
        
        # Any game actions that should accompany the dialogue
        actions = self._determine_accompanying_actions(plan)
        
        return {
            "dialogue": dialogue,
            "actions": actions
        }
    
    # Helper methods would be implemented here
    def _detect_intent(self, message):
        pass
    
    def _extract_entities(self, message):
        pass
    
    def _analyze_tone(self, message):
        pass
    
    def _is_sensitive_topic(self, observation):
        pass
    
    def _get_trade_knowledge(self):
        pass
    
    def _knows_secret_about(self, observation):
        pass
    
    def _get_relevant_secrets(self, observation):
        pass
    
    def _generate_response_content(self, response_type, reasoning):
        pass
    
    def _format_dialogue(self, content, tone):
        pass
    
    def _determine_accompanying_actions(self, plan):
        pass