from hashlib import sha1
from enum import Enum

class Message:
    class Type(Enum):
        PROPOSE = 1
        OK = 2
        COUNTER = 3
        COMMIT = 4
    
    def __init__(self, sender, type, chain, signature = None):
        self.sender = sender
        self.type = type
        self.chain = chain
        self.signed = signature
    
    def ok(self, sender, signature):
        return Message(sender, Message.Type.OK, self.chain, signature)

class Offer:
    class State(Enum):
        INITIAL   = 0  # created Offer
        # leader
        PROPOSING = 1 # leader sent propose(); await cohorts
        DECIDING  = 2 # leader collected responses; await player
        COMITTING = 3 # leader got all OKs
        # cohort
        # TODO: do I need both OKED and COUNTERED states?
        RECEIVED  = 4 # cohort received new offer; await player
        OKED      = 5 # cohort OKed new offer; await leader
        COUNTERED = 6 # cohort countered offer; await leader
        # common
        COMMITTED = 7 # end result; both leader and cohort agree
        ABORTED   = 8 # end result; both leader and cohort agree
    
    def __init__(self, chain=None) -> None:
        self.chain: Chain = chain
        self.state = Offer.State.INITIAL
    
    def state(self):
        return self.state

    def responses(self):
        pass

    def propose(self, chain):
        assert self.state == Offer.State.INITIAL, (
            "Offer object is already filled. Create a new Offer."
        )
        self.chain:Chain = chain
        self.state = Offer.State.PROPOSING
        self.counters = {}
        return self
    
    def receive(self, chain):
        assert self.state == Offer.State.INITIAL, (
            "Offer object is already filled. Create a new Offer."
        )
        self.chain = chain
        self.state = Offer.State.RECEIVED
        return self
    
    def ok(self):
        assert self.state == Offer.State.RECEIVED
        self.state = Offer.State.OKED
        return self
    
    def counter(self, counter):
        assert self.state == Offer.State.RECEIVED
        self.state = Offer.State.COUNTERED
        return Offer(counter)

    def add_ok(self, pid, signature):
        self.chain.add_ok(pid, signature)
    
    def add_counter(self, pid, counter):
        assert isinstance(counter, Chain)
        # ensure counter is a valid counter of chain
        if not self.chain.is_counter(counter):
            return None
        
        # TODO: check if pid already made a counter
        self.counters[pid] = counter

    
    def __hash__(self):
        hash(self.chain)


class Chain:
    def __init__(self):
        self.actions: list[Action] = []
        self.OKs = {} # should be signatures

    def __init__(self, owner, actions, prev=None):
        self.owner = owner
        self.actions: list[Action] = actions
        self.OKs = {} # should be signatures
        self.prev = prev # hash for participants to remove the previous

    def add_ok(self, pid, ok):
        # TODO: should verify signature here
        self.OKs[pid] = ok
    
    def add_action(self, action):
        self.actions.append(action)
    
    def counter(self, actions): # return a new chain
        return Chain(self.owner, self.actions + actions, prev = hash(self))
    
    # is a valid counter offer if
    # only appended to actions
    # has a hash of self in counter.prev
    def is_counter(self, counter):
        return (counter.owner == self.owner and
                counter.prev == hash(self) and
                counter.actions[0:len(self.actions)] == self.actions)
    
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
    chain = Chain(1, [])
    assert hash(chain) == hash((1, tuple([])))

    # add an action
    action = Action(2, "BLAH")

    assert hash(action) == hash((2, "BLAH"))

    chain.add_action(action)
    assert hash(chain) == hash((1, tuple([action])))

    offer = Offer().receive(chain)

    offer.add_ok(2, "2")
    new_action = Action(3, "hmm")
    new_offer = offer.counter(chain.counter([new_action]))

    assert offer.chain.is_counter(new_offer.chain)


if __name__ == "__main__":
    main()
    print("PASS")

# TODO:
# 1. Add prev to hash of Chain