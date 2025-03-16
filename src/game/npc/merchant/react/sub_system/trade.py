"""
A trading system for player and merchant interaction
- self containing conversation loop
"""

import instructor
from pydantic import Field
from typing import List, Any
from atomic_agents.agents.base_agent import AgentMemory
from game.npc.merchant.react.models import *
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from game.npc.merchant.react.llm_client import llm

## Intent Recognition
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

## Item Identification
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

## Transaction Result
class TransactionResult(BaseModel):
    success: bool = Field(..., description="Transaction success status")
    item_name: str | None = Field(default=None, description="Item name")
    reasoning: str | None = Field(default=None, description="Transaction message")

## Instructed Feedback
class InstructedFeedbackInputSchema(BaseIOSchema):
    """ InstructedFeedbackInputSchema """
    message: str = Field(..., description="Player input message")
    npc_traits: str | None = Field(default=None, description="NPC character traits")
    instruction: str | None = Field(default=None, description="Instructions the llm should follow.")
    context: Any | None = Field(default=None, description="Contextual information for the feedback")

class InstructedFeedbackOutputSchema(BaseIOSchema):
    """ InstructedFeedbackOutputSchema """
    message: str = Field(..., description="NPC response message")

instructed_feednack_prompt = SystemPromptGenerator(
    background=[
        'You are an merchant NPC in a role-playing game with a specific traits',
        'You are already mid-conversation with the player, do not break the immersion',
        'Your task is to provide feedback based on the instruction and context provided',
    ],
    steps=[
        'Analyze the player input message and the context provided',
        'Follow the instruction provided and generate a response based on the context that is engaging and consistent with your character traits',
    ],
    output_instructions=[
        'Provide a response based on the instruction and context provided',
        'Ensure the response is engaging and consistent with the character traits of the merchant NPC',
        'Do not break the immersion of the conversation',
        'You are mid-conversation with the player, do not greet them under any circumstances'
    ]
)

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
    def __init__(self, player_inventory: Inventory, merchant_inventory: Inventory, merchant_trait:str):
        self.player_inventory = player_inventory
        self.merchant_inventory = merchant_inventory
        self.completed = False # prompt exit
        self.initiaited = False
        self.shared_memory = AgentMemory(max_messages=15)
        
        # NPC traits
        self.merchant_trait = merchant_trait
        
        # agents
        self.item_identity_agent = self.__build_identiy_agent()
        self.intent_agent = self.__build_intent_agent()
        self.respone_agent = self.__build_response_agent()
    
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
    
    def __build_response_agent(self):
        return BaseAgent(
            BaseAgentConfig(
                client=instructor.from_openai(
                    llm
                ),
                model='gpt-4o-mini',
                memory=self.shared_memory,
                system_prompt_generator=instructed_feednack_prompt,
                input_schema=InstructedFeedbackInputSchema,
                output_schema=InstructedFeedbackOutputSchema,
                temperature=0
            )
        )

    def __perform_transaction(self, intent: FewShotIntent, item: Item) -> TransactionResult:
        trade_action_res = TransactionResult(success=False, reasoning="Transaction failed")
        
        if intent.name not in ['buy']:
            trade_action_res.reasoning = f"Invalud transaction intent - can only buy"
            return trade_action_res

        if not item or not (item in self.merchant_inventory.items):
            trade_action_res.reasoning = f"Item not found in the inventory"
            return trade_action_res
            
        if self.player_inventory.gold < item.price:
            trade_action_res.success = False
            trade_action_res.item_name = item.name
            trade_action_res.reasoning = f"Transaction unsuccessful. Player does not have enough gold to buy {item.name}"
            return trade_action_res
        
        # deduct gold from player
        self.player_inventory.gold -= item.price
        # add item to player inventory
        self.player_inventory.items.append(item)
        # remove item from merchant inventory
        self.merchant_inventory.items.remove(item)
        # add gold to merchant
        self.merchant_inventory.gold += item.price

        trade_action_res.success = True
        trade_action_res.item_name = item.name
        trade_action_res.reasoning = f"Transaction successful. Player bought {item.name} for {item.price} gold coins"
        return trade_action_res

    def greeting(self):
        self.initiaited = True
        return "What are you looking for today?"

    def process_input(self, message: str) -> str:
        """
        Player Input -> Intnet Recognition -> Item Identification 
            (Yes Item) -> Action Resolution -> Dilalogue Generation -> NPC Response
            (No Item) -> Reprompt
        """

        if not self.initiaited:
            self.greeting()
        
        if self.completed:
            return "Merchant: Goodbye!"
        
        # Intent Recognition
        intent_input = IntentMatchingInputSchema(message=message, available_intents=INTENTS)
        intent_output = self.intent_agent.run(intent_input)

        if intent_output.confidence_score < 0.5:
            instucted_feefback_input = InstructedFeedbackInputSchema(
                message=message,
                npc_traits=self.merchant_trait,
                instruction="""
                    Ask the player to repeat their message or provide a different message.
                    Mention to the player that they can either buy an item or see the merchant's collection.
                """
            )
            
            response_output = self.respone_agent.run(instucted_feefback_input)
            return response_output.message

        ## filter by intent
        if intent_output.intent.name == 'exit':
            self.completed = True
            return "Good doing business with you."
        
        instucted_feefback_input = InstructedFeedbackInputSchema(
            message=message,
            npc_traits=self.merchant_trait,
        )

        # non-traction intets
        if intent_output.intent.name == 'see_collection':
            # instructed feedback
            instucted_feefback_input.instruction = """
                The player requested to see the merchant's collection. 
                Use the provided inventory items in the context to generate a response.
            """

            instucted_feefback_input.context = self.merchant_inventory.items
        
        # transaction intent
        else:
            # Item Identification
            item_input = ItemIdentitySystemInputSchema(
                message=message, 
                available_items=self.merchant_inventory.items
            )
            item_output = self.item_identity_agent.run(item_input)

            # provide instruction for response
            instucted_feefback_input.instruction = """
                You just performed a transaction. 
                Check the transaction result and provide feedback to the player.
                Prompt the user to either make another purchase or stop trading
            """

            # perform transaction
            transaction_res = self.__perform_transaction(intent_output.intent, item_output.item)
            # LOG EVENT
            print("[EVENT] Transaction: ", transaction_res.reasoning)
            if transaction_res.success:
                instucted_feefback_input.context = transaction_res
            else:
                instucted_feefback_input.context = transaction_res
        
        # provide response
        response_output = self.respone_agent.run(instucted_feefback_input)
        return response_output.message