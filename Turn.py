from hashlib import sha1
from enum import Enum

class Message:
    class Type(Enum):
        PROPOSE = 1
        OK = 2
        COUNTER = 3
        COMMIT = 4
    
    def __init__(self, sender, type, turn, signature = None):
        self.sender = sender
        self.type = type
        self.turn = turn
        self.signed = signature
    
    def ok(self, sender, signature):
        return Message(sender, Message.Type.OK, self.turn, signature)
    

class Turn:
    def __init__(self):
        self.actions: list[Action] = []
        self.OKs = {} # should be signatures

    def __init__(self, owner, actions):
        self.owner = owner
        self.actions: list[Action] = actions
        self.OKs = {} # should be signatures

    def add_ok(self, pid, ok):
        # TODO: should verify signature here
        self.OKs[pid] = ok
    
    def counter(self, action):
        return Turn(self.owner, self.actions + [action])
    
    def __hash__(self) -> int:
        return hash((self.owner, tuple(self.actions)))

# action can be nested using hashes
class Action:
    def __init__(self, owner: int, content: str):
        self.owner = owner
        self.content = content
    
    def __hash__(self):
        return hash((self.owner, self.content))

def main():
    turn = Turn(1, [])
    assert hash(turn) == hash((1, tuple([])))

    # add an action
    action = Action(2, "BLAH")

    assert hash(action) == hash((2, "BLAH"))

    new_turn = turn.counter(action)
    assert hash(new_turn) == hash((1, tuple([action])))


if __name__ == "__main__":
    main()
    print("PASS")
