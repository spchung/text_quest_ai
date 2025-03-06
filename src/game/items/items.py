from enum import Enum
from typing import Dict
from pydantic import BaseModel

class ItemTypeEnum(Enum):
    WEAPON = 1
    ARMOR = 2
    POTION = 3

class ItemRarityEnum(Enum):
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    LEGENDARY = 5

class PotionEffectEnum(Enum):
    HEAL = 1
    DEFENSE = 2

class Item(BaseModel):
    type: ItemTypeEnum
    name: str
    price: int

class Inventory(BaseModel):
    items: Dict[str, Item] = {}
    gold: int

    def items_to_context(self):
        res = ''
        for key, item in self.items.items():
            if isinstance(item, Weapon):
                res += f"id: {key} Weapon: {item.name} - Damage: {item.damage} Price: {item.price}\n"
            elif isinstance(item, Armour):
                res += f"id: {key} Armour: {item.name} - Defense: {item.defense} Price: {item.price}\n"
            elif isinstance(item, Potion):
                res += f"id: {key} Potion: {item.name} - Effect: {item.effect} Points: {item.points} Price: {item.price}\n"
            else:
                res += "unknown item \n"
        return res

class Weapon(Item):
    type: ItemTypeEnum = ItemTypeEnum.WEAPON
    damage: int

class Armour(Item):
    type: ItemTypeEnum = ItemTypeEnum.ARMOR
    defense: int

class Potion(Item):
    type: ItemTypeEnum = ItemTypeEnum.POTION
    effect: PotionEffectEnum

class HealthPotion(Potion):
    points: int

class DefensePotion(Potion):
    points: int
