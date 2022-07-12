import asyncio
from communication import ASYNCSocket

async def main():
    playid = int(input("ID: "))
    port = int(input("PORT: "))
    sock = ASYNCSocket(playid, port)
    listen_task = asyncio.create_task(sock.listen())
    print("returned from listen")
    await listen_task


if __name__ == "__main__":
    asyncio.run(main())