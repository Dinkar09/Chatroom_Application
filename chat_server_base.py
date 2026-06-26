# chat_server_base.py
import asyncio

class ChatServerBase:
    """Foundational server class managing the shared chat platform data and streaming mechanics."""
    
    def __init__(self) -> None:
        # Shared Platform Data Structures mapping room names to their specific data
        # Format: { "room_name": { writer_object: "username" } }
        self.rooms: dict[str, dict[asyncio.StreamWriter, str]] = {}  
        # Format: { "room_name": ["message 1", "message 2"] }
        self.room_histories: dict[str, list[str]] = {}               
        self.max_users_per_room: int = 5

    async def broadcast_message(self, room_name: str, message: str, sender_writer: asyncio.StreamWriter = None) -> None:
        """Appends message to the specific room's timeline and pushes it to active terminal streams in that room."""
        if room_name not in self.rooms:
            return

        self.room_histories[room_name].append(message)
        
        # Clean terminal output management
        print(f"\r{message}\n> ", end="", flush=True)
        
        for network_writer in list(self.rooms[room_name].keys()):
            if network_writer != sender_writer:
                try:
                    network_writer.write((message + "\n").encode())
                    await network_writer.drain()
                except (ConnectionResetError, RuntimeError, BrokenPipeError):
                    pass