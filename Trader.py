from abc import ABC, abstractmethod
from threading import Thread
from enum import Enum
import logging
from Offer import Message, Chain, Offer, Action

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class Trader(ABC):
    def __init__(self):
        super().__init__()
        self.__offers: dict[int, Offer] = {}
    

    # these must be implemented
    # must call accept() or reject() with offer
    @abstractmethod
    def respond(self, offer):
        pass
    
    @abstractmethod
    def committed(self, chain):
        pass

    @abstractmethod
    def aborted(self, chain):
        pass

    # ===========================
    # to be implemented by deCoordinated
    # --------------
    @abstractmethod
    def send_to_pid(self, participant, message):
        pass

    @abstractmethod
    def get_participants(self):
        pass
    
    @abstractmethod
    def get_own_pid(self):
        pass
    # ==========================

# interface
# offer(), accept(), reject(), counter()
# ---------------------------------------
    def offer(self, chain, prev=None):
        """
        Create an Offer and propose to all participants
        """
        # create offer for tracking
        offer = Offer().propose(chain, prev=prev)
        self.__add_offer(offer)

        # send PROPOSE to everyone
        self.__propose(offer)

    def accept(self, offer: Offer):
        """
        Used for:
        1. accept a proposed offer and send OK
        2. accept a COUNTER and propose it to everyone
        """

        # cohort received offer and accepting
        if offer.state == Offer.State.RECEIVED:
            if not self.__has_offer(offer):
                log.error("Accepting uncrecognized offer")
                return 

            self.__ok(offer)

        # leader choosing counter offer
        elif (offer.state == Offer.State.COUNTER and 
              self.__has_offer(offer.chain.prev)):
                orig_offer = self.__get_offer(offer.chain.prev)
                if orig_offer.state == Offer.State.DECIDING:
                    orig_offer.abort()
                    # remove orig_offer with its counters
                    self.__pop_offer(orig_offer)
                
                    # propose counter
                    self.offer(offer.chain, prev=orig_offer.chain)

    def reject(self, original_chain, counter_chain=None):
        """
        Used for:
        1. reject a proposed offer and send COUNTER
        2. reject a COUNTER but propose a new COUNTER
        """
        # offers are just hashed by their chain so I think this should work...?
        orig_offer = self.__get_offer(original_chain)
        # cohort received a proposed offer
        if orig_offer.state == Offer.State.RECEIVED:
            if counter_chain:
                counter_offer = orig_offer.counter(counter_chain)
        # leader rejecting a counter offer
        elif orig_offer.state == Offer.State.DECIDING:
            pass

# internal
# ---------------------------------------
    def __broadcast(self, message):
        log.debug(f"broadcasting message: {str(message)}")
        for p in self.get_participants():
            if p != self.get_own_pid(): # do not send to self
                self.send_to_pid(p, message)

    def __propose(self, offer: Offer):
        """
        send PROPOSE message to all participant
        """
        log.debug(f"Proposing offer {str(offer)}")
        message = offer.get_message(self.get_own_pid())
        message.sign(self.get_own_pid())

        self.__broadcast(message)
    
    def __commit(self, offer: Offer):
        log.debug("Committing offer %s", str(offer))
        offer.commit()
        message = offer.get_message(self.get_own_pid())
        message.sign(self.get_own_pid())

        self.__broadcast(message)

        offer.committed()

        self.committed(offer.chain)

    def __ok(self, offer:Offer):
        offer.ok(self.get_own_pid(), self.get_own_pid())
        message = offer.get_message(self.get_own_pid())
        message.sign(self.get_own_pid())

        # send OK to leader
        leader = offer.chain.owner
        self.send_to_pid(leader, message)

    def __counter(self, original, new):
        pass

    def __responses_received(self, offer: Offer):
        if len(offer.counters) == 0:
            self.__commit(offer)
        
        else:
            offer.state = Offer.State.DECIDING
            self.respond(offer)
    
    def __all_responded(self, offer: Offer):
        return (set(offer.respondants() + [self.get_own_pid()]) ==
                set(self.get_participants()))
    
    def __recv(self, message: Message):
        """
        ### leader:
        1. if OK:
            1.1. add to OKers
            1.2. if (oks + counters) == participants, go to 3.
        2. if COUNTER
            2.1. find prev, add to prev
            2.2. if (oks + counters) == participants, go to 3.

        3. check OKs and counters:
            3.1. if all OKs, send COMMIT
            3.2. else, respond() with all counters
            
        ### if cohort:
        1. if PROPOSE:
            1.1. if prev in self.__offers, delete original
            1.2. respond()

        2. if COMMIT:
            2.1. confirm OKs and validate signatures
                (if good, commit, else reject)
        
        """
        # leader
        # -------------------------------------
        if message.type == Message.Type.OK:
            offer = self.__get_offer(message.chain)
            offer.add_ok(message.sender, message.signed)
            if self.__all_responded(offer):
                self.__responses_received(offer)

        elif message.type == Message.Type.COUNTER:
            offer = self.__get_offer(message.chain.prev)
            offer.add_counter(message.sender, message.chain)
            if self.__all_responded(offer):
                self.__responses_received(offer)
        # -------------------------------------

        # cohort
        # -------------------------------------
        elif message.type == Message.Type.PROPOSE:
            # if prev in offers (leader accepted counter)
            if message.chain.prev and self.__has_offer(message.chain.prev):
                # remove
                self.__pop_offer(message.chain.prev)

            offer = Offer().receive(message.chain)
            self.__add_offer(offer)
            self.respond(offer)
        
        elif message.type == Message.Type.COMMIT:
            # TODO: validate signatures
            offer = self.__get_offer(message.chain)
            offer.committed()
            self.committed(offer.chain)
        # -------------------------------------

    # ===============================
    # mechanisms to lookup using offers and chains
    # ----------------
    def __has_offer(self, lookup: Offer | Chain) -> bool:
        return hash(lookup) in self.__offers

    def __add_offer(self, offer: Offer):
        self.__offers[hash(offer)] = offer
    
    def __get_offer(self, lookup: Offer | Chain):
        return self.__offers[hash(lookup)]
    
    def __pop_offer(self, lookup: Offer | Chain):
        return self.__offers.pop(hash(lookup))
    # ===============================
    

class BasicTrader(Trader):
    def __init__(self):
        super().__init__()
    
    # these must be implemented
    # must call accept() or reject() with offer
    def respond(self, offer):
        pass

    def get_participants(self):
        return [0, 1, 2]
    
    def get_own_pid(self):
        return 1

    # temporary
    # TODO: remove and actually use Peer's send()
    def send(self, participant, message):
        pass

def main():
    trader = BasicTrader()
    actions = [Action(1, f"action{i}") for i in range(1, 3)]
    chain = Chain(1, actions)
    trader.offer(chain)

if __name__ == "__main__":
    main()


# TODO:
# 1. make Teller thread-safe, should I though? Does this make more limited?
#     (a) make sure you only call one respond() at a time
#     this also allows me to make it async so it does not have to wait for respond(), e.g.
