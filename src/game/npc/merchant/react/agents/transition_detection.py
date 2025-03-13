import instructor
from pydantic import Field
from typing import List
from game.npc.merchant.react.models import *
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm

class TransitionDetectionInputSchema(BaseIOSchema):
    """Input schema for the Intent Detection Agent."""
    player_message: str = Field(..., description="The message from the player to the NPC")
    current_state: State = Field(..., description="Current state of the NPC")
    available_transition_conditions: List[FewShotIntent] = Field(..., description="List of available state transition conditions")

class TransitionDetectionOutputSchema(BaseIOSchema):
    """Output schema for the Intent Detection Agent."""
    detected_condition: str = Field(..., description="Most likely transition condition detected in the player's message")
    confidence_score: float = Field(..., description="Confidence score of the detected result (from 0.0 - 1.0)")

# Create the system prompt generator
intent_detection_prompt = SystemPromptGenerator(
    background=[
        "You are an expert intent detection system for an NPC in a role-playing game.",
        "Your task is to analyze player messages and detect intents that satisfy state transition conditions",
        "You have access to a library of few-shot examples for each possible condition."
    ],
    steps=[
        "Carefully analyze the player's message.",
        "Compare it to the few-shot examples for each possible intent from the current state.",
        "Detect any matching intents and assign confidence scores.",
        "Determine if any detected intents should trigger a state transition."
    ],
    output_instructions=[
        "Only detect intents that are truly present in the player's message.",
        "Assign reasonable confidence scores (0.0 to 1.0) based on how closely the message matches the examples.",
    ],
)

transition_detection_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(
            llm
        ),
        model='gpt-4o-mini',
        system_prompt_generator=intent_detection_prompt,
        input_schema=TransitionDetectionInputSchema,
        output_schema=TransitionDetectionOutputSchema,
        memory=None,
        temperature=0,  # Low temperature for more deterministic intent detection
        max_tokens=None,
    ) 
)