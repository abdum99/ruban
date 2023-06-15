from CoordinatedCommunicator import CoordinatedCommunicator
from proto.action_pb2 import ActionType, Action, Report

id_port_map = {
    0: 33340,
    1: 33341,
    # 2: 33342,
    # 3: 33333,
}

def make_action(message, own_id, peer_id):
    report = Report()
    report.report = message

    action = Action()
    action.type = ActionType.ACTION_INITIATE
    action.from_id = own_id
    action.to_id = peer_id
    action.report.MergeFrom(report)

    return action

def make_end_turn(own_id, peer_id):
    action = Action()
    action.type = ActionType.END_TURN
    action.from_id = own_id
    action.to_id = peer_id
    return action


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

            action = make_action(message, own_id, peer_id)
            print("made action:", action)
            to_send = action.SerializeToString() + "\n".encode()
            print("sending:", to_send)
            communicator.send(peer_id, to_send)
            for peer_id in id_port_map:
                if peer_id == own_id:
                    continue
                action = make_end_turn(own_id, peer_id)
                communicator.send(peer_id, action.SerializeToString() + "\n".encode())
            turn = (turn + 1) % len(id_port_map)
        else: # someone else's turn
            while True:
                message = communicator.recv(turn)
                print("recv:", message)
                for received in message:
                    print(received)
                    action = Action()
                    action.ParseFromString(received)
                    print("parsed:", action)
                    if action.type == ActionType.END_TURN:
                        print("GOT END")
                        break

                else:
                    # handle action
                    print("<action handler> goes here")

            turn = (turn + 1) % len(id_port_map)

if __name__ == '__main__':
    main()
