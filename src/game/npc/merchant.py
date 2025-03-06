from game.items.items import Weapon, Armour, Inventory, HealthPotion, PotionEffectEnum
from game.npc.npc_memory import NPCMemory, ChatRoleEnum
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from typing import Literal
from game.player.player import Player

load_dotenv()

class NPCResponse(BaseModel):
    actions: List[str] = Field(description="List of actions to perform, if any")
    response_text: str = Field(description="Response text to send to the user")
    confidence: float = Field(description="Confidence in this response (0-1)")


class RouteClassification(BaseModel):
    destination: Literal["trade", "transaction", "ask_information", "default"] = Field(
        description="Determine the appropriate route for handling the player's input"
    )
    reasoning: str = Field(
        description="Brief explanation of why this route was chosen"
    )

class IdentifySellingItem(BaseModel):
    item_id: str = Field(
        description="The if of the item that is being sold"
    )

class Merchant:
    def __init__(self):
        self.inventory = self.init_inventory()
        self.llm = ChatOpenAI()

        self.memory = NPCMemory()

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
                5. item_unavailable
                """
        }
    
    def init_inventory(self):
        return Inventory(
            items={
                'sword': Weapon(name='Sword', damage=10, price=10),
                'shield': Armour(name='Shield', defense=5, price=25),
                'potion': HealthPotion(name='Potion', points=10, effect=PotionEffectEnum.HEAL, price=5)
            },
            gold=1523
        )

    def create_router_chain(self):
        router_prompt = ChatPromptTemplate.from_template("""
        Analyze the player's input and previous context to determine the most appropriate interaction route:

        Possible routes:
        - trade: When the player wants to browse items, see what's available, ask about prices, or discuss merchandise but is NOT yet committing to a specific purchase
        - transaction: When the player is EXPLICITLY trying to buy or sell a SPECIFIC item (e.g., "I'll buy the sword" or "I want to purchase the potion")
        - ask_information: When the player is asking for information unrelated to merchandise
        - default: General conversation or greetings

        Examples:
        - "What do you sell?" → trade
        - "Do you have any weapons?" → trade
        - "How much is the potion?" → trade
        - "I want to see your items" → trade
        - "I'll take the sword" → transaction
        - "I want to buy the health potion" → transaction
        - "I'll sell you this dagger" → transaction
        - "Tell me about this area" → ask_information
        - "What's the best way to defeat the dragon?" → ask_information
        - "Hello!" → default
        - "Good day!" → default

        Previous conversation:
        {conversation_history}

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
                2. Only offer to sell items that are in your inventory
                3. You are allowed to buy any item from the player
                4. Only suggests actions from your allowed list if appropriate
                
                Respond in the following JSON format:
                {format_instructions}
                """),

            "transaction": ChatPromptTemplate.from_template("""
                You are an NPC named {npc_name} with the following traits: {npc_traits}.
                
                Your role is: {npc_role}
                                                            
                You are now handling a transaction interaction with the player.
                
                Your inventory:
                {npc_inventory}

                Player inventory item:
                {player_inventory}
                
                Previous conversation:
                {conversation_history}
                                                        
                ACTIONS YOU ARE ALLOWED TO PERFORM:
                {allowed_actions}
                
                Player says: {player_input}
                
                First, understand the player's transaction request. Then generate a response that:
                1. Stays in character based on your personality
                2. Only completes transactions for items that exist in the relevant inventory
                3. Includes the appropriate action in the actions list
                
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
    
    def process_input(self, player_input: str, player: Player):
        router_chain = self.create_router_chain()
        router_parser = PydanticOutputParser(pydantic_object=RouteClassification)
        router_result = router_chain.invoke(
            {
                "player_input": player_input,
                "format_instructions": router_parser.get_format_instructions(),
                "conversation_history": self.memory.to_context(),
            }
        )

        # get the route chain
        intent_dest = router_result.destination
        routed_chain = self.route_chain(router_result)
        routed_chain_parser = PydanticOutputParser(pydantic_object=NPCResponse)

        # See intent destination
        print("Intent: ",intent_dest)

        # # See history
        # print("=========")
        # print(self.memory.to_context())
        # print("=========")
        
        # run the routed chain
        routed_result = routed_chain.invoke(
            {
                "player_input": player_input,
                "npc_name": self.context['name'],
                "npc_role": self.context['role'],
                "npc_traits": self.context['traits'],
                "npc_inventory": self.inventory.items_to_context(),
                "player_inventory": player.inventory.items_to_context(),
                "npc_money": self.inventory.gold,
                "player_money": player.inventory.gold,
                "conversation_history": self.memory.to_context(),
                "allowed_actions": self.context['allowed_actions'],
                "format_instructions": routed_chain_parser.get_format_instructions()
            }
        )
        
        parsed_result = routed_chain_parser.invoke(routed_result)

        # handle actions
        if intent_dest == 'transaction':
            print(parsed_result.actions)
            if 'sell_item' in parsed_result.actions:
                ## TODO: add new chain to handle selling of items
                print("Handle Sell Item")
                
                sell_attempt_response =self.handle_sell_item(player_input, player)

                self.memory.add_chat_history(role=ChatRoleEnum.PLAYER, text=player_input)
                self.memory.add_chat_history(role=ChatRoleEnum.NPC, text=sell_attempt_response)
                
                return sell_attempt_response
            elif 'buy_item' in parsed_result.actions:
                ## TODO: add new chain to handle buying of items
                print("Handle Buy Item")


    
        ## Update memory
        self.memory.add_chat_history(role=ChatRoleEnum.PLAYER, text=player_input)
        self.memory.add_chat_history(role=ChatRoleEnum.NPC, text=parsed_result.response_text)

        return parsed_result.response_text

    def handle_sell_item(self, player_input: str, player: Player):
        # extract item for sale
        prompt = ChatPromptTemplate.from_template("""
        Analyze the player's input and extract the item they are referring to:
                                                  
        Inventory items:
        {npc_inventory}
        
        Player says: {player_input}
                                                  
        Provide your selection in the following format:
        {format_instructions}
        """)

        parser = PydanticOutputParser(pydantic_object=IdentifySellingItem)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        chain = prompt | llm | parser

        result = chain.invoke(
            {
                "player_input": player_input,
                "npc_inventory": self.inventory.items_to_context(),
                "format_instructions": parser.get_format_instructions()
            }
        )

        # get item id
        item_id = result.item_id

        # find item
        item = self.inventory.items.get(item_id, None)
        if not item:
            prompt = ChatPromptTemplate.from_template("""
            You are an NPC named {npc_name} with the following traits: {npc_traits}.
                                                      
            The player mentioned an item that is not in your inventory.
            
            Please ask the player to specify an item in your inventory.
                                                    
            Inventory items:
            {npc_inventory}
            
            Player says: {player_input}
                                                      
            Provide a response reiterating your available items.
            """)

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

            chain = prompt | llm

            response = chain.invoke(
                {
                    "npc_name": self.context['name'],
                    "npc_traits": self.context['traits'],
                    "player_input": player_input,
                    "npc_inventory": self.inventory.items_to_context()
                }
            )
            return response.content
        
        else:
            # 1. get item
            item = self.inventory.items[item_id]

            # 2. check if player has enough gold
            if player.inventory.gold < item.price:
                prompt = ChatPromptTemplate.from_template("""
                    You are an NPC named {npc_name} with the following traits: {npc_traits}.
                                                          
                    Player does not have enough gold to purchase the item.

                    Player gold: {player_gold}
                    Item price: {item_price}

                    Explain to the player that they do not have enough gold to purchase the item.  
                    """)
                
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

                chain = prompt | llm

                response = chain.invoke(
                    {
                        "npc_name": self.context['name'],
                        "npc_traits": self.context['traits'],
                        "player_gold": player.inventory.gold,
                        "item_price": item.price
                    }
                )

                return response.content
            
            # 3. deduct gold from player
            player.inventory.gold -= item.price

            # 4. add item to player inventory
            player.inventory.items[item_id] = item

            # 5. remove item from npc inventory
            del self.inventory.items[item_id]

            # 6. return success message
            prompt = ChatPromptTemplate.from_template("""
                You are an NPC named {npc_name} with the following traits: {npc_traits}.
                                                        
                Player has successfully purchased the item.
                
                Item name: {item_name}

                Ask the player if they need anything else.
                """)

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

            chain = prompt | llm

            response = chain.invoke(
                {
                    "npc_name": self.context['name'],
                    "npc_traits": self.context['traits'],
                    "item_name": item.name
                }
            )

            return response.content