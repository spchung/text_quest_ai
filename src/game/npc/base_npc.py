from abc import ABC, abstractmethod

'''
BaseNPC is an abstract class that all NPCs should inherit from.
'''

class BaseNPC(ABC):
    
    @abstractmethod
    def greeting(self):
        pass

    @abstractmethod
    def farewell(self):
        pass