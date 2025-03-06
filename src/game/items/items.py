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

class Inventory(BaseModel):
    items: Dict[str, Item] = {}
    gold: int

    def items_to_context(self):
        res = ''
        for _, item in self.items.items():
            if isinstance(item, Weapon):
                res += f"Weapon: {item.name} - Damage: {item.damage}\n"
            elif isinstance(item, Armour):
                res += f"Armour: {item.name} - Defense: {item.defense}\n"
            elif isinstance(item, Potion):
                res += f"Potion: {item.name} - Effect: {item.effect} Points: {item.points}\n"
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
