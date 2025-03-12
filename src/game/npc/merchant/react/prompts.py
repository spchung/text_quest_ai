from typing import List
from atomic_agents.agents.base_agent import BaseIOSchema
from game.npc.merchant.react.models import StateTransition
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# collection of atomic agent Prompts

MERCHANT_PROMPTS = {
    'trigger':{
        'detect_trigger':""
    }
}

## DETECT State Transition Trigger
class DetectTransitionInputSchema(BaseIOSchema):
    """Input schema for state transition condition"""
    available_transitions: List[StateTransition]

class DetectTransitionOutputSchema(BaseIOSchema):
    """Output schema for state transition condition"""