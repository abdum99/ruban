# Ruban: Mutually-distrustful Turn-based P2P Transactions
Ruban is a P2P Counterable Transaction System inspired by the classic Two Phase Commit (2PC) Protocol. It's written as a static Python library that is meant to be implemented for any communication protocol that allows multiple peers to be connected to each other independently.

Currently it follows a basic round-robin assignment to elect leaders. In the system, a peer can propose an offer to all other participants in the system which they can independently accept or counter. Counters can be stacked to create a chain and reach a final state that all participants accept.

All participants are mutually distrustful and we use the P2P nature of the system and public-key cryptography to to introduce the concept of Contesting to provide majority-based authenticity and security without a large traffic overhead.

> **Warning**
> This is a WIP. Please refer to the  [paper](./doc/paper/ruban-1_0.pdf) for more info.

## Guarantees
Ruban provides the following guarantees:
- **Extensibility:**
Chains can be recursively countered.
- **Authenticity:**
Peers should be confident that all other participants endorsed a chain before committing it.
- **Scalability:**
Traffic (packets sent) should grow in O(n) where n is the number of nodes.
- **Byzantine Fault Tolerance:**
The system should be able to gracefully recover from a node failing.
- **Liveness through Maliciuosness:**
A malicious player does not cause the game to halt for honest participants.
- **Proposer Autonomy:**
The decision for which counter to choose, if more than one is available, belongs to the original proposer.
- **Architecture and Protocol Agnositicism:**
The system should be easily extensible to other session layer including, e.g., Bluetooth, pure POSIX Sockets, MQTT.

## Running
> **Warning**
> This is a WIP. Please refer to the [paper](./doc/paper/ruban-1_0.pdf) for more info.

To install, make sure you have `python3.7+`
```
git clone git@github.com:amohamdy99/ruban.git
cd ruban
python3 -m pip install p2pnetwork
```
Then to run a peer
```
python3 tests/test_peer.py
```
You can run many peers. One peer should have ID 0 to serve as the host
> **Warning**
> Make sure one peer has ID 0

> **Note**
> This will be changed in favor of an ad-hoc network model where participants can connect to any of the other participants post game initiation.
