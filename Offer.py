from enum import Enum
from copy import deepcopy
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class Message:
    class Type(Enum):
        PROPOSE = 1
        OK = 2
        COUNTER = 3
        COMMIT = 4
    
    def __init__(self, sender, type, chain, signature = None):
        self.sender = sender
        self.type: Message.Type = type
        self.chain: Chain = chain
        self.signed = signature
    
    def sign(self, key):
        #TODO: actually make this signature instead of just key
        self.signed = key
    
    def ok(self, sender, signature):
        return Message(sender, Message.Type.OK, self.chain, signature)
    
    def __str__(self):
        string = f"Message by {self.sender}\n"
        string += f"type: {self.type.name}\n"
        string += str(self.chain)
        string += str(self.signed)
        return string 

class Offer:
    class State(Enum):
        INITIAL   = 0  # created Offer
        # leader
        PROPOSING = 1  # leader sent propose(); await cohorts
        COUNTER   = 2  # leader received counter; await player
        DECIDING  = 3  # leader collected responses; await player
        COMITTING = 4  # leader got all OKs
        # cohort
        # TODO: do I need both OKED and COUNTERED states?
        RECEIVED  = 6  # cohort received new offer; await player
        OKED      = 7  # cohort OKed new offer; await leader
        COUNTERED = 8  # cohort countered offer; await leader
                       # old offer: ABORTED;
        # common
        COMMITTED = 10 # end result; both leader and cohort agree
        ABORTED   = 11 # end result; both leader and cohort agree
    
    def __init__(self, chain=None) -> None:
        self.chain: Chain = chain
        self.state = Offer.State.INITIAL
        self.prev = None
        self.counters = {}

    def state(self):
        return self.state

    def respondants(self) -> list[any]:
        return list(self.chain.OKs.keys()) + list(self.counters.keys())

    def propose(self, chain, prev=None):
        assert self.state == Offer.State.INITIAL, (
            "Offer object is already filled. Create a new Offer."
        )
        self.chain:Chain = chain
        self.state = Offer.State.PROPOSING
        self.prev=hash(prev)
        self.counters = {}
        return self
    
    def counter(self, counter):
        assert self.state == Offer.State.INITIAL

        self.state = Offer.State.COUNTER
        self.chain = counter

        return self

    def commit(self):
        assert self.state == Offer.State.PROPOSING, (
            "trying to COMMIT an unproposed offer"
        )
        assert len(self.counters) == 0, (
            "at least one cohort did not ok"
        )

        self.state = Offer.State.COMITTING
    
    def abort(self):
        self.state = Offer.State.ABORTED

    def receive(self, chain):
        assert self.state == Offer.State.INITIAL, (
            "Offer object is already filled. Create a new Offer."
        )
        # separate copy avoids single process, multi-threaded issues
        self.chain = deepcopy(chain)
        self.state = Offer.State.RECEIVED
        return self
    
    def ok(self, own_pid, signature):
        assert self.state == Offer.State.RECEIVED
        self.state = Offer.State.OKED
        self.add_ok(own_pid, signature)
        return self

    def make_counter(self, pid, counter):
        assert self.state == Offer.State.RECEIVED
        assert self.chain.is_counter(counter)

        self.state = Offer.State.COUNTERED

        self.add_counter(pid, counter)

        return self
    
    def committed(self):
        self.state == Offer.State.COMMITTED
        return self
    
    def add_ok(self, pid, signature):
        self.chain.add_ok(pid, signature)
        return self
    
    def add_counter(self, pid, counter):
        assert isinstance(counter, Chain)
        # ensure counter is a valid counter of chain
        if not self.chain.is_counter(counter):
            return None
        
        # TODO: check if pid already made a counter
        counter_offer = Offer().counter(counter)
        self.counters[pid] = counter_offer
        return self
    
    def get_message(self, own_pid):
        m_type = None
        chain = self.chain
        if self.state == Offer.State.PROPOSING:
            m_type = Message.Type.PROPOSE
        elif self.state == Offer.State.OKED:
            m_type = Message.Type.OK
        elif self.state == Offer.State.COUNTERED:
            m_type = Message.Type.COUNTER
            chain = self.counters[own_pid]
        elif self.state == Offer.State.COMITTING:
            m_type = Message.Type.COMMIT
        else:
            return None

        return Message(
            sender=own_pid,
            type=m_type,
            chain=chain,
        )
    
    def __hash__(self):
        return hash(self.chain)
    
    def __str__(self):
        string = "\n======OFFER======\n"
        string += f"state: {self.state.name}\n"
        string += str(self.chain) + "\n"
        string += "counters:\n"
        if not self.counters:
            string += "None\n"
        else:
            string += "\n"
            for pid, counter in self.counters.items():
                string += str(pid) + ":" + str(counter)  + "\n"
        string += "=================\n"
        return string


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
    
    def __str__(self):
        string = f"----{hex(hash(self))}-----\n"
        string += "owner: " + str(self.owner) + "\n"
        string += "OKs:\n" + str(self.OKs) + "\n"
        string += f"prev: {'None' if not self.prev else hex(self.prev)}\n"
        string += "ACTIONS:\n"
        for i, action in enumerate(self.actions):
            string += f"\t{i}: " + str(action) + "\n"
        string += "-------------\n"
        return string

    def __repr__(self) -> str:
        string = f"----{hex(hash(self))}-----\n"
        string += "owner: " + str(self.owner) + "\n"
        string += "OKs:\n" + str(self.OKs) + "\n"
        string += f"prev: {'None' if not self.prev else hex(self.prev)}\n"
        string += "ACTIONS:\n"
        for i, action in enumerate(self.actions):
            string += f"\t{i}: " + str(action) + "\n"
        string += "-------------\n"
        return string


# action can be nested using hashes
class Action:
    def __init__(self, owner: int, content: str):
        if not content:
            log.error("cannot create empty action")
            return

        self.owner = owner
        self.content = content
    
    def __hash__(self):
        return hash((self.owner, self.content))
    
    def __str__(self) -> str:
        return f"ACTION by {self.owner}: {self.content}"

    def __repr__(self) -> str:
        return f"ACTION by {self.owner}: {self.content}"

def main():
    chain = Chain(1, [])
    assert hash(chain) == hash((1, tuple([])))

    # add an action
    action = Action(1, "BLAH")

    assert hash(action) == hash((1, "BLAH"))

    chain.add_action(action)
    assert hash(chain) == hash((1, tuple([action])))

    offer_prop = Offer().propose(chain)

    offer_to_ok = Offer().receive(offer_prop.chain)
    offer_to_counter = Offer().receive(offer_prop.chain)

    offer_to_ok.ok(2, "2")

    new_action = Action(3, "hmm")
    counter = offer_to_counter.chain.counter([new_action])
    offer_to_counter.counter(3, counter)

    print("proposed offer:\n", offer_prop)
    print("oked offer:\n", offer_to_ok)
    print("countered offer:\n", offer_to_counter)

    print(id(offer_to_counter.chain))
    print(id(offer_to_ok.chain))
    print(id(offer_prop.chain))



if __name__ == "__main__":
    main()
    print("PASS")

# TODO:
# 1. Add prev to hash of Chain
