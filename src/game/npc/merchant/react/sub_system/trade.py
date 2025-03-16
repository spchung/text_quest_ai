"""
A trading system for player and merchant interaction
- self containing conversation loop
"""

import instructor
from pydantic import Field
from typing import List
from game.player.player import Player
from atomic_agents.agents.base_agent import AgentMemory
from game.npc.merchant.react.models import *
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm
from game.npc.merchant.react.react_merchant import ReActMerchant

class IntentMatchingInputSchema(BaseIOSchema):
    """ IntentMatchingInputSchema """
    message: str = Field(..., description="Player input message")
    available_intents: List[FewShotIntent] = Field(..., description="List of available intents")

class IntentMatchingOutputSchema(BaseIOSchema):
    """ IntentMatchingOutputSchema """
    intent: FewShotIntent = Field(..., description="Detected intent")
    confidence_score: float = Field(..., description="Confidence score for the detected intent")

intent_matching_prompt = SystemPromptGenerator(
    background=[
        'Your task is to analyze the player input message and detect their intent',
    ],
    steps=[
        'Analyze the player input message for the available intents',
        'Detect the intent of the player input message',
        'Provide a confidence score for the detected intent (0-1)'
    ],
    output_instructions=[
        'Provide the detected intent',
        'Provide a confidence score for the detected intent',
        'Only provide intents from the available intents list'
    ]
)

class ItemIdentitySystemInputSchema(BaseIOSchema):
    """ ItemIdentitySystemInputSchema """
    message: str = Field(..., description="Player input message")
    # inventory: Inventory = Field(..., description="Player inventory")
    available_items: List[Item] = Field(..., description="List of available items")

class ItemIdentitySystemOutputSchema(BaseIOSchema):
    """ ItemIdentitySystemOutputSchema"""
    item: Item | None = Field(..., description="Mentioned Item")
    confidence_score: float = Field(..., description="Confidence score for the identified item name")

item_identity_prompt = SystemPromptGenerator(
    background=[
        'Your task is to analyze the player input message and identify the item name if mentioned',
    ],
    steps=[
        'Analyze the player input message for any items in the inventory',
        'Only provide an item name if you are confident it is mentioned in the player input',
        'provide a confidence score for the identified item name (0-1)'
    ],
    output_instructions=[
        'If the item name is not mentioned, provide an empty string',
        'If the item name is mentioned, provide the item name and a confidence score',
        'You may only provide an item that is in the available_items list'
    ]
)

class TransactionResult(BaseModel):
    success: bool = Field(..., description="Transaction success status")
    intent: FewShotIntent = Field(..., description="Detected intent")
    item: Item | None = Field(..., description="Mentioned Item")
    message: str = Field(..., description="Transaction message")

## TODO:
class ResponseInputSchema(BaseIOSchema):
    """ ResponseInputSchema """
    message: str = Field(..., description="Player input message")

class ResponseOutputSchema(BaseIOSchema):
    """ ResponseOutputSchema """
    message: str = Field(..., description="NPC response message")
    

INTENTS = [
    FewShotIntent(name='buy', examples=[
        'I want to buy a sword', 
        'Can I buy a potion?',
        'I want the', 
        'Give me the',
        "I will take the",
        'I need to purchase a shield',
        'Can I get the armor?',
        'I would like to buy the dagger',
        'Do you have any potions for sale?',
        'I am looking to buy a helmet'
    ]),
    FewShotIntent(
        name='see_collection', examples=[
            'Show me your collection', 
            'What do you have?',
            'Can I see your items?',
            'What are you selling?',
            'Show me what you got',
            'Let me see your inventory',
            'What do you have in stock?',
            'Can I browse your goods?',
            'What items do you have?',
            'Show me your wares'
        ],
        description='Player wants to see the merchant inventory'
    ),
    FewShotIntent(
        name='exit', 
        examples=[
            'I am done',
            "I don't need anything else",
            "I have enough",
        ],
        description='Player wishes to stop trading.'
    ),
]


class TradeSystem:
    def __init__(self, player: Player, merchant: ReActMerchant):
        self.player = player
        self.merchant = merchant
        self.completed = False # prompt exit
        self.initiaited = False
        self.shared_memory = AgentMemory(max_messages=15)
        # identity
        self.item_identity_agent = self.__build_identiy_agent()
        self.intent_agent = self.__build_intent_agent()
    
    def __build_identiy_agent(self):
        return BaseAgent(
            BaseAgentConfig(
                client=instructor.from_openai(
                    llm
                ),
                model='gpt-4o-mini',
                memory=self.shared_memory,
                system_prompt_generator=item_identity_prompt,
                input_schema=ItemIdentitySystemInputSchema,
                output_schema=ItemIdentitySystemOutputSchema,
                temperature=0
            )
        )

    def __build_intent_agent(self):
        return BaseAgent(
            BaseAgentConfig(
                client=instructor.from_openai(
                    llm
                ),
                model='gpt-4o-mini',
                memory=self.shared_memory,
                system_prompt_generator=intent_matching_prompt,
                input_schema=IntentMatchingInputSchema,
                output_schema=IntentMatchingOutputSchema,
                temperature=0
            )
        )
    
    def __perform_action(self, intent: FewShotIntent, item: Item) -> TransactionResult:
        if intent.name == 'buy':
            if item:
                # TODO
                print(f'PLAYER WANTS TO BUY {item.name}')
            else:
                print(f'Item not found.')
        elif intent.name == 'see_collection':
            # TODO
            print("SHOWING COLLECTION\n")
            print(self.merchant.inventory.model_dump_json())
        elif intent.name == 'exit':
            self.completed = True
            print("GOODBYE")

        ## TEMP
        return TransactionResult(success=True, intent=intent, item=item, message='Transaction completed')


    def greeting(self):
        self.initiaited = True
        return "Merchant: Welcome! What can I do for you today?"

    def process_input(self, message: str):
        """
        Player Input -> Intnet Recognition -> Item Identification 
            (Yes Item) -> Action Resolution -> Dilalogue Generation -> NPC Response
            (No Item) -> Reprompt
        """

        if not self.initiaited:
            self.initiaited = True
            return "Merchant: Welcome! What can I do for you today?"
        
        if self.completed:
            return "Merchant: Goodbye!"
        
        # Intent Recognition
        intent_input = IntentMatchingInputSchema(message=message, available_intents=INTENTS)
        intent_output = self.intent_agent.run(intent_input)
        print("INTENT OUTPUT", intent_output)

        # Item Identification
        item_input = ItemIdentitySystemInputSchema(
            message=message, 
            available_items=self.merchant.inventory.items
        )
        item_output = self.item_identity_agent.run(item_input)
        print("ITEM OUTPUT", item_output)

        
        self.__perform_action(intent_output.intent, item_output.item)
        # Action Resolution
        # transaction_result = self.__perform_action(intent, item)
        # self.completed = True
