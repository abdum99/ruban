from Peer import Peer
from Offer import Action, Chain
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def main():
    pid = int(input("ID: "))
    peer = Peer(pid)
    if peer.is_host:
        input("Press <Return> when ready\n")
        peer.host_begin_round_robin()
    
    if pid == 0:
        act = input("Enter action\n")
        chain = Chain(pid, [act])
        peer.offer(chain)


if __name__ == "__main__":
    main()
