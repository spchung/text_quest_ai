import os
import instructor
from pydantic import Field
from typing import List, Optional
from game.npc.merchant.react.models import *
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from openai import OpenAI
from game.logging.logfire_logger import logfire

API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable or in the environment variable OPENAI_API_KEY."
    )


class IntentDetectionInputSchema(BaseIOSchema):
    """Input schema for the Intent Detection Agent."""
    player_message: str = Field(..., description="The message from the player to the NPC")
    current_state: State = Field(..., description="Current state of the NPC")
    available_transition_conditions: List[FewShotIntent] = Field(..., description="List of available state transition conditions")

class DetectedIntent(BaseModel):
    """A detected intent with confidence score"""
    intent_name: str = Field(..., description="Name of the detected intent")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    matching_example: str = Field(..., description="The example from few-shot that best matches")

class IntentDetectionOutputSchema(BaseIOSchema):
    """Output schema for the Intent Detection Agent."""
    detected_conditions: str = Field(..., description="Most likely transition condition detected in the player's message")
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
        "Determine if any detected intents should trigger a state transition.",
        "Provide reasoning for your decisions."
    ],
    output_instructions=[
        "Only detect intents that are truly present in the player's message.",
        "Be specific about which few-shot example most closely matches the player's message.",
        "Assign reasonable confidence scores (0.0 to 1.0) based on how closely the message matches the examples.",
    ],
)
llm = OpenAI(api_key=API_KEY)

logfire.instrument_openai(llm)

transition_detection_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(
            llm
        ),
        model='gpt-4o-mini',
        system_prompt_generator=intent_detection_prompt,
        input_schema=IntentDetectionInputSchema,
        output_schema=IntentDetectionOutputSchema,
        memory=None,
        temperature=0,  # Low temperature for more deterministic intent detection
        max_tokens=None,
    ) 
)