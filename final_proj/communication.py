# Holds info for communication between players
# Abstract class for communication

from abc import ABCMeta, abstractmethod
from multiprocessing.connection import Client, Listener
from typing import Dict, Tuple
import asyncio

from django.dispatch import receiver

class Communication(metaclass=ABCMeta):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def connect(self, id) -> None:
        pass

    @abstractmethod
    def send(self, id, message) -> None:
        pass

    @abstractmethod
    def on_recv(self) -> None:
        pass

    @abstractmethod
    def listen(self) -> None:
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
    
    def on_recv(self) -> None:
        pass
    
    # Open connection to port and add (id, port) to connections mappings
    # Should probably change this to only take host, port and have 
    # <handle_conn> return id which connect can just verify
    async def connect(self, id, host, port) -> None:
        print("connecting to", id, "on", host, ":", port)
        reader, writer = await asyncio.open_connection(host, port)
        writer.write(str(self.playid).encode())
        await writer.drain()

        # check if success
        data = await reader.readline()
        response = data.decode()
        print("received response:", response)
        print("HOOORRRAAAAAAYYYYY!")


    async def send(self, id, message) -> None:
        pass
    
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
    
    async def listen(self) -> None:
        server = await asyncio.start_server(self.handle_conn, 'localhost', self.listen_port)
        async with server:
            await server.serve_forever()

    async def close(self, playid) -> None:
        writer = self.connections[playid][1]
        writer.close()
        await writer.wait_closed()


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