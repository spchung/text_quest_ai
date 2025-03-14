import instructor
from pydantic import Field
from typing import List
from game.npc.merchant.react.models import *
from game.npc.merchant.react.models import State, ProtectedKnowledgeBase, Inventory, FewShotIntent
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm

class ReflectionReasonInputSchema(BaseIOSchema):
    """Input schema for the Reflection Reason Agent."""
    player_input: str = Field(..., description="PLayer input to the NPC")
    current_state: State = Field(..., description="Current state of the NPC")
    detected_transition_condition: FewShotIntent | None = Field(..., description="Detected possible transition condition")
    detected_action: Action | None = Field(..., description="Detected action")
    previous_step_reasoning: str | None = Field(..., description="Reasoning behind the previous step.")
    npc_knowledge_base: ProtectedKnowledgeBase = Field(..., description="Knowledge base of the NPC in the curent state.")
    previous_conversation: str = Field(..., description="chat history between user and npc")

class ReflectionReasonOutputSchema(BaseIOSchema):
    """Output schema for the Reflection Reason Agent."""
    transition_condition_approval: ApprovalWrapper[FewShotIntent] = Field(..., description="Approval for the detected transition condition")
    action_approval: ApprovalWrapper[Action] = Field(..., description="Approval for the detected action")
    reasoning: str = Field(..., description="Reasoning behind the decision")

reflection_reason_prompt = SystemPromptGenerator(
    background=[
        "You are a reflection reason agent for an NPC in a role-playing game.",
        "Your task is to decide whether the NPC should take a detected transition condition for state",
        "transition and whether the NPC should execute a detected action.",
        "You have access to the player input, current state, detected transition condition, detected action,",
        "previous step reasoning, NPC's knowledge base, and previous conversation history."
    ],

    steps=[
        "Take into account of the player input and previous conversation history.",
        "Analyze the player input in the context of previous conversations and the current state of the NPC.",
        "Consider the detected transition condition and action with the previous step reasoning.",
        "Decide whether the NPC should take the detected transition condition for state transition.",
        "Decide whether the NPC should execute the detected action.",
        "Provide reasoning behind the decisions made."
    ],

    output_instructions=[
        "Ensure the decisions align with the NPC's current state and previous interactions.",
        "Provide clear and concise reasoning for the decisions made.",
        "Consider the impact of the decisions on the NPC's traits and the overall game experience."
    ],
)

reflection_reason_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(
            llm
        ),
        model='gpt-4o-mini',
        system_prompt_generator=reflection_reason_prompt,
        input_schema=ReflectionReasonInputSchema,
        output_schema=ReflectionReasonOutputSchema
    )
)