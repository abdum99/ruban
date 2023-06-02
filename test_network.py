import unittest
import sys
from time import sleep
from Peer import Peer
import logging

MAX_TRIALS = 5
NUM_PARTICIPANTS = 6

class TestCoordinatedMethods(unittest.TestCase):

    def setUp(self):
        self.numParticipants = NUM_PARTICIPANTS
        self.peers = []
        self.msg_count = [0] * self.numParticipants

        # create 5 peers
        for i in range(self.numParticipants):
            self.peers.append(Peer(i))

        # busy wait until both nodes are connected
        while len(self.peers[0].all_nodes) < self.numParticipants - 1:
            sleep(2)
        
        print("All nodes connected to host: Host's list of participants", self.peers[0].all_nodes)
        self.peers[0].host_begin_round_robin()


    def all_nodes_connected(self):
        print("Testing all nodes are connected to each other")
        # for now just wait 5 seconds
        for i, peer in enumerate(self.peers):
            trials = 0
            while not peer.is_ready():
                if trials > MAX_TRIALS:
                    raise Exception(f"Timeout while waiting on peer {i} to be ready")
                trials += 1
                print(f"waiting on peer {i} to be ready")
                sleep(2)
            print("\npids:", peer.pids)
            try:
                self.assertEqual(sorted(peer.pids.values()),
                                 [j for j in range(self.numParticipants)])
            except AssertionError as e:
                print(repr(e))
                print(f"p{i} has participants:", peer.pids)

    def send_and_receive(self):
        for i, peer in enumerate(self.peers):
            for j, recipient in enumerate(self.peers):
                peer.coord_send(j, f"HELLO {j}. FROM {i}")

    def recv(self, pid, message):
        print(f"{pid} said {message}")


    def test_Coordinated(self):
        self.all_nodes_connected()
        for i, peer in enumerate(self.peers):
            peer.register_coord_callback(self.recv)
        self.send_and_receive()
            


if __name__ == "__main__":
    unittest.main()
    
