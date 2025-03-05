from pydantic import BaseModel

class Inventory(BaseModel):
    def __init__(self):
        self.items = []
        self.money = 100
    
class Player:
    def __init__(self):
        self.name = 'unknown'
        self.inventory = Inventory()
        self.health = 100
        self.defense = 0
        self.attack = 10
        self.level = 1
    

    

