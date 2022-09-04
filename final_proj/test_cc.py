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
        if turn == own_id:
            user_input = input("<id>,<message>: ")
            peer_id, message = user_input.split(',')[:2]
            peer_id = int(peer_id.strip())
            message = message.strip()
            communicator.send(peer_id, "ACTION: " + message + "\n")
            for peer_id in id_port_map:
                if peer_id == own_id:
                    continue
                communicator.send(peer_id, "END\n")
            turn += 1
        else:
            message = communicator.recv(turn)
            if message.startswith("ACTION:"):
                print("recv:", message)
                message = communicator.recv(turn)

            print("recv:", message)
            assert message == "END"
            turn += 1

if __name__ == '__main__':
    main()
