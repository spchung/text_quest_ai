import instructor
from pydantic import Field
from typing import List, Any
from game.npc.merchant.react.models import *
from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema

'''
NOT IN USE
'''

class ActionConfirmationInputSchema(BaseIOSchema):
    """ Action Confirm Message Input Schema """
    current_state: State = Field(..., description="Current state of the NPC")
    action: Action = Field(..., description="The action to be confirmed.")
    npc_knowledge_base: ProtectedKnowledgeBase = Field(..., description="Knowledge base of the NPC in the current state")
    context: Any | None = Field(default=None, description="Additonal context about the action to assist the npc response")

class ActionConfirmationOutputSchema(BaseIOSchema):
    """ Action Confirm Message Output Schema """
    response: str = Field(..., description="The NPC's formulated confirmation request to the player about whether the player will take this action.")

action_confirm_prompt = SystemPromptGenerator(
    background = [
        "You are an NPC in a role-playing game.",
        "Adhere to the character setting and current state of the NPC."
    ],

    steps=[
        "Consider the action, current state, previous conversation, npc knowledge base and context"
        "Formulate a message to ask for the player's intent about the action"
        "You may share any relevant information from the provided context"
    ],

    output_instructions=[
        "Ensure the response aligns with the NPC's character setting and current state.",
        "Consider the results of the observation, reasoning, planning, and action steps.",
        "The response must be a question that prompts the user to respond with a general yes/no."
        "avoid using the word 'bribe' in the response"
    ],
)

action_confirm_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(
            llm
        ),
        model='gpt-4o-mini',
        system_prompt_generator=action_confirm_prompt,
        input_schema=ActionConfirmationInputSchema,
        output_schema=ActionConfirmationOutputSchema,
        memory=None,
        temperature=0,  # Low temperature for more deterministic intent detection
        max_tokens=None,
    ) 
)

