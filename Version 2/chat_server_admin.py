# chat_server_admin.py
import asyncio
from chat_server_base import ChatServerBase

class ChatServerAdmin(ChatServerBase):
    """Administrative server layer handling virtual room creation and authorization queues."""
    
    def __init__(self) -> None:
        super().__init__()
        self.room_admins: dict[str, asyncio.StreamWriter] = {}  # {room_name: admin_writer}
        self.pending_authorizations: dict[str, dict[str, asyncio.Future]] = {}  # {room: {user: Future}}

    async def handle_client_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Manages incoming connections, routing them to create or join virtual chatrooms."""
        room_name = None 
        client_username = "Unknown"
        try:
            # 1. Receive the initial routing protocol from the client
            routing_payload = await reader.readline()
            if not routing_payload:
                writer.close()
                return
                
            command_parts = routing_payload.decode().strip().split(" ", 2)
            if len(command_parts) < 3:
                writer.write("ERROR: Invalid routing command.\n".encode())
                writer.close()
                return

            action, room_name, client_username = command_parts[0], command_parts[1], command_parts[2]

            # ROUTE 1: CREATE A NEW ROOM

            if action == "CREATE":
                if room_name in self.rooms:
                    writer.write("DENIED: A room with this name already exists.\n".encode())
                    writer.close()
                    return
                
                # Initialize virtual room data structures
                self.rooms[room_name] = {}
                self.room_histories[room_name] = []
                self.pending_authorizations[room_name] = {}
                
                # Assign this user as the Admin of this room
                self.room_admins[room_name] = writer
                self.rooms[room_name][writer] = client_username
                
                writer.write("ACCEPTED_ADMIN\n".encode())
                await writer.drain()
                await self.broadcast_message(room_name, f"🌟 {client_username} created the room '{room_name}'.", sender_writer=writer)

            # ROUTE 2: JOIN AN EXISTING ROOM

            elif action == "JOIN":
                if room_name not in self.rooms:
                    writer.write("DENIED: Room not found.\n".encode())
                    writer.close()
                    return

                if len(self.rooms[room_name]) >= self.max_users_per_room:
                    writer.write("DENIED: The chatroom has reached its limit.\n".encode())
                    writer.close()
                    return

                # Send request to the Room Admin
                admin_writer = self.room_admins.get(room_name)
                if admin_writer:
                    try:
                        alert_msg = f"\r\n[ACCESS REQUEST] '{client_username}' wants to join '{room_name}'. Type '/accept {client_username}' or '/deny {client_username}'\n> "
                        admin_writer.write(alert_msg.encode())
                        await admin_writer.drain()
                    except Exception:
                        writer.write("DENIED: Admin is unreachable.\n".encode())
                        writer.close()
                        return
                else:
                    writer.write("DENIED: Room has no active Admin.\n".encode())
                    writer.close()
                    return

                # Create a Future and wait for Admin to approve/deny
                current_loop = asyncio.get_running_loop()
                auth_signal = current_loop.create_future()
                self.pending_authorizations[room_name][client_username] = auth_signal

                try:
                    access_granted = await auth_signal
                except asyncio.CancelledError:
                    access_granted = False

                if not access_granted:
                    writer.write("DENIED: Access request rejected by the Admin.\n".encode())
                    writer.close()
                    return

                # Access Granted: Integrate and Sync
                writer.write("ACCEPTED\n".encode())
                await writer.drain()
                self.rooms[room_name][writer] = client_username

                if self.room_histories[room_name]:
                    writer.write("--- Synchronizing Past Messages ---\n".encode())
                    for msg in self.room_histories[room_name]:
                        writer.write((msg + "\n").encode())
                    writer.write("------------------------------------\n".encode())
                    await writer.drain()

                await self.broadcast_message(room_name, f"👋 {client_username} joined the chatroom.", sender_writer=writer)

            else:
                writer.write("ERROR: Unknown action.\n".encode())
                writer.close()
                return

            # CONTINUOUS CHAT / COMMAND LOOP

            while True:
                incoming_payload = await reader.readline()
                if not incoming_payload:
                    break
                    
                raw_text = incoming_payload.decode().strip()
                
                # If the sender is the Admin of this room, check for commands
                if writer == self.room_admins.get(room_name):
                    if raw_text.startswith("/accept "):
                        target_user = raw_text.split(" ", 1)[1].strip()
                        if target_user in self.pending_authorizations[room_name]:
                            self.pending_authorizations[room_name][target_user].set_result(True)
                            del self.pending_authorizations[room_name][target_user]
                        else:
                            writer.write(f"Error: No pending request for '{target_user}'.\n".encode())
                            await writer.drain()
                        continue
                        
                    elif raw_text.startswith("/deny "):
                        target_user = raw_text.split(" ", 1)[1].strip()
                        if target_user in self.pending_authorizations[room_name]:
                            self.pending_authorizations[room_name][target_user].set_result(False)
                            del self.pending_authorizations[room_name][target_user]
                        else:
                            writer.write(f"Error: No pending request for '{target_user}'.\n".encode())
                            await writer.drain()
                        continue

                # Standard Chat Message Broadcasting
                role_tag = " (Admin)" if writer == self.room_admins.get(room_name) else ""
                formatted_message = f"[{client_username}{role_tag}]: {raw_text}"
                await self.broadcast_message(room_name, formatted_message, sender_writer=writer)

        except Exception:
            pass
        finally:
            # Cleanup on disconnect
            if room_name and room_name in self.rooms and writer in self.rooms[room_name]:
                del self.rooms[room_name][writer]
                await self.broadcast_message(room_name, f"🚪 {client_username} left the chatroom.")
                
                # If Admin leaves, the room is frozen (nobody new can join)
                if writer == self.room_admins.get(room_name):
                    await self.broadcast_message(room_name, f"⚠️ The Admin ({client_username}) has disconnected.")
                    self.room_admins.pop(room_name, None)
                    
            if not writer.is_closing():
                writer.close()