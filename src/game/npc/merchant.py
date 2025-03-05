from game.items.items import Weapon, Armour, Potion
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from typing import Literal

load_dotenv()

class NPCResponse(BaseModel):
    actions: List[str] = Field(description="List of actions to perform, if any")
    response_text: str = Field(description="Response text to send to the user")
    confidence: float = Field(description="Confidence in this response (0-1)")


class RouteClassification(BaseModel):
    destination: Literal["trade", "ask_information", "default"] = Field(
        description="Determine the appropriate route for handling the player's input"
    )
    reasoning: str = Field(
        description="Brief explanation of why this route was chosen"
    )

class Merchant:
    def __init__(self):
        self.money = 1000
        self.inventory = self._initInventory()
        self.llm = ChatOpenAI()

        self.momory = {
            'player_name': None,
            'chat_history': [],
            'items_sold': [],
            'quest_offered': []
        }

        self.personality = {
            "knowledge": ["local_area", 'town_history', 'trade'],
            "traits": ["friendly", "helpful", "knowledgeable"]
        }

        self.dialogue_status = {
            'GREETING': [
                'Hello, traveler! How can I help you today?',
            ]
        }

        self.quests = {
            "defeat_dragon": {
                "name": "Defeat the Dragon",
                "description": "A dragon has been terrorizing the town. Be a hero and defeat it!",
            },
        }

        self.context = {
            'name': 'Magnus the Merchant',
            'role': 'Merchant',
            'traits': 'Friendly, helpful, knowledgeable',
            'rules': """
                1. Never reveals information about dungeon locations
                2. Cannot discuss political matters
                3. Must maintain polite tone regardless of player actions
                """,
            'allowed_actions': """
                1. sell_item
                2. buy_item
                3. offer_quest
                4. provide_information
                """
        }
    
    def _initInventory(self):
        self.inventory = {
            'sword': Weapon('Sword', 10),
            'shield': Armour('Shield', 5),
            'potion': Potion('Health Potion', 10)
        }

    def process_input(self, player_input, conversation_history):
        # 1. Set up the prompt template with NPC context and rules
        prompt = ChatPromptTemplate.from_template("""
        You are an NPC named {npc_name} with the following traits: {npc_traits}.
        
        Your role is: {npc_role}
        
        YOU MAY ONLY INTERPRET PLAYER INPUTS AS THE FOLLOWING INTENTS:
        
        RULES YOU MUST FOLLOW:
        {npc_rules}
        
        ACTIONS YOU ARE ALLOWED TO PERFORM:
        {allowed_actions}
        
        Previous conversation:
        {conversation_history}
        
        Player says: {player_input}
        
        First, classify the player's intent. Then generate a response that:
        1. Stays in character based on your personality
        2. Follows all your defined rules
        3. Only suggests actions from your allowed list if appropriate
        
        Respond in the following JSON format:
        {format_instructions}
        """)

        # 2. parser
        parser = PydanticOutputParser(pydantic_object=NPCResponse)
        
        # 3. Initialize the LLM
        llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0.7)
        
        # 4. Create and run the chain
        chain = prompt | llm | parser
        
        # 5. Run the chain with appropriate inputs
        result = chain.invoke(
            {
                "npc_name": self.context['name'],
                "npc_role": self.context['role'],
                "npc_traits": self.context['traits'],
                "npc_rules": self.context['rules'],
                "allowed_actions": self.context['allowed_actions'],
                "conversation_history": conversation_history,
                "player_input": player_input,
                "format_instructions": parser.get_format_instructions()
            }
        )
        
        # # 6. Process actions if needed
        # if result.actions:
        #     print(f"Actions to perform: {result.actions}")
        
        # # 7. Store in conversation history
        # conversation_history.append({
        #     "player": player_input,
        #     "npc": result.response_text
        # })
        
        return result
    
    def create_router_chain(self, player_input):

        router_prompt = ChatPromptTemplate.from_template("""
        Analyze the player's input and determine the most appropriate interaction route:

        Possible routes:
        - trade
        - ask_information
        - default
                                                         
        Player says: {player_input}
                                                         
        Provide your classification in the following format:
        {format_instructions}                   
        """)

        # Output parser for routing
        router_parser = PydanticOutputParser(pydantic_object=RouteClassification)

        # Router LLM
        router_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

        # Routing chain
        router_chain = router_prompt | router_llm | router_parser
        # router_chain = router_prompt | router_llm

        return router_chain
    
    def create_route_chains(self):
        return {
            "trade": ChatPromptTemplate.from_template("""
                You are an NPC named {npc_name} with the following traits: {npc_traits}.
                
                Your role is: {npc_role}
                                                      
                You are now handling a trade interaction with the player.
                
                Your inventory:
                {npc_inventory}

                Previous conversation:
                {conversation_history}
                                                      
                ACTIONS YOU ARE ALLOWED TO PERFORM:
                {allowed_actions}
                
                Player says: {player_input}
                
                First, understand the player's request. Then generate a response that:
                1. Stays in character based on your personality
                2. Only offer items that are in your inventory
                3. Only suggests actions from your allowed list if appropriate
                
                Respond in the following JSON format:
                {format_instructions}
                """),

            "ask_information": ChatPromptTemplate.from_template("""
                You are an NPC named {npc_name} with the following traits: {npc_traits}.
                
                Your role is: {npc_role}
                                                                
                You are now handling a information request interaction with the player.
                
                Previous conversation:
                {conversation_history}
                                                      
                ACTIONS YOU ARE ALLOWED TO PERFORM:
                {allowed_actions}
                                                                
                Player says: {player_input}
                                                                
                First, understand the player's request. Then generate a response that:
                1. Stays in character based on your personality
                2. Only suggests actions from your allowed list if appropriate
                                                                
                Respond in the following JSON format:
                {format_instructions}
                """),

            "default": ChatPromptTemplate.from_template("""
                You are an NPC named {npc_name} with the following traits: {npc_traits}.
                
                Your role is: {npc_role}
                                                                
                You are now handling a general interaction with the player.
                
                Previous conversation:
                {conversation_history}
                                                      
                ACTIONS YOU ARE ALLOWED TO PERFORM:
                {allowed_actions}
                                                                
                Player says: {player_input}
                                                                
                First, understand the player's request. Then generate a response that:
                1. Stays in character based on your personality
                2. Only suggests actions from your allowed list if appropriate
                                                                
                Respond in the following JSON format:
                {format_instructions}
                """)
        }
    
    def route_chain(self, router_result):
        routes = self.create_route_chains()
        dest = router_result.destination
        prompt = routes.get(dest, routes['default'])

        # Create the response chain
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response_chain = prompt | llm

        return response_chain
    
    def create_full_chain(self, player_input, conversation_history):
        router_chain = self.create_router_chain(player_input)
        
        full_chain = (
            RunnablePassthrough.assign(
                route=router_chain,
            ) | RunnableLambda(lambda x: self.route_chain(x['route']).invoke(x))
        )

        return full_chain
    
    def process_full_chain(self, player_input, conversation_history):
        router_chain = self.create_router_chain(player_input)
        
        router_parser = PydanticOutputParser(pydantic_object=RouteClassification)
        
        router_result = router_chain.invoke(
            {
                "player_input": player_input,
                "format_instructions": router_parser.get_format_instructions()
            }
        )

        # get the route chain
        routed_chain = self.route_chain(router_result)
        routed_chain_parser = PydanticOutputParser(pydantic_object=NPCResponse)
        # run the route chain
        router_result = routed_chain.invoke(
            {
                "player_input": player_input,
                "npc_name": self.context['name'],
                "npc_role": self.context['role'],
                "npc_traits": self.context['traits'],
                "npc_inventory": "Knife, Shield, Health Potion",
                "conversation_history": conversation_history,
                "allowed_actions": self.context['allowed_actions'],
                "format_instructions": routed_chain_parser.get_format_instructions()
            }
        )

        return router_result


