import asyncio
from communication import ASYNCSocket

async def main():
    playid = int(input("MY ID: "))
    port = int(input("MY PORT: "))
    conn_port = int(input("Port to connect to: "))
    sock = ASYNCSocket(playid, port)
    listen_task = asyncio.create_task(sock.listen())
    print("returned from listen")
    conn_task = asyncio.create_task(sock.connect(playid, 'localhost', conn_port))
    await conn_task
    await listen_task


if __name__ == "__main__":
    asyncio.run(main())