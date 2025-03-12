from pydantic import BaseModel
from typing import List

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

class StateTransition(BaseModel):
    source: State
    destination: State
    conditions: List[FewShotIntent]

class NpcConfig(BaseModel):
    states: List[State]
    transitions: List[StateTransition]
