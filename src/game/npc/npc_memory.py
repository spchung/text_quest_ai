'''
self.momory = {
    'player_name': None,
    'chat_history': [],
    'items_sold': [],
    'quest_offered': []
}
'''
from typing import List
from pydantic import BaseModel
from enum import Enum

class ChatRoleEnum(Enum):
    PLAYER = "player"
    NPC = "npc"

class ChatHistory(BaseModel):
    role: ChatRoleEnum
    text: str
    idx: int

class NPCMemory(BaseModel):
    curr_index: int = 0
    player_name: str = None
    chat_history: List[ChatHistory] = []

    def add_chat_history(self, role: ChatRoleEnum, text: str):
        self.chat_history.append(ChatHistory(role=role, text=text, idx=self.curr_index))
        self.curr_index += 1
    
    def to_context(self, turn_limit=2):
        res = ''
        for chat in self.chat_history[-turn_limit*2:]:
            res += f"{chat.role.value}: {chat.text}\n"
        return res