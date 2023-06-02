from abc import ABC, abstractmethod
from threading import Thread, Event, Lock
from time import sleep
import pickle
import json
import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Users cannot set their cid (Coordinated ID) because
# then we would have to figure out a conflict resolution
# maybe something we can add later, but for now this is done
# by the organizing host

# should instead do as follows:
# 
#  ┌───────┐    ┌─────────────┐
#  │  Node │    │ Coordinated │
#  └───────┘    └─────────────┘
#      ▲               ▲
#      │               │
#      │               │
#      └───────┬───────┘
#              │
#              │
#          ┌───┴──┐
#          │ Peer │
#          └──────┘

# Coordinated is an abstract class for participants
# One participants serves as the host to connect everyone together
# From there on onwards communication is P2P
# The host listens for connections to build a dictionary of participants
# then sends it to each of the participants
# Coordinated organizes turns and connection intitiations for P2P networks

# connection:
#  Implementation-defined; holds connection info that will be used for
#  listen_for_connections, connect, send, on_receive
#  * Should implement __str__ for helpful debugging

class Coordinated(ABC):
    class State(Enum):
        NOT_CONFIGURED = 0
        ACCEPTING_GUESTS = 1        # host accepting guests
        CONNECTING_TO_HOST = 2      # guest connecting to host
        SENDING_PARTICIPANTS = 3    # host sending participants and awaiting ACKs
        AWAITING_PARTICIPANTS = 4   # guest awaiting participants from host
        SENT_PARTICIPANTS = 5       # host received ACKs for participants
        AWAITING_CONNECTIONS = 6    # guests waiting for lower PIDs to connect to them
        CONNECTING = 7              # all lower PIDs connected, connecting to higer PIDs
        READY = 8                   # connected to all guests and have open channels

    # constants
    HOST_PID = 0
    class Message:
        TYPE_KEY = "_Coordinated_message_"
        JOINED = "Joined Party"
        REQ_PARTICIPANTS = "Request Participants"
        RES_PARTICIPANTS = "Response Participants"
        ACK_PARTICIPANTS = "Received Participants"
        BEGIN_CONNECT_SEQ = "Begin Connection Sequence"

    # ----------------------------------------
    # must implement these methods
    @abstractmethod
    def get_conn_info(self, connection):
        pass

    @abstractmethod
    def listen_for_connections(self, connection, callback):
        pass


    @abstractmethod
    def stop_listening_for_connections(self):
        pass


    @abstractmethod
    def connect(self, peer) -> bool:
        pass


    @abstractmethod
    def send(recipient, message):
        pass
    # ----------------------------------------

    def __update_state__(self, state):
        self.state = state

    # These methods are already implemented. You should not override
    def __add_participant__(self, connection):
        # should lock here
        participant = self.get_conn_info(connection)
        with self.connections_lock:
            pid = len(self.participants)
            self.pids[participant] = pid 
            self.participants.append(participant)
            log.info("Added new participant %s: %s", str(pid), str(participant))
        return participant

    def __add_connection__(self, participant, connection):
        with self.connections_lock:
            self.connections[participant] = connection


    def coord_send(self, pid, message):
        participant = self.participants[pid]
        self.__send__(participant, message)


    def __send__(self, participant, message):
        with self.connections_lock:
            try:
                connection = self.connections[participant]
            except KeyError as e:
                log.error("Trying to send message to participant with no open connection: %s", str(participant))
                return

        # self.send(connection, pickle.dumps(message).replace(b'\x04', b'\x03'))
        self.send(connection, json.dumps(message))

    def host_begin_round_robin(self):
        self.all_participants_joined.set()

    def is_ready(self):
        return self.state == Coordinated.State.READY

    def __setup_host__(self):
        self.all_participants_joined = Event()
        self.all_participants_acked = Event()

        self.own_pid = Coordinated.HOST_PID

        # <pids> and <participants> are common across all nodes
        # participants id's
        # <pids>: { conn_info --> PID }
        self.pids = {
            self.own_conn_info: Coordinated.HOST_PID
        }

        # participant connection info
        # <participants>: [ conn_info ]
        self.participants = [ self.own_conn_info ]

        self.accepting_new_connections = True
        self.listen_for_connections(self.__host_on_new_connection__)
        self.__update_state__(Coordinated.State.ACCEPTING_GUESTS)

        self.all_participants_joined.wait()

        self.accepting_new_connections = False
        self.stop_listening_for_connections()

        self.__update_state__(Coordinated.State.SENDING_PARTICIPANTS)

        self.participants_ack = [False] * len(self.participants)
        # host does not ack participants
        self.participants_ack[Coordinated.HOST_PID] = True

        # TODO: repeat this until all users have ACKed
        # for each connection, send list of participants and connections
        log.debug("Sending RES_PART: %s", range(len(self.participants)))
        for participant, pid in self.pids.items():
            if pid == 0: # do not send participants to host
                continue
            message = {
                Coordinated.Message.TYPE_KEY: Coordinated.Message.RES_PARTICIPANTS,
                "sender_pid": self.own_pid,
                "own_pid": pid,
                "participants": self.participants,
                "pids": self.pids,
                }
            self.__send__(participant, message)

        self.all_participants_acked.wait();

        log.debug("Host: sent list to all guests")
        self.__update_state__(Coordinated.State.SENT_PARTICIPANTS)

        for participant, pid in self.pids.items():
            if pid == 0: # do not send participants to host
                continue
            message = {
                Coordinated.Message.TYPE_KEY: Coordinated.Message.BEGIN_CONNECT_SEQ,
                }
            self.__send__(participant, message)

        # TODO: confirm guests are connected here
        # TODO: do this using 2PC

        self.__update_state__(Coordinated.State.READY)

    def __setup_guest__(self, host_conn_info):
        # add host as participant
        self.pids = {
            host_conn_info: Coordinated.HOST_PID
        }
        # participant connection info
        self.participants = [ host_conn_info ]

        self.participants_filled = Event()

        self.listen_for_connections(self.__guest_on_new_connection__)

        # connect to host
        log.info("Connecting to host")
        host = None
        while True:
            host = self.connect(host_conn_info)
            if host:
                self.__add_connection__(host_conn_info, host)
                break
            sleep(2)
            log.info("Trying again...")
        log.info("Connected to host")

        # wait until host sends participants
        # no need for loop bc .set() is sticky
        self.participants_filled.wait()

        log.info("Received Personal ID from host: %s", str(self.own_pid))
        log.info("Received list of %s participants from host", str(len(self.participants)))
        log.debug("participants: %s", str(self.participants))

    def setup(self, host_conn_info = None):
        if self.is_host:
            self.coord_thread = Thread(target=self.__setup_host__)
        else:
            if not host_conn_info:
                log.error("Must provide host connection")
                return 
            self.coord_thread = Thread(target=self.__setup_guest__, args=(host_conn_info,))

        self.coord_thread.start()

    def __init__(self, is_host):
        log.debug("initializing coordinated %s", "host" if is_host else "guest")
        self.is_host = is_host
        self.state = Coordinated.State.NOT_CONFIGURED
        self.own_conn_info = self.get_conn_info(self)

        # connections are unique to each node and not sent by host
        self.connections = {} # no connection to self
        self.connections_lock = Lock()

    def __del__(self):
        # TODO: signal coord thread to stop
        self.coord_thread.join()


    def __host_on_new_connection__(self, connected_node):
        log.debug("Host received new connection request: %s", str(connected_node))
        if self.accepting_new_connections:
            if connected_node in self.pids:
                log.error("Connection Info Already used by another participant. Pick different parameters")
            else:
                participant = self.__add_participant__(connected_node)
                self.__add_connection__(participant, connected_node)
                self.__send__(participant, {Coordinated.Message.TYPE_KEY: Coordinated.Message.JOINED})

        else:
            log.debug("Connection Request Refused: No Longer Accepting Connections.")


    def __guest_on_new_connection__(self, connected_node):
        participant = self.get_conn_info(connected_node)
        with self.connections_lock:
            assert participant in self.participants
        log.debug("Guest received new connection: %s", str(connected_node))
        self.__add_connection__(participant, connected_node)

    # =====================================
    # responses to actions
    # -------------------------

    def __ack_participant__(self, pid):
        self.participants_ack[pid] = True
        log.debug("participant %s acked list", pid)
        # if all have acked, set event
        if False not in self.participants_ack:
            log.debug("all participants acked")
            self.all_participants_acked.set()

    def __fill_participants__(self, message):
        with self.connections_lock:
            self.own_pid = message["own_pid"]
            self.participants = message["participants"]
            self.pids = message["pids"]

        self.__send__(self.participants[Coordinated.HOST_PID], {
            Coordinated.Message.TYPE_KEY: Coordinated.Message.ACK_PARTICIPANTS,
        })

        self.participants_filled.set() # notify waiting threads to proceed

    def ___sequence_connect__(self):
        log.debug("beginning connection sequence to %s", self.participants)

        # wait until all guests with lower pid connect
        # TODO: remove polling and use lock + cv
        while True:
            self.connections_lock.acquire()
            if len(self.connections) >= self.own_pid:
                self.connections_lock.release()
                break
            self.connections_lock.release()
            sleep(2)

        with self.connections_lock:
            self.accepting_new_connections = False

        self.stop_listening_for_connections()

        # connect to all guests with higher pid
        for pid, conn_info in enumerate(self.participants[self.participants.index(self.own_conn_info) + 1:]):
            while True:
                connection = self.connect(conn_info)
                if connection:
                    self.__add_connection__(conn_info, connection)
                    break
                sleep(2)

        self.__update_state__(Coordinated.State.READY)
        log.info("Connected to all guests!")

    # =====================================

    def __handle_coordinated_message__(self, pid, message):
        try:
            message_type = message[Coordinated.Message.TYPE_KEY]
            if pid == Coordinated.HOST_PID: # sent from host
                if  message_type == Coordinated.Message.RES_PARTICIPANTS:
                    self.__fill_participants__(message)
                elif message_type == Coordinated.Message.BEGIN_CONNECT_SEQ:
                    self.___sequence_connect__()
            elif self.is_host:
                if message_type == Coordinated.Message.ACK_PARTICIPANTS:
                    self.__ack_participant__(pid)

            return True

        except KeyError as e:
            print(repr(e))
            log.debug("received ill-formatted message: %s", str(message))
            return False


    # connection
    # message is a string
    def on_receive(self, sender, message):
        if not isinstance(message, dict):
            try:
                # message = pickle.loads(message.replace(b'\x03', b'\x04'))
                message = json.loads(message)
            except Exception as e:
                print(repr(e))

        log.debug("received message: %s", message)

        if Coordinated.Message.TYPE_KEY in message:
            try:
                pid = self.pids[self.get_conn_info(sender)]
                return self.__handle_coordinated_message__(pid, message)
            except KeyError as e:
                print(repr(e))
                log.debug("received message from unknown participant %s\nMessage: %s", str(sender), str(message))
                return False



# TODO's:
# 1. Use protobuf instead of constant messages
# 2. Make a base class for ConnInfo that the user must derive
#  2.1 Maybe consider removing Coordinated dependency's on ConnInfo so it just deals with IDs ..?
#       The user can make a map of ID to connection info
#  2.2 for now, should probably use a set of tuples instead of two dicts
# 3. Change terminology to use organizer instead of host
# 4. What happens if two people claim to be host???
# 5. Add ping to periodically check if not connected to any client
# 6. Make organizer into a separate class that inherits Coordinated
# 7. Change self.participants to be a dict instead of a list in case participants drop
# 8. Handle failure on connection (i.e. guest tries fails to connect to other guest)
#       rn organizer assumes everyone will successfully connect to each other
# 9. Add flag to not allow sending or receiving messages until network is connected and
#       participants will not change
#           This will change when nodes can be disconnected
