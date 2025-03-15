import instructor
from pydantic import Field
from typing import List
from game.npc.merchant.react.models import *
from game.npc.merchant.react.models import State, ProtectedKnowledgeBase, Inventory, FewShotIntent
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm


class NpcResponseInputSchema(BaseIOSchema):
    """Input schema for the NPC Response Agent."""
    player_input: str = Field(..., description="Player input to the NPC")
    current_state: State = Field(..., description="Current state of the NPC")
    detected_transition_condition: FewShotIntent | None = Field(..., description="Detected possible transition condition")
    detected_action: Action | None = Field(..., description="Detected action")
    previous_step_reasoning: str | None = Field(..., description="Reasoning behind the previous step.")
    npc_knowledge_base: ProtectedKnowledgeBase = Field(..., description="Knowledge base of the NPC in the current state.")
    previous_conversation: str = Field(..., description="Chat history between user and NPC")