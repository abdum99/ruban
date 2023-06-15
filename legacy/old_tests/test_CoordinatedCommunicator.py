import logging
from time import sleep
from CoordinatedCommunicator import CoordinatedCommunicator

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

ports_map = {
        1: 8001,
        2: 8002,
        3: 8003,
        }

def main():
    cid = int(input("ID: "))
    cc = CoordinatedCommunicator(cid, "127.0.0.1", ports_map[cid])
    cc.start()


    if cid == 1:
        log.info("cc1 about  to send message")
        input("PressEnter when ready")
        cc.connect_with_node("127.0.0.1",ports_map[2])
        cc.send_to_nodes({"message": "whatup"})

    while True: # run indefinitely
        pass

if __name__ == "__main__":
    main()
