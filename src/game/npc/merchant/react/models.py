from pydantic import BaseModel, Field
from typing import List, Literal
import time

## Generics
class NameDescriptionModel(BaseModel):
    name: str
    description: str

## State Machine
class Action(BaseModel):
    name: str
    description: str

class FewShotIntent(BaseModel):
    name: str
    examples: List[str] # example text that this intent should look like
    
    def __eq__(self, other):
        if not isinstance(other, FewShotIntent):
            return False
        return self.name == other.name
    
    def __hash__(self):
        return hash(self.name)

class State(BaseModel):
    name: str
    trait: str # how the npc should act in this state
    available_actions: List[Action]

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)
    
class StateTransition(BaseModel):
    source: State
    destination: State
    conditions: List[FewShotIntent]

class NpcConfig(BaseModel):
    states: List[State]
    transitions: List[StateTransition]

## ReAct Logic
class ObservationResult(BaseModel):
    condition: str | None = Field(..., description="Detected transition condition.")
    action: str | None = Field(..., description="Detected action.")
    sentiment: str | None = Field(..., description="Detected sentiment.")


## Chat history
class Message(BaseModel):
    timestamp: float = Field(default=time.time())
    role: str = Field(..., description="Who this message belongs to (NPC or player).")
    message: str = Field(..., description="Chat message")

    def __repr__(self):
        return f"{self.role}: {self.message}"

class ChatHistory:
    messages: List[Message] = Field(..., description="list of messages")

    def add_player(self, message):
        self.messages.append(Message(role='player', message=message))
    
    def add_npc(self, message):
        self.messages.append(Message(role='npc', message=message))

    def messages_to_string(self, messages:List[Message]):
        return "\n".join([str(m) for m in messages])

    def get_last_k_turns(self, k):
        if k*2 > len(self.messages):
            return self.messages_to_string(self.messages)
        
        return self.messages_to_string(self.messages[-k*2:])
        
## GAME
class Item(BaseModel):
    name: str = Field(..., description='Name of the item')
    type: Literal['weapon', 'armour', 'potion'] = Field(..., description='Item type (weapon, armour or potion).')
    price: int = Field(..., description='Price of item in gold coins.')

class Inventory(BaseModel):
    items: List[Item] = Field(..., description="Currently held items.")
    gold: int = Field(..., description="Currently held gold coins (in-game currency).")

class Quest(BaseModel):
    name: str = Field(..., description='Name of the quest')
    description: str = Field(..., description='Description of the quest')
    reward: int = Field(..., description='Reward for completing the quest (in gold coins).')

class KnowledgeBase(BaseModel):
    quests: List[Quest] = Field(..., description="List of quests that npc knows of.")
    secrets: List[NameDescriptionModel] = Field(..., description="List of secrets that will help the player during quests tha the npc knows of.")
    generic_info: List[NameDescriptionModel] = Field(..., description="Basic information the npc knows about the environments.")
