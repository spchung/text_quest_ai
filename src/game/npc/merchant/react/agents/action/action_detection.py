import instructor
from pydantic import Field
from typing import List
from game.npc.merchant.react.models import *
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm

class ActionDetectionInputSchema(BaseIOSchema):
    """Input Schema for Action Detection"""
    previous_conversation: str = Field(..., description="Chat history between user and NPC")
    player_message: str = Field(..., description="The message from the player to the NPC")
    current_state: State = Field(..., description="Current state of the NPC")

class ActionDetectionOutputSchema(BaseIOSchema):
    """Output Schema for Action Detection"""
    detected_action: str = Field(..., description="Most likely action detected in the player's message")
    confidence_score: float = Field(..., description="Confidence score of the detected result (from 0.0 - 1.0)")

action_detection_prompt = SystemPromptGenerator(
    background=[
        "Your job is to interpurt the user's message and determine if any action is an appropriate reponse.",
        "You may only choose one action from actions available to this state.",
        "You have access to a description of each action"
    ],
    steps=[
        "Carefully analyze the player's message in the context of the previous conversation.",
        "Compare it to each action and action description of the current state.",
        "Determine if any of the available action is an appropriate response to the user's message."
    ],
    output_instructions=[
        "Only choose an action if it is an appropriate response to the user's message.",
        "Assign reasonable confidence scores (0.0 to 1.0) based on how relative the message is to the selected action.",
    ]
)

action_detection_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(
            llm
        ),
        model='gpt-4o-mini',
        system_prompt_generator=action_detection_prompt,
        input_schema=ActionDetectionInputSchema,
        output_schema=ActionDetectionOutputSchema,
        memory=None,
        temperature=0,  # Low temperature for more deterministic intent detection
        max_tokens=None,
    ) 
)