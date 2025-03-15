import instructor
from pydantic import Field
from typing import List
from game.npc.merchant.react.models import *
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm


"""
An agent that find the most relavant information using
- current_state attributes
- detected transition conditions
- detected actions
"""

class KnowledgeBaseWorkerInputSchema(BaseIOSchema):
    """Input schema for the Knowledge Base Worker."""
    current_state: State = Field(..., description="Current state of the NPC")
    detected_condition: FewShotIntent | None = Field(..., description="Detected transition condition")
    detected_action: str | None = Field(..., description="Detected action")
    npc_knowledge_base: ProtectedKnowledgeBase = Field(..., description="Knowledge base of the NPC in the curent state.")
    npc_inventory: Inventory = Field(..., description="The npc's inventory")

class KnowledgeBaseWorkerOutputSchema(BaseIOSchema):
    """Output schema for the Knowledge Base Worker."""
    information: List[str] = Field(..., description="List of relevant information to share with the player")
    reasoning: str = Field(..., description="Reasoning behind the provided information")

# Create the system prompt generator
knowledge_base_worker_prompt = SystemPromptGenerator(
    background=[
        "You are a knowledge base worker for an NPC in a role-playing game.",
        "Your task is to provide relevant information based on the current state, detected transition conditions, and actions.",
        "You have access to the NPC's knowledge base and inventory."
    ],
    steps=[
        "Analyze the current state of the NPC.",
        "Consider the detected transition condition and action.",
        "Retrieve relevant information from the knowledge base and inventory.",
        "You may choose multiple pieces of information to share with the player.",
        "Be sure to check if the information you share is compliant with the allowed actions in the current state."
        "Explain the reasoning behind the information provided."
    ],
    output_instructions=[
        "Ensure the response is relevant to the current state, transition condition, and action.",
        "Provide concise and informative responses based on the available information.",
        "If sharing sensitive information, make sure it aligns with the NPC's current state and do not overshare."
    ],
)

knowledge_base_worker_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(
            llm
        ),
        model='gpt-4o-mini',
        system_prompt_generator=knowledge_base_worker_prompt,
        input_schema=KnowledgeBaseWorkerInputSchema,
        output_schema=KnowledgeBaseWorkerOutputSchema,
        memory=None,
        temperature=0,  # Low temperature for more deterministic response
        max_tokens=None,
    ) 
)