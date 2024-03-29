import asyncio
from communication import ClientServerSocket
import socket
from time import sleep


class CoordinatedCommunicator:
    def __init__(self, own_id, id_port_map) -> None:
        self.own_id = own_id
        self.id_port_map = id_port_map
        self.port_id_map = { v: k for k, v in id_port_map.items() }

        self.sockets: Dict[int, socket] = {}

        self.server = socket.socket()
        addr = ('localhost', id_port_map[own_id])
        self.server.bind(addr)
        self.server.setblocking(True)

        for peer_id in sorted(id_port_map.keys()):
            print("own:", own_id)
            print("on:", peer_id)
            print(id_port_map)

            if peer_id == own_id:
                continue

            # self.sockets[peer_id] = ClientServerSocket(id_port_map[own_id], id_port_map[peer_id])

            # act as server for ids less than own
            if peer_id < own_id:
                while not peer_id in self.sockets:
                    print("listening for", peer_id)
                    self.accept()

            # act as client for ids greater than own
            else: # peer_id > own_id
                # self.sockets[peer_id].connect()
                print("connecting to", peer_id)
                self.connect(peer_id)

        print("INIT FINISHED. Sockets:")
        print(self.sockets)

    def connect(self, peer_id) -> None:
        while True:
            # self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sockets[peer_id] = socket.socket()
            ret = self.sockets[peer_id].connect_ex(('localhost', self.id_port_map[peer_id]))
            if ret == 0:
                self.send_str(peer_id, str(self.own_id))
                break
            print("RET:", ret)
            print("Failed. Trying again in 2 seconds")
            sleep(2)
        print(self.sockets[peer_id])

    def accept(self) -> None:
        # server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while True:
            try:
                self.server.listen()
                client, client_addr = self.server.accept()
                print(client)
                print(client_addr)
                peer_id = int(client.recv(1024).decode())
                print("peer_id:", peer_id)
                self.sockets[peer_id] = client
                return
            except Exception as e:
                print(e)
                sleep(2)
                print("Trying again...")

    def send_str(self, peer_id, message) -> None:
        if peer_id == self.own_id:
            print("Can't send to self")
            return None
        if not peer_id in self.sockets:
            print (f"No socket data found for {peer_id}")
            return None
        self.sockets[peer_id].sendall(message.encode())

    def send(self, peer_id, data) -> None:
        print("send() got:", data)
        if peer_id == self.own_id:
            print("Can't send to self")
            return None
        if not peer_id in self.sockets:
            print (f"No socket data found for {peer_id}")
            return None
        self.sockets[peer_id].sendall(data)

    def recv(self, peer_id) -> str:
        if peer_id == self.own_id:
            print("Can't receive from self")
            return None
        if not peer_id in self.sockets:
            print (f"No socket data found for {peer_id}")
            return None

        while True:
            try:
                # [:-1] to remove b'\n'
                return self.sockets[peer_id].recv(1024).split()
            except:
                print("No data. Trying Again in 2 seconds!")
                sleep(2)

    def recv_str(self, peer_id) -> str:
        if peer_id == self.own_id:
            print("Can't receive from self")
            return None
        if not peer_id in self.sockets:
            print (f"No socket data found for {peer_id}")
            return None

        while True:
            try:
                # [:-1] to remove b'\n'
                return self.sockets[peer_id].recv(1024).decode().strip()
            except:
                print("No data. Trying Again in 2 seconds!")
                sleep(2)

    def flush(self, peer_id) -> None:
        if peer_id == self.own_id:
            print("Can't flush self")
            return None
        if not peer_id in self.sockets:
            print (f"No socket data found for {peer_id}")
            return None


