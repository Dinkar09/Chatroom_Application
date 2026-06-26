# chat_server_base.py
import asyncio

class ChatServerBase:
    """Foundational server class managing the shared chat platform data and streaming mechanics."""
    
    def __init__(self) -> None:
        # Core data platform attributes
        self.active_connections: dict[asyncio.StreamWriter, str] = {}  # Maps network writer sockets to usernames
        self.message_history: list[str] = []                          # Stores sequential timeline data
        self.max_connection_limit: int = 5                             # Total allowable participants (Admin + Clients)

    async def broadcast_message(self, message: str, sender_writer: asyncio.StreamWriter = None) -> None:
        """Appends message to history timeline and safely pushes it out to all active terminal streams."""
        self.message_history.append(message)
        
        # Clean terminal output management: clear line, print message, restore prompt
        print(f"\r{message}\n> ", end="", flush=True)
        
        for network_writer in list(self.active_connections.keys()):
            if network_writer != sender_writer:
                try:
                    network_writer.write((message + "\n").encode())
                    await network_writer.drain()
                except (ConnectionResetError, RuntimeError):
                    # Fail silently during broadcast if connection dropped abruptly
                    pass