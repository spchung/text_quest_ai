from transitions import Machine, MachineError

class QuestMasterStateMachine:
    states = ['untrusting', 'trusting', 'helpful']

    actions = ['persuade']

    def __init__(self):
        self.machine = Machine(model=self, states=QuestMasterStateMachine.states, initial='untrusting')

        # transitions
        self.machine.add_transition(trigger='persuade', source='untrusting', dest='trusting')

    
    def next_state(self, action:str, callback:function) -> None:

        if not action in QuestMasterStateMachine.actions:
            raise MachineError(f'{action} is not a valid. Valid actions are {' '.join(QuestMasterStateMachine.actions)}')
        
        if action == 'persuade':
            self.machine.persuade()
        
        if callback:
            callback()