# chat_server_admin.py
import asyncio
import sys
from chat_server_base import ChatServerBase

class ChatServerAdmin(ChatServerBase):
    """Administrative server layer handling entry verification and manual authorization queues."""
    
    def __init__(self) -> None:
        super().__init__()
        self.pending_authorizations: dict[str, asyncio.Future] = {}  # Tracks {username: approval_future_signal}
        self.admin_username: str = ""

    async def handle_client_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Manages lifecycle of an incoming network stream and enforces access authorization rules."""
        
        # 1. Capacity Guardrail (Admin occupies 1 slot, leaving space for max_connections - 1)
        if len(self.active_connections) >= self.max_connection_limit - 1:
            writer.write("DENIED: The chatroom has reached its limit of 5 participants.\n".encode())
            await writer.drain()
            writer.close()
            return

        # 2. Extract Client Identity
        writer.write("IDENTITY_REQUEST\n".encode())
        await writer.drain()
        identity_payload = await reader.readline()
        client_username = identity_payload.decode().strip()

        # 3. Queue Authorization Request
        print(f"\r\n[ACCESS REQUEST] '{client_username}' wants to join. Action required: '/accept {client_username}' or '/deny {client_username}'\n> ", end="", flush=True)
        
        current_event_loop = asyncio.get_running_loop()
        authorization_signal = current_event_loop.create_future()
        self.pending_authorizations[client_username] = authorization_signal

        try:
            # Task pauses execution status until Admin updates the Future state
            access_granted = await authorization_signal  
        except asyncio.CancelledError:
            access_granted = False

        # 4. Evaluate Authorization Result
        if not access_granted:
            writer.write("DENIED: Access request rejected by the Admin.\n".encode())
            await writer.drain()
            writer.close()
            return

        # 5. Integrate Client into the Active Session Pool
        writer.write("ACCEPTED\n".encode())
        await writer.drain()
        self.active_connections[writer] = client_username

        # 6. Synchronize History Timeline to Client Screen
        if self.message_history:
            writer.write("--- Synchronizing Past Messages ---\n".encode())
            for historic_message in self.message_history:
                writer.write((historic_message + "\n").encode())
            writer.write("------------------------------------\n".encode())
            await writer.drain()

        await self.broadcast_message(f"👋 {client_username} has entered the chatroom.", sender_writer=writer)

        try:
            # Continuous network parsing loop for the connected client
            while True:
                incoming_payload = await reader.readline()
                if not incoming_payload:
                    break
                formatted_message = f"[{client_username}]: {incoming_payload.decode().strip()}"
                await self.broadcast_message(formatted_message, sender_writer=writer)
        finally:
            if writer in self.active_connections:
                del self.active_connections[writer]
                await self.broadcast_message(f"🚪 {client_username} has left the chatroom.")
            writer.close()

    async def listen_to_admin_commands(self) -> None:
        """Asynchronously monitors local terminal input for chat messages or command logic execution."""
        current_event_loop = asyncio.get_running_loop()
        while True:
            raw_input = await current_event_loop.run_in_executor(None, input, "")
            sanitized_input = raw_input.strip()
            
            # Command Router Interceptor
            if sanitized_input.startswith("/accept "):
                target_user = sanitized_input.split(" ", 1)[1].strip()
                if target_user in self.pending_authorizations:
                    self.pending_authorizations[target_user].set_result(True)
                    del self.pending_authorizations[target_user]
                else:
                    print(f"Error: No pending request found for '{target_user}'.\n> ", end="")
                continue
                
            elif sanitized_input.startswith("/deny "):
                target_user = sanitized_input.split(" ", 1)[1].strip()
                if target_user in self.pending_authorizations:
                    self.pending_authorizations[target_user].set_result(False)
                    del self.pending_authorizations[target_user]
                else:
                    print(f"Error: No pending request found for '{target_user}'.\n> ", end="")
                continue

            if sanitized_input.lower() == 'quit':
                print("Terminating host environment...")
                sys.exit(0)
                
            admin_chat_message = f"[{self.admin_username} (Admin)]: {sanitized_input}"
            await self.broadcast_message(admin_chat_message)

    async def start_admin_host(self) -> None:
        """Spawns the TCP networking stream server and registers the local admin loop."""
        self.admin_username = input("Enter your Admin username: ").strip()
        tcp_network_server = await asyncio.start_server(self.handle_client_connection, '127.0.0.1', 8888)
        
        print(f"Chatroom hosted successfully on 127.0.0.1:8888! (Room Limit: {self.max_connection_limit} total users)")
        print("Awaiting incoming join requests...")
        print("-----------------------------------------------------------------------------------------")
        
        async with tcp_network_server:
            await asyncio.gather(
                tcp_network_server.serve_forever(),
                self.listen_to_admin_commands()
            )