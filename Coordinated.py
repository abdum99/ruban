from abc import ABC, abstractmethod
from threading import Event
from time import sleep
import pickle
import logging

logging.basicConfig(level=logging.DEBUG)
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
    # constants
    HOST_PID = 0
    TypeKey = "_coordinated_type"
    RequestParticipants = "Request Participants"
    ResponseParticipants = "Response Participants"

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

    # These methods are already implemented. You should not override
    def __add_participant__(self, connection):
        # should lock here
        participant = self.get_conn_info(connection)
        pid = len(self.participants)
        self.pids[participant] = pid 
        self.participants.append(participant)
        log.info("Added new participant %s: %s", str(pid), str(participant))
        return participant

    def __add_connection__(self, participant, connection):
        self.connections[participant] = connection

    def __send__(self, participant, message):
        try:
            connection = self.connections[participant]
        except KeyError as e:
            log.error("Trying to send message to participant with no open connection: %s", str(participant))
            return

        self.send(connection, pickle.dumps(message).replace(b'\x04', b'\x03'))

    def __setup_host__(self):
        self.own_pid = Coordinated.HOST_PID

        # <pids> and <participants> are common across all nodes
        # participants id's
        # <pids>: { conn_info --> PID }
        self.pids = {
            self.get_conn_info(self): Coordinated.HOST_PID
        }

        # participant connection info
        # <participants>: [ conn_info ]
        self.participants = [ self.get_conn_info(self) ]

        # connections are unique to each node and not sent by host
        self.connections = {} # no connection to self

        self.accepting_new_connections = True
        self.listen_for_connections(self.__host_on_new_connection__)

        # TODO: change this to wait on an Event instead
        input("Press <Return> when all participants have joined\n")

        self.accepting_new_connections = False
        self.stop_listening_for_connections()

        log.debug("Sending RES_PART: %s", range(len(self.participants)))
        # for each connection, send list of participants and connections
        # TODO: Put this in async function and await responses from users
        # confirm all users responded, otherwise send new list
        # this should prob be done in a 2PC fashion
        for participant, pid in self.pids.items():
            if pid == 0: # do not send participants to host
                continue
            message = {
                Coordinated.TypeKey: Coordinated.ResponseParticipants,
                "sender_pid": self.own_pid,
                "own_pid": pid,
                "participants": self.participants,
                "pids": self.pids,
                }
            self.__send__(participant, message)

    
    def __setup_guest__(self, host_connection):
        # add host as participant
        self.pids = {
            host_connection: Coordinated.HOST_PID
        }
        # participant connection info
        self.participants = [ host_connection ]

        self.connections = {}

        self.participants_filled = Event()

        # self.listen_for_connections(self.__guest_on_new_connection__)

        # connect to host
        log.info("Connecting to host")
        host = None
        while True:
            host = self.connect(host_connection)
            if host:
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


    def setup(self, host_connection = None):
        if self.is_host:
            self.__setup_host__()
        else:
            if not host_connection:
                log.error("Must provide host connection")
                return 
            self.__setup_guest__(host_connection)

    def __init__(self, is_host):
        log.debug("initializing coordinated %s", "host" if is_host else "guest")
        self.is_host = is_host
        self.own_conn_info = self.get_conn_info(self)


    def __host_on_new_connection__(self, connected_node):
        log.debug("Host received new connection request: %s", str(connected_node))
        if self.accepting_new_connections:
            if connected_node in self.pids:
                log.error("Connection Info Already used by another participant. Pick different parameters")
            else:
                participant = self.__add_participant__(connected_node)
                self.__add_connection__(participant, connected_node)
                self.__send__(participant, {Coordinated.TypeKey: "You're IN"})

        else:
            log.debug("Connection Request Refused: No Longer Accepting Connections.")


    def __guest_on_new_connection__(self, connected_node):
        log.info("Guest received new connection: %s", str(connected_node))


    # connection
    # message is a string
    def on_receive(self, sender, message):
        log.debug("received message: %s", str(message))

        try:
            message = pickle.loads(message.replace(b'\x03', b'\x04'))
        except Error as e:
            print(repr(e))
            return

        try:
            pid = self.pids[self.get_conn_info(sender)]
            assert(pid == message["sender_pid"])
            try:
                if (pid == Coordinated.HOST_PID and
                    message[Coordinated.TypeKey] == Coordinated.ResponseParticipants):
                    self.own_pid = message["own_pid"]
                    self.participants = message["participants"]
                    self.pids = message["pids"]

                    self.participants_filled.set() # notify waiting threads to proceed
            except KeyError as e:
                print(repr(e))
                log.debug("received ill-formatted message: %s", str(message))
                return

        except KeyError as e:
            print(repr(e))
            log.debug("received message from unknown participant %s\nMessage: %s", str(sender), str(message))
            return


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
