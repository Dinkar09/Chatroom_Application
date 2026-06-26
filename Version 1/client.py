import asyncio
import sys

async def read_from_server(reader: asyncio.StreamReader):
    """Listens for incoming messages from the platform and updates the display."""
    try:
        while True:
            data = await reader.readline()
            if not data:
                print("\n[Disconnected from server]")
                break
            # Print the incoming message to the user's display
            print(f"\r{data.decode().strip()}\n> ", end="")
    except asyncio.CancelledError:
        pass

async def write_to_server(writer: asyncio.StreamWriter):
    """Waits for the user to type a message and sends it to the platform."""
    loop = asyncio.get_running_loop()
    try:
        while True:
            # Run the blocking 'input()' function in a background thread 
            # so it doesn't freeze the asyncio event loop.
            message = await loop.run_in_executor(None, input, "> ")
            if message.lower() == 'quit':
                break
            writer.write((message + "\n").encode())
            await writer.drain()
    except asyncio.CancelledError:
        pass

async def main():
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
        
        # Start two concurrent tasks: 
        # 1. Reading messages from the server
        # 2. Waiting for the user to type messages
        read_task = asyncio.create_task(read_from_server(reader))
        write_task = asyncio.create_task(write_to_server(writer))
        
        # Wait until the user decides to quit writing
        await write_task
        
        # Cleanup
        read_task.cancel()
        writer.close()
        await writer.wait_closed()
        
    except ConnectionRefusedError:
        print("Could not connect. Is the central server running?")

if __name__ == "__main__":
    asyncio.run(main())