"""
* Ensures integrity and coordination
* de-centralized process (no need for a "central" player)
 ** How to join game?
 *** can make it centralized just in joining for now...
* (2PC) --> PC2PC --> NPC2PC
* LATER: Wrapper that is Method-independent for sending, receiving, and potentially error handling
"""

# If any player objects, action is abandoned.
# What if player does not respond. Abandon? or remove player from game?

"""
Flow to join game will be:
1. There's a leader with known connection information
2. Leader keeps info of current players in session
3. When a new player asks to connect. Leader gives them id and adds them to list
4. Leader decides when to commence game.
5. Once game commences, (FOR NOW) no new players can be added.
6. Leader sends list of id's to each of the registered players deciding turn
"""

from typing import List


class Resource:
    def __init__(self) -> None:
        pass

class Game:
    def __init__(self) -> None:
        self.players: List[Player] = []
        pass
    
    def register_player(self, id) -> None:
        self.players.append(Player(id))

# ONCE Game is established and each player has id and turn
class Player:
    def __init__(self, id: int) -> None:
        self.id = id
        self.cards = []
    
    # Use this. Returns id
    def __init__(self) -> int: # will also provice info to connec
        # use info provided to connect to get id
        pass
        return 1

    # Other players can object!
    def play_resource(self, resource: Resource) -> None:
        pass

    # Note to self: generalize and abstract this more later on
    # For example, add actions that don't need to directly attack a resource
    # needs to be broadcasted to all players
    # If any player objects, abort
    def attack(self, attackee: Player, resource: Resource):
        pass

    # pass turn to next player in line
    def end_turn(self) -> None:
        pass
