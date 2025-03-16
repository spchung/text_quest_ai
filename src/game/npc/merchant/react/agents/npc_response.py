import instructor
from pydantic import Field
from typing import List
from game.npc.merchant.react.models import *
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm

""" Agent for final npc response message """
class NpcResponseInputSchema(BaseIOSchema):
    """Input schema for the NPC Response Agent."""
    player_input: str | None = Field(..., description="Player input to the NPC")
    current_state: State = Field(..., description="Current state of the NPC")
    previous_conversation: str = Field(..., description="Chat history between user and NPC")
    npc_knowledge_base: ProtectedKnowledgeBase = Field(..., description="Knowledge base of the NPC in the current state")
    actionStepResult: ActionResult = Field(..., description="Action step results.")

class NpcResponseOutputSchema(BaseIOSchema):
    """Output schema for the NPC Response Agent."""
    npc_response: str = Field(..., description="NPC's response to the player input")

npc_response_prompt = SystemPromptGenerator(
    background=[
        "You are an NPC in a role-playing game.",
        "Adhere to the character setting and current state of the NPC."
    ],

    steps=[
        "Analyze the player input and previous conversation history.",
        "Consider the NPC's character setting and current state.",
        "Pay extra attention to the actionStepResult, take account of the success and failure of this action into your response",
        "If the action result is more important than the player's message, focus on the action result",
        "Generate a response answers the player's message that take into account the actions result"
    ],

    output_instructions=[
        "Ensure the response aligns with the NPC's character setting and current state.",
        "Consider the results of the observation, reasoning, planning, and action steps.",
        "Provide a response that is engaging and consistent with the NPC's personality."
        "avoid using the word 'bribe' in the response"
    ],
)
    
response_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(
            llm
        ),
        model='gpt-4o-mini',
        system_prompt_generator=npc_response_prompt,
        input_schema=NpcResponseInputSchema,
        output_schema=NpcResponseOutputSchema,
        temperature=0.7
    )
)