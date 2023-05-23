import asyncio

class SomeClass:
    def __init__(self):
        self.count = 0
        self.srv = None

    async def client_connected(self, reader, writer):
        print("Client connected!")
        writer.write("Hello client!\n".encode())
        await writer.drain()
        print("sent message")
        self.count += 1
        if self.count >= 2:
            print("Two connections. Closing server!")
            self.srv.close()
            await self.srv.wait_closed()
            print("Closed server. Is reader/writer still valid?")
            writer.write("Hello client!\n".encode())
            await writer.drain()
            print("sent message")


    async def main(self):
        self.srv = await asyncio.start_server(
            self.client_connected, 'localhost', 33333)
        await self.srv.start_serving()
        print("Finished Waiting!")
        input("<RETURN>")
        async with self.srv:
            await self.srv.serve_forever()
        while True:
            pass

if __name__ == '__main__':
    c = SomeClass()
    asyncio.run(c.main())

