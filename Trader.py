from abc import ABC, abstractmethod
from threading import Thread
import asyncio
from enum import Enum
import logging
from Peer import Peer
from Offer import Message, Chain, Offer, Action


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# 
#               ┌──────┐
#               │Trader│
#               └──┬───┘
#                  │
#            ┌─────▼─────┐
#            │Coordinated│
#            └─────┬─────┘
#                  │
#   ┌────┐      ┌──▼───┐        Peer implements:
#   │Node│      │Player│
#   └─┬──┘      └──┬───┘         send() -- network specific
#     │            │
#     └─────┬──────┘             respond() -- player choice
#           │
#         ┌─▼──┐                Peer uses:
#         │Peer│                 offer() -- player choice
#         └────┘                 dc_receive() -- on receiving
# 

# use of library implements Peer with some functionality and provide it
# TODO: remove Node from this diagram: implementation-specific


class Trader(Peer, ABC):
    def __init__(self, pid):
        super().__init__(pid)
        self.__offers: set(Offer) = set()
    

    # these must be implemented
    # must call accept() or reject() with offer
    @abstractmethod
    def respond(self, offers):
        pass

    @abstractmethod
    def get_participants():
        pass
    
    @abstractmethod
    def get_own_pid():
        pass

# interface
# ---------------------------------------
    async def offer(self, chain, prev=None):
        """
        Create an Offer and propose to all participants
        """
        # create offer for tracking
        offer = Offer().propose(chain, prev=prev)
        self.__offers.add(offer)

        # send PROPOSE to everyone
        await self.__propose(offer)

    async def accept(self, chain: Chain):
        """
        Used for:
        1. accept a proposed offer and send OK
        2. accept a COUNTER and propose it to everyone
        """

        if chain in self.__offers:
            offer = self.__offers[chain]
            # cohort received offer and accepting
            if offer.state == Offer.State.RECEIVED:
                self.__ok(offer)

        # leader received counters and chose offer
        elif chain.prev in self.__offers:
            original_offer = self.__offers[chain.prev]
            if original_offer.state == Offer.State.DECIDING:
                original_offer.abort()
                # remove original_offer with its counters
                self.__offers.remove(original_offer)
            
                # propose counter
                self.offer(chain, prev=original_offer.chain)

    async def reject(self, original_chain, counter_chain=None):
        """
        Used for:
        1. reject a proposed offer and send COUNTER
        2. reject a COUNTER but propose a new COUNTER
        """
        # offers are just hashed by their chain so I think this should work...?
        original_offer: Offer = self.__offers[original_chain]
        # cohort received a proposed offer
        if original_offer.state == Offer.State.RECEIVED:
            if counter_chain:
                counter_offer = original_offer.counter(counter_chain)
        # leader rejecting a counter offer
        elif original_offer.state == Offer.State.DECIDING:
            pass


# internal
# ---------------------------------------
    async def __propose(self, offer: Offer):
        """
        send PROPOSE message to all participant
        """
        message = offer.get_message(self.get_own_pid())
        message.sign(self.get_own_pid())

        participants = self.get_participants()
        send_tasks = [asyncio.create_task(self.send(p, message))
                      for p in participants]
        asyncio.gather(send_tasks)
    
    async def __commit(self, offer: Offer):
        offer.commit()
        message = offer.get_message(self.get_own_pid())
        message.sign(self.get_own_pid())

        participants = self.get_participants()
        send_tasks = [asyncio.create_task(self.send(p, message))
                      for p in participants]
        asyncio.gather(send_tasks)

    async def __ok(self, offer:Offer):
        offer.ok()
        message = offer.get_message(self.get_own_pid())
        message.sign(self.get_own_pid())

        # send OK to leader
        leader = offer.chain.owner
        await asyncio.create_task(self.send(leader, message))
        

    async def __counter(self, original, new):
        pass

    async def __responses_received(self, offer: Offer):
        if len(offer.counters) == 0:
            await self.__commit(offer)
        
        else:
            await self.respond(offer.counters.values())

    
    async def __recv(self, message: Message):
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
            offer: Offer = self.__offers[message.chain]
            offer.add_ok(message.sender, message.signed)
            if (offer.chain.OKs.keys() + offer.counters.keys() ==
                self.get_participants()):
                await self.__responses_received(offer)

        elif message.type == Message.Type.COUNTER:
            offer: Offer = self.__offers[message.chain.prev]
            offer.add_counter(message.sender, message.chain)
            if (offer.chain.OKs.keys() + offer.counters.keys() ==
                self.get_participants()):
                await self.__responses_received(offer)
        # -------------------------------------

        # cohort
        # -------------------------------------
        elif message.type == Message.Type.PROPOSE:
            # if prev in offers (leader accepted counter)
            if message.chain.prev and message.chain.prev in self.__offers:
                # remove
                self.__offers.remove(message.chain.prev)

            offer = Offer().receive(message.chain)
            self.__offers.add(offer)
            self.respond(offer)
        # -------------------------------------

    # temporary
    # TODO: remove and actually use Peer's send()
    async def send(participant, message):
        print(f"SENDING {participant}:\n{message}")


class BasicTrader(Trader):
    def __init__(self):
        super().__init__()
    
    # these must be implemented
    # must call accept() or reject() with offer
    def respond(self, offers):
        for i, offer in enumerate(offers):
            print(f"{i}:", offer)
        input("Enter counter")
        pass

    def get_participants():
        return [0, 1, 2]
    
    def get_own_pid():
        return 1

if __name__ == "__main__":
    trader = BasicTrader()


# TODO:
# 1. make Teller thread-safe, should I though? Does this make more limited?
#     (a) make sure you only call one respond() at a time
#     this also allows me to make it async so it does not have to wait for respond(), e.g.