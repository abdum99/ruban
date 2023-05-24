from abc import ABC, abstractmethod
from threading import Event
from time import sleep
import json
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

# conn_info:
#  Implementation-defined; holds connection info that will be used for
#  listen_for_connections, connect, send, on_receive
#  * Should implement __str__ for helpful debugging
class Coordinated(ABC):
    # constants
    HOST_PID = 0
    CoordinatedTypeKey = "_coordinated_type"
    CoordinatedRequestParticipants = "Request Participants"
    CoordinatedResponseParticipants = "Response Participants"

    def __setup_host__(self):
        self.participants = {
            Coordinated.HOST_PID: self.own_conn_info,
        }

        self.conn_info_to_pid = {
            frozenset(self.own_conn_info.values()): Coordinated.HOST_PID
        }

        self.accepting_new_connections = True
        self.listen_for_connections(self.own_conn_info, self.host_on_new_connection)

        # TODO: change this to wait on an Event instead
        input("Press <Return> when all participants have joined\n")

        self.accepting_new_connections = False
        self.stop_listening_for_connections()

        log.debug("Sending RES_PART: %s", self.participants)
        # for each connection, send list of participants and conn_info
        # TODO: Put this in async function and await responses from users
        # confirm all users responded, otherwise send new list
        # this should prob be done in a 2PC fashion
        for pid, conn_info in self.participants.items():
            self.send(conn_info, json.dumps(
                {
                Coordinated.CoordinatedTypeKey: Coordinated.CoordinatedResponseParticipants,
                "own_pid": pid,
                "participants": self.participants
                }
            ))
    
    def __setup_guest__(self, host_conn_info):
        self.participants = {
        }

        self.conn_info_to_pid = {
            frozenset(host_conn_info.values()): Coordinated.HOST_PID
        }

        self.participants_filled = Event()

        # connect to host
        log.info("Connecting to host")
        while not self.connect(host_conn_info):
            sleep(2)
            log.info("Trying again...")
        log.info("Connected to host")

        # wait until host sends participants
        # no need for loop bc .set() is sticky
        self.participants_filled.wait()

        log.info("Received Personal ID from host: %s", str(self.own_id))
        log.info("Received list of %s participants from host", str(len(self.participants)))
        log.debug("participants: %s", str(self.participants))


    def setup(self, host_conn_info):
        if self.is_host:
            self.__setup_host__()
        else:
            if not host_conn_info:
                log.error("Must provide host connection info")
                return 
            self.__setup_guest__(host_conn_info)


    def __init__(self, is_host, own_conn_info):
        log.debug("initializing coordinated %s", "host" if is_host else "guest")
        self.is_host = is_host

        if own_conn_info == None:
            log.error("All participants must provide connection info")
            return

        self.own_conn_info = own_conn_info

    def host_on_new_connection(self, conn_info):
        log.debug("Host received new connection request: %s", str(conn_info))
        if self.accepting_new_connections:
            if conn_info in self.participants.values():
                log.error("Connection Info Already used by another participant. Pick different ones")
            else:
                self.participants[len(self.participants)] = conn_info
                log.info("Added new participant %s: %s", str(len(self.participants) - 1), str(conn_info))
        else:
            log.debug("Connection Request Refused: No Longer Accepting Connections")

    # conn_info is conn_info
    # message is a string
    def on_receive(self, conn_info, message):
        if not frozenset(conn_info.values()) in self.conn_info_to_pid:
            log.error("received message from unknown conn_info: %s", str(conn_info))
            return

        sender_pid = self.conn_info_to_pid[frozenset(conn_info.values())]

        # check if message is json, can be loaded
        # check if (from host and is participants info)
        try:
            print("received message:", message)
            m_obj = json.loads(str(message))
        except json.JSONDecodeError:
            log.debug("Could not decode message into JSON. Skipping.\nMessage: %s", str(message))
            return

        try:
            if sender_pid == HOST_PID and m_obj[CoordinatedTypeKey] == CoordinatedResponseParticipants:
                self.own_id = m_obj["own_id"]
                self.participants = m_obj["participants"]
                self.participants_filled.set() # notify waiting threads to proceed

        except KeyError:
            log.debug("message is not a formatted coordinated message.\nMessage: %s", str(m_obj))
            return


    @abstractmethod
    def listen_for_connections(self, conn_info, callback):
        pass

    @abstractmethod
    def stop_listening_for_connections(self):
        pass

    @abstractmethod
    def connect(self, conn_info) -> bool:
        pass

    @abstractmethod
    def send(conn_info, message):
        pass

# TODO's:
# 1. Use protobuf instead of constant messages
# 2. Make a base class for ConnInfo that the user must derive
#  2.1 Maybe consider removing Coordinated dependency's on ConnInfo so it just deals with IDs ..?
#       The user can make a map of ID to connection info
#  2.2 for now, should probably use a set of tuples instead of two dicts
# 3. Change terminology to use organizer instead of host
# 4. Make it more usable by separating Coordinated
#     initialization and configuration (i.e. to  start listening)
#     When you do that, it makes sense to have a separate function to configure the host
# 5. Should new participants send a request to the host first?
#     or just connect for the host to recognize them
# 6. What happens if two people claim to be host???
# 7. Add ping to periodically check if not connected to any client
