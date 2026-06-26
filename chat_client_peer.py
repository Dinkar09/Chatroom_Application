# chat_client_peer.py
import asyncio
import sys
from chat_server_base import ChatServerBase
from chat_server_admin import ChatServerAdmin

class ChatClientPeer(ChatServerAdmin, ChatServerBase):
    """Client class executing remote stream processing routines, inheriting node hosting capabilities."""
    
    def __init__(self) -> None:
        # Python Method Resolution Order (MRO) correctly cascades class setup
        super().__init__()

    async def receive_messages_stream(self, reader: asyncio.StreamReader) -> None:
        """Listens continuously to incoming server transmissions and formats the terminal output window."""
        while True:
            network_payload = await reader.readline()
            if not network_payload:
                print("\n[ALERT] Connection to the central chatroom was severed.")
                sys.exit(0)
            print(f"\r{network_payload.decode().strip()}\n> ", end="")

    async def send_messages_stream(self, writer: asyncio.StreamWriter) -> None:
        """Captures local peripheral keystrokes and dispatches them down the active outbound network pipe."""
        current_event_loop = asyncio.get_running_loop()
        while True:
            user_input = await current_event_loop.run_in_executor(None, input, "> ")
            sanitized_input = user_input.strip()
            
            if sanitized_input.lower() == 'quit':
                writer.close()
                sys.exit(0)
                
            writer.write((sanitized_input + "\n").encode())
            await writer.drain()

    async def join_existing_chatroom(self) -> None:
        """Establishes connection to an active network socket and negotiates the entry verification routine."""
        client_username = input("Enter your username: ").strip()
        
        try:
            reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
            
            # Step 1: Handshake and authentication challenge handling
            await reader.readline() 
            writer.write((client_username + "\n").encode())
            await writer.drain()
            print("Access request transmitted. Awaiting Admin authorization response...")
            
            # Step 2: Evaluate access stream confirmation
            handshake_response_payload = await reader.readline()
            handshake_response = handshake_response_payload.decode().strip()
            
            if handshake_response.startswith("DENIED"):
                print(f"\n[ACCESS DENIED] Connection closed by remote node: {handshake_response}")
                writer.close()
                return
                
            print("\n[ACCESS GRANTED] You have successfully entered the chatroom!")
            
            # Step 3: Concurrently launch asymmetric read/write loops
            await asyncio.gather(
                self.receive_messages_stream(reader),
                self.send_messages_stream(writer)
            )
            
        except ConnectionRefusedError:
            print("\n[ERROR] Connection failed. Ensure the remote Admin host is running and reachable.")

# ==========================================
# APPLICATION INITIALIZER / ENGINE RUNNER
# ==========================================
async def main() -> None:
    print("=== HYBRID P2P ASYNC CHAT COMPONENT ===")
    print("1. Initialize Network Host Environment (Host as Admin)")
    print("2. Request Connection to Existing Network Host (Join Chatroom)")
    user_selection = input("Select operation mode (1 or 2): ").strip()
    
    # Initialize unified component instance mapping to target execution parameters
    peer_node = ChatClientPeer()
    
    if user_selection == '1':
        await peer_node.start_admin_host()
    elif user_selection == '2':
        await peer_node.join_existing_chatroom()
    else:
        print("Error: Invalid application routing choice specified.")

if __name__ == "__main__":
    # Optimize event loops for explicit cross-platform network performance criteria
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication lifecycle terminated via manual interrupt.")