from atomic_agents.agents.base_agent import BaseIOSchema
from pydantic import Field
import instructor 
import os
from dotenv import load_dotenv
from openai import OpenAI
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig 
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

load_dotenv()

API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable or in the environment variable OPENAI_API_KEY."
    )

# Your existing code
class AnswerAgentInputSchema(BaseIOSchema):
    """Input schema for the AnswerAgent."""
    question: str = Field(..., description="A question that needs to be answered based on the provided context. Also output a confidence score.",)

class AnswerAgentOutputSchema(BaseIOSchema):
    """Output schema for the AnswerAgent."""
    text_output: str = Field(..., description="The answer to the question in markdown format.")
    confidence_score: str = Field(..., description="The confidence score about your answer")

system_prompt_generator = SystemPromptGenerator(
    background=[
         "You are an intelligent answering expert.",
         "Your task is to provide accurate and detailed answers to user questions basedoon the given context."],
    steps=[
          "You will receive a question and the context information.",
          "Generate a detailed and accurate answer based on the context.",
    ],
    output_instructions=[
        "Ensure clarity and conciseness in each answer.",
        "Ensure the answer is directly relevant to the question and context provided.",
    ],
)

# Initialize the agent
answer_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(OpenAI(
            api_key=API_KEY
        )),
        model='gpt-4o-mini',
        system_prompt_generator=system_prompt_generator,
        input_schema=AnswerAgentInputSchema,
        output_schema=AnswerAgentOutputSchema,
        memory=None,
        temperature=0,
        max_tokens=None,
    ) 
)