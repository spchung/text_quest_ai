from pydantic import BaseModel
from game.items.items import Inventory, Item
    
class Player:
    def __init__(self):
        self.name = 'unknown'
        self.inventory = Inventory(gold=100)
        self.health = 100
        self.level = 1
    
    def set_name(self, name):
        self.name = name

    def deduct_gold(self, amount):
        if self.inventory.gold < amount:
            return False
        self.inventory.gold -= amount
    
    def add_gold(self, amount):
        self.inventory.gold += amount
    
    def add_item(self, item: Item):
        self.inventory.items[item.name] = item