from p2pnetwork.node import Node
from Coordinated import Coordinated
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class Peer(Node, Coordinated):
    ADDRESS = "localhost"
    HOST_PORT = 33330

    def __init__(self, is_host, nid, port):
        # __mro__ : Peer, Node, Thread, Coordinated
        # calls Node's __init__()
        super().__init__(Peer.ADDRESS, port, nid, None, 0)

        # calls Coordinated's __init__()
        host_conn_info = {"host": Peer.ADDRESS, "port": Peer.HOST_PORT}
        own_conn_info = {"host": Peer.ADDRESS, "port": port}
        Coordinated.__init__(self, is_host, host_conn_info, own_conn_info)

    def outbound_node_connected(self, connected_node):
        print("outbound_node_connected: " + connected_node.id)
        self.on_new_connection_callback({"host": connected_node.host, "port": connected_node.port})

    def inbound_node_connected(self, connected_node):
        log.info("in inbound_node_connected")
        print("inbound_node_connected: " + connected_node.id)
        self.on_new_connection_callback({"host": connected_node.host, "port": connected_node.port})

    def inbound_node_disconnected(self, connected_node):
        print("inbound_node_disconnected: " + connected_node.id)

    def outbound_node_disconnected(self, connected_node):
        print("outbound_node_disconnected: " + connected_node.id)

    def node_message(self, connected_node, data):
        print("node_message from " + connected_node.id + ": " + str(data))
        # call Coordinated's on_receive
        self.on_receive({"host": connected_node.host, "port": connected_node.port}, data)

    def node_disconnect_with_outbound_node(self, connected_node):
        print("node wants to disconnect with oher outbound node: " + connected_node.id)

    def node_request_to_stop(self):
        print("node is requested to stop!")

# These functions are implemented for Coordinated
    def listen_for_connections(self, conn_info, callback):
        self.on_new_connection_callback = callback
        self.start()

    def stop_listening_for_connections(self):
        self.node_request_to_stop()

    def connect(self, conn_info) -> bool:
        return self.connect_with_node(conn_info["host"], conn_info["port"])

    def send(self, conn_info, message):
        self.send_to_nodes(message)

