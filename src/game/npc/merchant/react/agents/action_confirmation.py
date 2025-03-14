import instructor
from pydantic import Field
from typing import List
from game.npc.merchant.react.models import *
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm


'''
NOT IN USE
'''

class ActionConfirmationInputSchema(BaseIOSchema):
    npc_confirmation_query: str = Field(..., description="The npc's confirmation request to the player.")
    player_message: str = Field(..., description="The player's response to a confirmation request.")
    action: Action = Field(..., description="The action being confirmed.")

class ActionConfirmationOutputSchema(BaseIOSchema):
    confirmed: bool = Field(..., description="Player's answer to a confirmation request. (True = confirm; False = not confirm)")

action_confirm_prompt = SystemPromptGenerator(
    background = [
        "You are a sentiment anal"
    ]
)

