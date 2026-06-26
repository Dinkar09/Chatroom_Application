# chat_client_peer.py
import asyncio
import sys
from chat_server_admin import ChatServerAdmin

class ChatClientPeer(ChatServerAdmin):
    """Client node capable of interacting with the Master Hub or becoming the Hub itself."""
    
    def __init__(self) -> None:
        super().__init__()
        self.host_ip = '127.0.0.1'
        self.host_port = 8888

    async def receive_messages_stream(self, reader: asyncio.StreamReader) -> None:
        """Listens continuously to incoming server transmissions."""
        while True:
            network_payload = await reader.readline()
            if not network_payload:
                print("\n[ALERT] Connection severed by the Master Hub.")
                sys.exit(0)
            print(f"\r{network_payload.decode().strip()}\n> ", end="", flush=True)

    async def send_messages_stream(self, writer: asyncio.StreamWriter) -> None:
        """Captures local peripheral keystrokes and dispatches them to the Master Hub."""
        current_event_loop = asyncio.get_running_loop()
        while True:
            user_input = await current_event_loop.run_in_executor(None, input, "> ")
            sanitized_input = user_input.strip()
            
            if sanitized_input.lower() == 'quit':
                writer.close()
                sys.exit(0)
                
            writer.write((sanitized_input + "\n").encode())
            await writer.drain()

    async def start_master_hub_background(self):
        """Attempts to bind port 8888. If successful, runs the Hub silently in the background."""
        try:
            hub_server = await asyncio.start_server(self.handle_client_connection, self.host_ip, self.host_port)
            print("[SYSTEM] Successfully initialized Master Hub on 127.0.0.1:8888.")
            # Starts the server but does not block the client UI
            asyncio.create_task(hub_server.serve_forever()) 
        except OSError:
            # Error 10048 naturally triggers here. We catch it and route to the existing hub!
            print("[SYSTEM] Master Hub already detected on network. Routing request to existing Hub...")

    async def create_new_chatroom(self) -> None:
        """Option 1: Spawns the Hub (if needed) and negotiates a new virtual room creation."""
        room_name = input("Enter a name for your new Chatroom: ").strip()
        client_username = input("Enter your Admin username: ").strip()
        
        # Step 1: Try to spawn the background Hub
        await self.start_master_hub_background()
        
        # Step 2: Connect to the Hub as a client to set up the room
        try:
            await asyncio.sleep(0.1) # Micro-pause to let the background hub bind
            reader, writer = await asyncio.open_connection(self.host_ip, self.host_port)
            
            # Send protocol: Action, Room, User
            writer.write(f"CREATE {room_name} {client_username}\n".encode())
            await writer.drain()
            
            response = (await reader.readline()).decode().strip()
            
            if response == "ACCEPTED_ADMIN":
                print(f"\n[SUCCESS] Virtual Room '{room_name}' created. You are the Admin.")
                print("Type messages normally. Use '/accept [name]' or '/deny [name]' to authorize users.")
                print("-" * 60)
                await asyncio.gather(
                    self.receive_messages_stream(reader),
                    self.send_messages_stream(writer)
                )
            else:
                print(f"\n[ERROR] {response}")
                writer.close()
                
        except ConnectionRefusedError:
            print("\n[FATAL ERROR] Could not connect to Master Hub.")

    async def join_existing_chatroom(self) -> None:
        """Option 2: Connects to Hub and requests authorization to enter a specific room."""
        room_name = input("Enter the name of the Chatroom you want to join: ").strip()
        client_username = input("Enter your username: ").strip()
        
        try:
            reader, writer = await asyncio.open_connection(self.host_ip, self.host_port)
            
            # Send protocol: Action, Room, User
            writer.write(f"JOIN {room_name} {client_username}\n".encode())
            await writer.drain()
            
            print("Access request transmitted. Awaiting Admin authorization response...")
            response = (await reader.readline()).decode().strip()
            
            if response == "ACCEPTED":
                print("\n[ACCESS GRANTED] You have successfully entered the chatroom!")
                await asyncio.gather(
                    self.receive_messages_stream(reader),
                    self.send_messages_stream(writer)
                )
            else:
                print(f"\n[ACCESS DENIED] {response}")
                writer.close()
                
        except ConnectionRefusedError:
            print("\n[ERROR] Master Hub not found. Someone must select Option 1 first to initialize the Hub.")

# APPLICATION INITIALIZER / ENGINE RUNNER

async def main() -> None:
    print("=== MASTER HUB P2P ASYNC CHAT ===")
    print("1. Create a New Virtual Chatroom (Become Admin)")
    print("2. Join an Existing Virtual Chatroom")
    user_selection = input("Select operation mode (1 or 2): ").strip()
    
    peer_node = ChatClientPeer()
    
    if user_selection == '1':
        await peer_node.create_new_chatroom()
    elif user_selection == '2':
        await peer_node.join_existing_chatroom()
    else:
        print("Error: Invalid application routing choice specified.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication lifecycle terminated via manual interrupt.")