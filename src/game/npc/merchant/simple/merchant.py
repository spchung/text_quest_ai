from game.items.items import Weapon, Armour, Inventory, HealthPotion, PotionEffectEnum
from game.npc.npc_memory import NPCMemory, ChatRoleEnum
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from typing import Literal
from game.player.simple.player import Player
from .prompts import NPC_PROMPTS

load_dotenv()

merchant_prompts = NPC_PROMPTS['merchant']

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

class IdentifyItem(BaseModel):
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
        router_prompt = merchant_prompts.get('route_discovery')

        # Output parser for routing
        router_parser = PydanticOutputParser(pydantic_object=RouteClassification)

        # Router LLM
        router_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

        # Routing chain
        router_chain = router_prompt | router_llm | router_parser

        return router_chain
    
    def create_route_chains(self):
        return {
            "trade": merchant_prompts.get('trade_route'),
            "transaction": merchant_prompts.get('transaction_route'),
            "ask_information": merchant_prompts.get('ask_information_route'),
            "default": merchant_prompts.get('default_route')
        }
    
    def route_chain(self, router_result):
        routes = self.create_route_chains()
        dest = router_result.destination
        
        # get the prompt for the destination
        prompt = routes.get(dest, routes.get('default'))

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
            # print(parsed_result.actions)
            if 'sell_item' in parsed_result.actions:
                # print("Handle Sell Item")
                
                sell_attempt_response = self.handle_sell_item(player_input, player)

                self.memory.add_chat_history(role=ChatRoleEnum.PLAYER, text=player_input)
                self.memory.add_chat_history(role=ChatRoleEnum.NPC, text=sell_attempt_response)
                
                return sell_attempt_response
            
            elif 'buy_item' in parsed_result.actions:
                # print("Handle Buy Item")

                sell_attempt_response = self.handle_buy_item(player_input, player)

                self.memory.add_chat_history(role=ChatRoleEnum.PLAYER, text=player_input)
                self.memory.add_chat_history(role=ChatRoleEnum.NPC, text=sell_attempt_response)
                
                return sell_attempt_response
    
        ## Update memory
        self.memory.add_chat_history(role=ChatRoleEnum.PLAYER, text=player_input)
        self.memory.add_chat_history(role=ChatRoleEnum.NPC, text=parsed_result.response_text)

        return parsed_result.response_text
    
    def handle_buy_item(self, player_input: str, player: Player):
        # extract item for sale
        prompt = merchant_prompts.get('extract_buy_item')

        parser = PydanticOutputParser(pydantic_object=IdentifyItem)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        chain = prompt | llm | parser

        result = chain.invoke({
            "player_input": player_input,
            "player_inventory": player.inventory.items_to_context(),
            "format_instructions": parser.get_format_instructions()
        })

        # get item id
        item_id = result.item_id

        # find item
        item = player.inventory.items.get(item_id, None)
        if not item:
            prompt = merchant_prompts.get('buy_item_not_found')

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
            chain = prompt | llm

            response = chain.invoke({
                "npc_name": self.context['name'],
                "npc_traits": self.context['traits'],
                "player_inventory": player.inventory.items_to_context(),
                "player_input": player_input
            })
            return response.content
        
        # 1. get item
        item = player.inventory.items[item_id]

        # 2. check if npc has enough gold
        if self.inventory.gold < item.price:
            prompt = merchant_prompts.get('merchant_insufficient_gold')
            
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

            chain = prompt | llm

            response = chain.invoke({
                "npc_name": self.context['name'],
                "npc_traits": self.context['traits'],
                "npc_gold": self.inventory.gold,
                "item_price": item.price
            })

            return response.content

        # 3. deduct gold from self
        self.inventory.gold -= item.price

        # 4. add gold to player
        player.inventory.gold += item.price

        # 4. add item to self inventory
        self.inventory.items[item_id] = item

        # 5. remove item from player inventory
        del player.inventory.items[item_id]

        prompt = merchant_prompts.get('buy_successful')

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        chain = prompt | llm

        response = chain.invoke({
            "npc_name": self.context['name'],
            "npc_traits": self.context['traits'],
            "item_name": item.name
        })

        return response.content

    def handle_sell_item(self, player_input: str, player: Player):
        # extract item for sale
        prompt = merchant_prompts.get('extract_sell_item')

        parser = PydanticOutputParser(pydantic_object=IdentifyItem)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        chain = prompt | llm | parser

        result = chain.invoke({
            "player_input": player_input,
            "npc_inventory": self.inventory.items_to_context(),
            "format_instructions": parser.get_format_instructions()
        })

        # get item id
        item_id = result.item_id

        # find item
        item = self.inventory.items.get(item_id, None)
        if not item:
            prompt = merchant_prompts.get('sell_item_not_found')

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

            chain = prompt | llm

            response = chain.invoke({
                "npc_name": self.context['name'],
                "npc_traits": self.context['traits'],
                "player_input": player_input,
                "npc_inventory": self.inventory.items_to_context()
            })
            return response.content
        
        # 1. get item
        item = self.inventory.items[item_id]

        # 2. check if player has enough gold
        if player.inventory.gold < item.price:
            prompt = merchant_prompts.get('player_insufficient_gold')
            
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

            chain = prompt | llm

            response = chain.invoke({
                "npc_name": self.context['name'],
                "npc_traits": self.context['traits'],
                "player_gold": player.inventory.gold,
                "item_price": item.price
            })

            return response.content
        
        # 3. deduct gold from player
        player.inventory.gold -= item.price

        # 4. add item to player inventory
        player.inventory.items[item_id] = item

        # 5. remove item from npc inventory
        del self.inventory.items[item_id]

        # 6. return success message
        prompt = merchant_prompts.get('sale_successful')

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        chain = prompt | llm

        response = chain.invoke({
            "npc_name": self.context['name'],
            "npc_traits": self.context['traits'],
            "item_name": item.name
        })

        return response.content