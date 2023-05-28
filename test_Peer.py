from Peer import Peer
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def main():
    pid = int(input("ID: "))
    peer = Peer(pid)


if __name__ == "__main__":
    main()
