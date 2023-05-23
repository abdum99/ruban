import asyncio
from communication import ASYNCSocket
from aioconsole import ainput
from time import sleep

# async def main():
#     playid = int(input("ID: "))
#     port = int(input("PORT: "))
#     sock = ASYNCSocket(playid, port)
#     listen_task = asyncio.create_task(sock.listen())
#     print("returned from listen")
#     await listen_task

async def get_user_message():
    while True:
        line = await ainput()
        print(line)

async def print_and_wait():
    while True:
        print('.')
        await asyncio.sleep(1)

async def main():
    while True:
        m_task = asyncio.create_task(get_user_message())
        p_task = asyncio.create_task(print_and_wait())
        await asyncio.wait([m_task, p_task])
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.create_task(get_user_message())
    # loop.create_task(print_and_wait())
    # loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
