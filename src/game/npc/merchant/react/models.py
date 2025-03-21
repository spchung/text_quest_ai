import time
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal, TypeVar, Generic

T = TypeVar('T')

## Generics
class NameDescriptionModel(BaseModel):
    name: str
    description: str

class ApprovalWrapper(BaseModel, Generic[T]):
    data: T
    approved: bool = False

## State Machine
class StateProtectedResource(BaseModel, Generic[T]):
    allowed_states : List[str] = Field(..., description="List of states that can access this resource.")
    data: T = Field(..., description="Data that is protected by states.")

class Action(BaseModel):
    name: str
    description: str
    confirmation_required: bool = Field(default=False, description="Whether this action require explicit confirmation")

class FewShotIntent(BaseModel):
    name: str
    examples: List[str] # example text that this intent should look like
    description: str | None = Field(default=None, description="Description of the intent")
    
    def __eq__(self, other):
        if not isinstance(other, FewShotIntent):
            return False
        return self.name == other.name
    
    def __hash__(self):
        return hash(self.name)

class CharacterSetting(BaseModel):
    name: str = Field(..., description="Name of the NPC")
    physcical_description: str = Field(..., description="Description of the NPC")
    in_game_role: str = Field(..., description="Role of the NPC in the game")
    trait: str | None = Field(default=None, description="Trait of the NPC character")

class State(BaseModel):
    name: str
    character_setting: CharacterSetting
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
## CHAT HISTORY
class Message(BaseModel):
    timestamp: float = Field(default=time.time())
    role: str = Field(..., description="Who this message belongs to (NPC or player).")
    message: str = Field(..., description="Chat message")

    def __str__(self):
        return f"{self.role}: {self.message}"

class ChatHistory:
    messages: List[Message] = []

    def add_player(self, message):
        self.messages.append(Message(role='player', message=message))
    
    def add_npc(self, message):
        self.messages.append(Message(role='npc', message=message))

    def messages_to_string(self, messages:List[Message]):
        return "\n".join([str(m) for m in messages])

    def get_last_k_turns(self, k=3):
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
    npc_dialog_option: str | None = Field(default=None, description="Dialog options the NPC might consider when describing this quest.")
    reward: int = Field(..., description='Reward for completing the quest (in gold coins).')
    is_given: bool = Field(default=False, description='Whether the quest has been given to the player or not.')

class ProtectedKnowledgeBase(BaseModel):
    quests: List[Quest] = Field(..., description="List of quests that npc knows of.")
    secrets: List[NameDescriptionModel] = Field(..., description="List of secrets that will help the player during quests tha the npc knows of.")
    generic_info: List[NameDescriptionModel] = Field(..., description="Basic information the npc knows about the environments.")

class KnowledgeBase(BaseModel):
    quests: StateProtectedResource[List[Quest]] = Field(..., description="List of quests that npc knows of.")
    secrets: StateProtectedResource[List[NameDescriptionModel]] = Field(..., description="List of secrets that will help the player during quests tha the npc knows of.")
    generic_info: StateProtectedResource[List[NameDescriptionModel]] = Field(..., description="Basic information the npc knows about the environments.")

    def get_protected_knowledge(self, state: State) -> ProtectedKnowledgeBase:
        """Return a protected knowledge base for the given state"""
        quests = [q for q in self.quests.data if state.name in self.quests.allowed_states]
        secrets = [s for s in self.secrets.data if state.name in self.secrets.allowed_states]
        generic_info = [g for g in self.generic_info.data if state.name in self.generic_info.allowed_states]

        return ProtectedKnowledgeBase(quests=quests, secrets=secrets, generic_info=generic_info)
        
## ReAct Logic
class ObservationResult(BaseModel):
    condition: str | None = Field(..., description="Detected transition condition.")
    action: str | None = Field(..., description="Detected action.")
    sentiment: Literal['positive', 'negative'] | None = Field(..., description="Detected sentiment.")

class ReasonResult(BaseModel):
    information: List[str] | None = Field(..., description="List of relevant information to share with the player")
    reasoning: str | None = Field(..., description="Reasoning behind the provided information")

class PlanResult(BaseModel):
    player_message: str = Field(..., description="Player inpuyt")
    action: Action | None = Field(..., description="Action to take.")
    transition_condition: FewShotIntent | None = Field(..., description="Transition condition to check.")
    reasoning: str | None = Field(..., description="Reasoning behind the action.")

class PerformActionResult(BaseModel):
    action: Action | None = Field(..., description="Action attempted")
    is_successful: bool = Field(..., description="Whether the action was successful or not")
    reasoning: str | None = Field(..., description="Resaonsing behind the result")
    overridden_player_message: str | None = Field(default=None, description="The new player message to be used in the next step.")

class PerformTransitionConditionResult(BaseModel):
    transition_condition: FewShotIntent | None = Field(..., description="Transition condition attempted")
    is_successful: bool = Field(..., description="Whether the transition condition was successful or not")
    reasoning: str | None = Field(..., description="Resaonsing behind the result")

class TransactionResult(BaseModel):
    is_successful: bool = Field(..., description="Whether the transaction was successful or not")
    reasoning: str | None = Field(default=None, description="Reasoning behind the result")

class ActionResult(BaseModel):
    transition_condition: FewShotIntent | None = Field(..., description="Transition condition attempted")
    transition_condition_is_successful: bool = Field(..., description="Whether the transition condition was successful or not")
    action: Action | None = Field(..., description="Action attempted")
    action_is_successful: bool = Field(..., description="Whether the action was successful or not.")
    reasoning: str | None = Field(default=None, description="Reasoning for the success or failure of this action.")
    overridden_player_message: str | None = Field(default=None, description="The new player message to be used in the next step.")