from CoordinatedCommunicator import CoordinatedCommunicator

id_port_map = {
    0: 33340,
    1: 33341,
    2: 33342,
    # 3: 33333,
}


def main():
    own_id = int(input("ID:"))
    input("<Return> when ready")
    communicator = CoordinatedCommunicator(own_id, id_port_map)
    turn = 0
    while True:
        if turn == own_id: # my turn
            valid = False
            while not valid:
                try:
                    user_input = input("<id>,<message>: ")
                    peer_id, message = user_input.split(',')[:2]
                    peer_id = int(peer_id.strip())
                    message = message.strip()
                    valid = True
                except:
                    print("Invalid input. Try Again")
            communicator.send(peer_id, "ACTION: " + message + "\n")
            for peer_id in id_port_map:
                if peer_id == own_id:
                    continue
                communicator.send(peer_id, "END\n")
            turn = (turn + 1) % len(id_port_map)
        else: # someone else's turn
            while True:
                message = communicator.recv(turn)
                print("recv:", message)
                if "END" in message:
                    print("GOT END")
                    break

                # handle action
                if message.startswith("ACTION:"):
                    print("<action handler> goes here")

            turn = (turn + 1) % len(id_port_map)

if __name__ == '__main__':
    main()
