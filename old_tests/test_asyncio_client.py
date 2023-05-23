import asyncio

async def main():
    print("About to open connection")
    reader, writer = await asyncio.open_connection(
        'localhost', 33333)

    print("Opened connection")

    while True:
        message = await reader.readline()
        print("GOT:", message.decode())

if __name__ == '__main__':
    asyncio.run(main())

