# Holds info for communication between players
# Abstract class for communication

from abc import ABCMeta, abstractmethod
from multiprocessing.connection import Client, Listener
from typing import Dict, Tuple
import asyncio
import logging as log
import socket
from time import sleep

class Communication(metaclass=ABCMeta):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def connect(self, id) -> None:
        pass

    @abstractmethod
    def listen(self) -> None:
        pass

    @abstractmethod
    def send(self, id, message) -> None:
        pass

    @abstractmethod
    def recv(self) -> None:
        pass

    @abstractmethod
    def close(self, id) -> None:
        pass

class NETSocket(Communication):
    def __init__(self, port) -> None:
        super().__init__()
        self.listen_port = port
        self.connections = {}
    
    def on_recv(self) -> None:
        pass
    
    # Open connection to port and add (id, port) to connections mappings
    def connect(self, id, port) -> None:
        addr = ('localhost', port)
        conn = Client(addr) # family is deduced to be AF_INET
        self.connections[id] = conn

    def send(self, id, message) -> None:
        self.connections[id].send(message)
    
    def listen(self) -> None:
        addr = ('localhost', self.listen_port)
        listener = Listener(addr) # family is deduced to be AF_INET

    def close(self, id) -> None:
        self.connections[id].close()

class ASYNCSocket(Communication):
    def __init__(self, playid, port) -> None:
        super().__init__()
        self.listen_port = port
        self.playid = playid
        # holds tuples of (reader, writer)
        self.connections: Dict[int, Tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {} 
    
    # Open connection to port and add (id, port) to connections mappings
    # Should probably change this to only take host, port and have 
    # <handle_conn> return id which connect can just verify
    async def connect(self, id, host, port) -> None:
        print("called connect")
        if id in self.connections: # check that a connection wasn't already established with this id
            log.error(self.playid, "is already connected to", id)
            return

        log.info("connecting to", id, "on", host, ":", port)
        print("connecting...")
        reader, writer = await asyncio.open_connection(host, port)
        writer.write(str(self.playid).encode())
        await writer.drain()
        print("finished draining writer")

        # check if success
        data = await reader.readline()
        response = data.decode()
        log.info("received response:", response)
        if response.strip() == "success":
            self.connections[id] = (reader, writer)
            print("success, adding to connections")
            print(self.connections)
            log.info("Added", id, "to connections")


    async def handle_conn(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        message = (await reader.read(255)).decode()
        print("server received connection request:", message)
        playid = int(message)
        print("converted to int:", playid)
        if not playid in self.connections: # check that a connection wasn't already established with this id
            print("Was not in connections. Establishing new one")
            self.connections[playid] = (reader, writer)
            writer.write("success\n".encode())
            await writer.drain()

        else:
            print("player already connected:", self.connections[playid])
        print("HOOORRRAAAAAAYYYYY!")

    async def handle_conn(self, client) -> None:
        message = (await reader.read(255)).decode()
        print("server received connection request:", message)
        playid = int(message)
        print("converted to int:", playid)
        if not playid in self.connections: # check that a connection wasn't already established with this id
            print("Was not in connections. Establishing new one")
            self.connections[playid] = (reader, writer)
            writer.write("success\n".encode())
            await writer.drain()

        else:
            print("player already connected:", self.connections[playid])
        print("HOOORRRAAAAAAYYYYY!")

    # async def listen(self) -> None:
    #     server = await asyncio.start_server(self.handle_conn, 'localhost', self.listen_port)
    #     async with server:
    #         await server.serve_forever()
    #         print("serving")
    #         # await server.start_serving()
    #     print ("got out of serve loop")

    async def listen(self) -> None:
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        addr = ('localhost', self.listen_port)
        server.bind(addr)
        server.listen(1)
        client, client_addr = server.accept()
        print(client)
        print(client_addr)

    async def send(self, id, message) -> None:
        if not id in self.connections:
            log.error("ID NOT FOUND in connections")
        
        writer = self.connections[id][1]
        writer.write(message.encode())
        await writer.drain()
        print("drained writer")

    async def recv(self, playid) -> None:
        data = await self.connections[playid][0].readline()
        message = data.decode()
        print ("received msg:", message)
        # if not message:
        #     self.close()
        #     return ""
        return message

    async def close(self, playid) -> None:
        writer = self.connections[playid][1]
        writer.close()
        await writer.wait_closed()

class ClientServerSocket(Communication):
    def __init__(self, own_port, peer_port):
        super().__init__()
        self.own_port = own_port
        self.peer_port = peer_port


    def send(self, message) -> None:
        self.client.sendall(message.encode())
        pass

    def recv(self) -> None:
        return self.client.recv(1024).decode()

    def close(self, id) -> None:
        self.client.close()



"""
NOTE:
CHANGE The socket thing you fool. Make it so that each player gets a set of id's and connection info (e.g. port number)
and each player first starts server to listen for connections and then opens connections with other players whose id is
greater. That way we cover all connections.

1 2 3 4
1 <-> 2
1 <-> 3
1 <-> 4
2 <-> 3
2 <-> 4
3 <-> 4

Above abstraction is good though to just abstract away having to deal with whether a player was a server or a client in
openning the connections and just getting a pair of async readers/writers, but change impl to do as above
"""
"""
ADD:
each player starts listening until it has received connections from each of the id's below it:
So flow is
2, 3, 4 listen
1 connects to each of them
2 has now received connections from lower ids and closes listen socket
2 sends connections to 3 and 4
3 has now received connections from lower ids and closes listen socket
3 sends connections to 4
4 has now received connections from lower ids and closes listen socket
"""
