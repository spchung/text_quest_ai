from enum import Enum

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

class Item:
    def __init__(self, type:ItemTypeEnum, rarity:ItemRarityEnum):
        self.type = type
        self.rarity = rarity

class Weapon(Item):
    def __init__(self, name:str, damage:int):
        super().__init__(ItemTypeEnum.WEAPON, name)
        self.damage = damage

class Armour(Item):
    def __init__(self, name:str, defense:int):
        super().__init__(ItemTypeEnum.ARMOR, name)
        self.defense = defense

class Potion(Item):
    def __init__(self, name:str, effect: PotionEffectEnum):
        super().__init__(ItemTypeEnum.POTION, name)
        self.effect = effect

class HealthPotion(Potion):
    def __init__(self, name:str, points:int):
        super().__init__(name, PotionEffectEnum.HEAL)
        self.points = points

class DefensePotion(Potion):
    def __init__(self, name:str, points:int):
        super().__init__(name, PotionEffectEnum.DEFENSE)
        self.points = points
