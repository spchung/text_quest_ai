from pydantic import BaseModel
from enum import Enum

class ActionType(Enum):
    ATTACK = 1
    DEFEND = 2
    USE_ITEM = 3