import asyncio
from Communication import ASYNCSocket
from aioconsole import ainput

# sock = None
# playid = None
# port = None
# conn_id = None
# conn_port = None

id_port_map = {
    0: 33330,
    1: 33331,
    2: 33332,
    3: 33333,
}

async def get_user_input(sock, conn_id):
    assert sock != None
    assert conn_id != None
    while True:
        line = await ainput()
        print("sending message:", line + '\n')
        await sock.send(conn_id, line + '\n')
        print("sent")

async def recv_forever(sock, conn_id):
    while True:
        await sock.recv(conn_id)

async def main():
    playid = int(input("MY ID: "))
    port = id_port_map[playid]
    conn_id = int(input("id to connect to: "))
    conn_port = id_port_map[conn_id]
    sock = ASYNCSocket(playid, port)
    conn_task = asyncio.create_task(sock.connect(conn_id, 'localhost', conn_port))
    await conn_task
    print ("connected to", conn_port)
    print(sock.connections)

    print("Ready to send messages")

    send_task = asyncio.create_task(get_user_input(sock, conn_id))
    recv_task = asyncio.create_task(recv_forever(sock, conn_id))
    await asyncio.wait([send_task, recv_task])


if __name__ == "__main__":
    asyncio.run(main())
