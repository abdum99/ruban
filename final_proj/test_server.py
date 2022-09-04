import asyncio
from communication import ASYNCSocket
from aioconsole import ainput

sock = None
playid = None
port = None
conn_id = None
conn_port = None

id_port_map = {
    0: 33330,
    1: 33331,
    2: 33332,
    3: 33333,
}

async def main():
    playid = int(input("ID: "))
    port = id_port_map[playid]
    sock = ASYNCSocket(playid, port)
    conn_port = id_port_map[conn_id]
    listen_task = asyncio.create_task(sock.listen())
    await listen_task
    send_task = asyncio.create_task(get_user_input())
    await asyncio.wait([listen_task, send_task])


if __name__ == "__main__":
    asyncio.run(main())
