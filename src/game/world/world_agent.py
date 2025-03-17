"""
A trading system for player and merchant interaction
- self containing conversation loop
"""

import instructor
from pydantic import Field
from typing import List, Any
from atomic_agents.agents.base_agent import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm

class WorldAgent:
    def __init__(self):
        self.world_state = WorldState()  # Contains map, NPCs, quests, enemies
        self.player = Player()
        self.memory = WorldMemory()  # For persistent world state
        self.npc_registry = NPCRegistry()  # Contains all NPCs including your merchant
        self.current_location = "starting_town"
        
    def process_input(self, player_input: str):
        # Similar ReAct pattern as your merchant
        observation_result = self.__observe(player_input)
        reasoning_result = self.__reason(observation_result)
        plan_result = self.__plan(player_input, observation_result, reasoning_result)
        action_result = self.__action(plan_result)
        
        # Generate narrative response
        narrative_response = self.__generate_narrative(action_result)
        
        # Update world state and memory
        self.__update_world_state(action_result)
        
        return narrative_response

class WorldIntentDetectionInputSchema(BaseIOSchema):
    """Input schema for World Intent Detection"""
    previous_conversation: str = Field(..., description="Chat history")
    player_message: str = Field(..., description="Player's message")
    current_location: Location = Field(..., description="Player's current location")
    available_intents: List[WorldIntent] = Field(..., description="Available intents")

class WorldIntentDetectionOutputSchema(BaseIOSchema):
    """Output schema for World Intent Detection"""
    detected_intent: str = Field(..., description="Most likely intent")
    confidence_score: float = Field(..., description="Confidence score (0.0-1.0)")


class WorldState(BaseModel):
    locations: Dict[str, Location] = {}
    npcs: Dict[str, NPC] = {}
    quest_states: Dict[str, QuestState] = {}
    time_of_day: TimeOfDay = TimeOfDay.MORNING
    weather: Weather = Weather.CLEAR
    
    def get_location_description(self, location_id: str) -> str:
        """Get narrative description of location"""
        location = self.locations.get(location_id)
        return location.get_description(self.time_of_day, self.weather)
    
    def get_available_actions(self, location_id: str) -> List[WorldAction]:
        """Get actions available at current location"""
        location = self.locations.get(location_id)
        return location.available_actions

class ActionHandler:
    def __init__(self, world_state: WorldState, player: Player):
        self.world_state = world_state
        self.player = player
        self.action_map = {
            "navigate": self.handle_navigation,
            "talk_to_npc": self.handle_npc_interaction,
            "combat": self.handle_combat,
            "use_item": self.handle_item_use,
            "examine": self.handle_examine,
            "quest_action": self.handle_quest_action
        }
    
    def execute_action(self, action: WorldAction) -> ActionResult:
        """Execute an action and return the result"""
        if action.action_type in self.action_map:
            return self.action_map[action.action_type](action)
        return ActionResult(success=False, reason="Unknown action type")
    
    def handle_navigation(self, action: WorldAction) -> ActionResult:
        """Handle player movement between locations"""
        # Implementation for navigation
        
    def handle_npc_interaction(self, action: WorldAction) -> ActionResult:
        """Handle talking to NPCs including your merchant"""
        npc_id = action.params.get("npc_id")
        npc = self.world_state.npcs.get(npc_id)
        
        if isinstance(npc, ReActMerchant):
            # Use your existing merchant logic
            return npc.process_input(action.params.get("message"), self.player)
        
        # Handle other NPC types
    

class NarrativeGenerator:
    def __init__(self, world_state: WorldState):
        self.world_state = world_state
        self.llm = ChatOpenAI(model="gpt-4o-mini")
    
    def generate_location_description(self, location_id: str) -> str:
        """Generate a rich description of the current location"""
        location = self.world_state.locations.get(location_id)
        
        prompt = self.create_location_prompt(location)
        return self.llm.invoke(prompt).content
    
    def generate_action_result_narrative(self, action_result: ActionResult) -> str:
        """Generate narrative description of action results"""
        prompt = self.create_action_result_prompt(action_result)
        return self.llm.invoke(prompt).content

class NPCRegistry:
    def __init__(self):
        self.npcs = {}
    
    def register_npc(self, npc_id: str, npc_instance):
        """Register an NPC with the registry"""
        self.npcs[npc_id] = npc_instance
    
    def get_npc(self, npc_id: str):
        """Get an NPC by ID"""
        return self.npcs.get(npc_id)

class WorldMemory:
    def __init__(self):
        self.event_history = []
        self.player_interactions = {}
        self.quest_progress = {}
    
    def record_event(self, event: WorldEvent):
        """Record a game event"""
        self.event_history.append(event)
    
    def record_npc_interaction(self, npc_id: str, interaction: NPCInteraction):
        """Record interactions with NPCs"""
        if npc_id not in self.player_interactions:
            self.player_interactions[npc_id] = []
        self.player_interactions[npc_id].append(interaction)
    
    def get_recent_events(self, count: int = 5) -> List[WorldEvent]:
        """Get recent events for context"""
        return self.event_history[-count:]

class CombatSystem:
    def __init__(self, player: Player):
        self.player = player
    
    def initiate_combat(self, enemy: Enemy) -> CombatSession:
        """Start a combat encounter"""
        return CombatSession(self.player, enemy)
    
class CombatSession:
    def __init__(self, player: Player, enemy: Enemy):
        self.player = player
        self.enemy = enemy
        self.turn = 1
        self.is_active = True
    
    def process_combat_action(self, player_action: CombatAction) -> CombatRound:
        """Process a single round of combat"""
        # Implementation for turn-based combat

class QuestManager:
    def __init__(self, world_state: WorldState, player: Player):
        self.world_state = world_state
        self.player = player
    
    def check_quest_progress(self, action_result: ActionResult) -> List[QuestUpdate]:
        """Check if an action has progressed any quests"""
        updates = []
        for quest in self.player.quest_log:
            if self.action_progresses_quest(action_result, quest):
                updates.append(self.update_quest_progress(quest, action_result))
        return updates
    
    def action_progresses_quest(self, action_result: ActionResult, quest: Quest) -> bool:
        """Check if an action progresses a specific quest"""
        # Implementation to check quest objectives


def main():
    world_agent = WorldAgent()
    
    # Register your merchant NPC
    merchant = ReActMerchant()
    world_agent.npc_registry.register_npc("magnus_merchant", merchant)
    
    # Game loop
    while True:
        player_input = input("You: ")
        
        if player_input.lower() == "quit":
            break
            
        response = world_agent.process_input(player_input)
        print(response)