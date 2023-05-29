from p2pnetwork.node import Node, NodeConnection
from Coordinated import Coordinated
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# sample ports map to use for connection
ports_map = {
        0: 33330,
        1: 33331,
        2: 33332,
        3: 33333,
        4: 33334,
        5: 33335,
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

        self.setup((Peer.ADDRESS, Peer.HOST_PORT))

    def outbound_node_connected(self, connected_node):
        print("outbound_node_connected: " + connected_node.id)
        self.on_new_connection_callback(connected_node)

    def inbound_node_connected(self, connected_node):
        print("inbound_node_connected: " + connected_node.id)
        self.on_new_connection_callback(connected_node)

    def inbound_node_disconnected(self, connected_node):
        print("inbound_node_disconnected: " + connected_node.id)

    def outbound_node_disconnected(self, connected_node):
        print("outbound_node_disconnected: " + connected_node.id)

    def node_message(self, connected_node, data):
        print("node_message from " + connected_node.id + ": " + str(data))
        # call Coordinated's on_receive
        self.on_receive(connected_node, data)

    def node_disconnect_with_outbound_node(self, connected_node):
        print("node wants to disconnect with oher outbound node: " + connected_node.id)

    def node_request_to_stop(self):
        print("node is requested to stop!")

    def __find_connection__(self, conn_info):
        for node in self.all_nodes:
            if (node.host == conn_info[0] and
                node.port == conn_info[1]):
                return node
        return None

# These functions are implemented for Coordinated
    def get_conn_info(self, connection):
        return (connection.host, int(connection.port))

    def listen_for_connections(self, callback):
        self.on_new_connection_callback = callback
        self.start()

    def stop_listening_for_connections(self):
        pass
        # self.node_request_to_stop()

    def connect(self, peer) -> NodeConnection:
        if self.connect_with_node(peer[0], peer[1]):
            # find connected node
            for connection in self.all_nodes:
                if (connection.host == peer[0] and
                    connection.port == peer[1]):
                    return connection
        return None

    def send(self, recipient, message):
        self.send_to_node(recipient, message)
