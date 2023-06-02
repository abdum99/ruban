from p2pnetwork.node import Node, NodeConnection
from Coordinated import Coordinated
import logging
from threading import Thread

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# sample ports map to use for connection
ports_map = {
        0: 33330,
        1: 33331,
        2: 33332,
        3: 33333,
        4: 33334,
        5: 33335,
        6: 33336,
        7: 33337,
        8: 33338,
        9: 33339,
        }

# a connection is something you can call
# <get_conn_info> on and pass to send, etc
class Peer(Node, Coordinated):
    ADDRESS = "127.0.0.1"
    HOST_PORT = 33330

    def __init__(self, pid):
        port = ports_map[pid]
        is_host = pid == 0

        # __mro__ : Peer, Node, Thread, Coordinated
        # calls Node's __init__()
        super().__init__(Peer.ADDRESS, port, pid, None, 0)

        Coordinated.__init__(self, is_host)

        self.setup(f"{Peer.ADDRESS}:{Peer.HOST_PORT}")

    def register_callback(self, callback):
        self.register_coord_callback(callback)


    def outbound_node_connected(self, connected_node):
        # print("outbound_node_connected: " + connected_node.id)
        self.on_new_connection_callback(connected_node)

    def inbound_node_connected(self, connected_node):
        # print("inbound_node_connected: " + connected_node.id)
        self.on_new_connection_callback(connected_node)

    def inbound_node_disconnected(self, connected_node):
        pass

    def outbound_node_disconnected(self, connected_node):
        pass

    def node_message(self, connected_node, data):
        # call Coordinated's on_receive
        self.on_receive(connected_node, data)

    def node_disconnect_with_outbound_node(self, connected_node):
        pass
        # print("node wants to disconnect with oher outbound node: " + connected_node.id)

    def node_request_to_stop(self):
        pass
        # print("node is requested to stop!")

    def __get_connection__(self, conn_info):
        l = conn_info.split(":")
        return (l[0], int(l[1]))

# These functions are implemented for Coordinated
    def get_conn_info(self, connection):
        return f"{connection.host}:{connection.port}"
        # return (connection.host, int(connection.port))

    def listen_for_connections(self, callback):
        self.on_new_connection_callback = callback
        self.start()

    def stop_listening_for_connections(self):
        pass
        # self.node_request_to_stop()

    def connect(self, peer) -> NodeConnection:
        conn_info = self.__get_connection__(peer)
        if self.connect_with_node(conn_info[0], conn_info[1]):
            # find connected node
            for connection in self.all_nodes:
                if (connection.host == conn_info[0] and
                    connection.port == conn_info[1]):
                    return connection
            print("did not find connection")
        return None

    def send(self, recipient, message):
        self.send_to_node(recipient, message)

# TODO: remove this class and just have people implement Coordinated instead
# TODO: actually make it so that they can pass a class to Coordinated when initializing
#           and Coordinated just uses that class
