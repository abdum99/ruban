from Peer import Peer
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

ports_map = {
        0: 33330,
        1: 33331,
        2: 33332,
        3: 33333,
        }

def main():
    pid = int(input("ID: "))
    peer = Peer(pid == 0, pid, ports_map[pid])



if __name__ == "__main__":
    main()
