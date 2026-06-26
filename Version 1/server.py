import asyncio

class ChatServer:
    def __init__(self):
        # The Shared Data Platform: 
        # Stores active users {writer_object: username}
        self.active_users = {} 
        # Stores the chat history to sync new displays
        self.chat_history = [] 

    async def broadcast(self, message: str, sender_writer=None):
        """Sends a message to all connected displays."""
        self.chat_history.append(message) # Save to central platform
        print(f"[SERVER LOG] {message}")
        
        for writer in self.active_users:
            # Send to everyone except the person who just sent it 
            # (their local display already shows what they typed)
            if writer != sender_writer:
                writer.write((message + "\n").encode())
                await writer.drain()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Manages a single display's connection to the platform."""
        # 1. Ask for a username
        writer.write("Enter your username: ".encode())
        await writer.drain()
        username_data = await reader.readline()
        username = username_data.decode().strip()

        self.active_users[writer] = username

        # 2. Sync the new display with the shared data (Chat History)
        if self.chat_history:
            writer.write("--- Previous Chat History ---\n".encode())
            for old_msg in self.chat_history:
                writer.write((old_msg + "\n").encode())
            await writer.drain()
            writer.write("-----------------------------\n".encode())

        # 3. Announce new user to the group
        await self.broadcast(f"👋 {username} joined the chat!", sender_writer=writer)

        try:
            # 4. Listen for new messages from this user
            while True:
                data = await reader.readline()
                if not data:
                    break # User disconnected
                
                message = data.decode().strip()
                formatted_message = f"[{username}]: {message}"
                
                # Send the message to the other 4 displays
                await self.broadcast(formatted_message, sender_writer=writer)
                
        except asyncio.CancelledError:
            pass
        finally:
            # Cleanup when a display disconnects
            del self.active_users[writer]
            await self.broadcast(f"🚪 {username} left the chat.")
            writer.close()
            await writer.wait_closed()

async def main():
    server_app = ChatServer()
    server = await asyncio.start_server(server_app.handle_client, '127.0.0.1', 8888)
    
    print("Central Chat Platform running on 127.0.0.1:8888...")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())