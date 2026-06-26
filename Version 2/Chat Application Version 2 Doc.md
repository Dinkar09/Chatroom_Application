# Chat Application Version 2 Documentation

## Scripts Include
### 1. chat_client_peer.py
### 2. chat_server_admin.py
### 3. chat_server_base.py

## Overview
This version introduces a peer-style chat system where the first user can start a Master Hub locally on port 8888. That hub acts as the central coordinator for virtual chatrooms, but the actual room logic is handled by the admin-based server layer.

Unlike Version 1, this version supports:
- Creating a new virtual chatroom as an Admin
- Joining an existing chatroom through Admin approval
- Broadcasting messages only to users inside the same room
- Synchronizing past room history to new members
- Handling room cleanup when users disconnect

## File Responsibilities

### 1. chat_client_peer.py
This file acts as the user-facing client application.

It provides:
- A menu to either create a new room or join an existing one
- Automatic startup of the Master Hub if one is not already running
- Connection to the hub using the CREATE or JOIN protocol
- Sending messages from the terminal to the server
- Receiving and printing incoming messages from the room

Key functions:
- start_master_hub_background(): tries to start the hub on 127.0.0.1:8888
- create_new_chatroom(): creates a new virtual room and becomes its Admin
- join_existing_chatroom(): requests access to a room and waits for approval
- receive_messages_stream(): continuously reads incoming messages from the server
- send_messages_stream(): reads user input and sends it to the hub

### 2. chat_server_admin.py
This file contains the room administration logic.

It manages:
- Room creation and room lookup
- Admin assignment for each room
- Pending join authorization requests
- Waiting for Admin approval or rejection
- Chat message broadcasting inside a room
- Cleanup when users disconnect

Key behavior:
- When a user sends CREATE, the server creates a new room and assigns that user as the Admin.
- When a user sends JOIN, the server sends an access request to the room Admin.
- The Admin can approve with /accept username or deny with /deny username.
- Once approved, the user joins the room and receives the chat history from earlier messages.

### 3. chat_server_base.py
This file is the shared foundation for the server logic.

It stores:
- self.rooms: active users grouped by room name
- self.room_histories: chat history for each room
- self.max_users_per_room: the maximum number of users allowed in a room

It also provides:
- broadcast_message(): appends messages to room history and sends them to all connected members in that room

## How to Test This

### Step 1: Start the application
Open a terminal in the project folder and run:

python chat_client_peer.py

### Step 2: Create the first room
Choose option 1.

You will be asked for:
- A room name
- An Admin username

The first user becomes the Admin of that room and the Master Hub is started automatically if it is not already running.

### Step 3: Join the room from another terminal
Open another terminal and run:

python chat_client_peer.py

Choose option 2.

Enter:
- The room name
- Your username

Your request is sent to the Admin for approval.

### Step 4: Approve or deny the request
The Admin sees a request message like:

[ACCESS REQUEST] 'username' wants to join 'room_name'. Type '/accept username' or '/deny username'

The Admin can type:
- /accept Alice
- /deny Bob

### Step 5: Start chatting
Once approved, users can send normal chat messages.

Messages are broadcast to everyone in that room, and new users receive the previous history when they join.

## How the Chat Flow Works
1. The client connects to the Master Hub.
2. The hub identifies whether the request is CREATE or JOIN.
3. For CREATE, a new room is initialized and the user becomes Admin.
4. For JOIN, an approval request is sent to the Admin.
5. After approval, the user is added to the room and can send/receive messages.
6. Every message is stored in the room history and delivered to active room members.

## How to Exit the Chat
A user can type:

quit

This closes the client connection and exits the application.

When a user disconnects:
- They are removed from the room
- A leave message is broadcast to remaining users
- If the Admin disconnects, the room is marked as no longer having an active Admin

## How to Rejoin the Chat
A user can open the app again and choose option 2 to join the same room.

If the room still exists and the Admin approves the request, the user can re-enter and receive the earlier room history.

## Notes
- The application uses port 8888 by default.
- The maximum users per room is set to 5.
- The room system is virtual, meaning users are grouped by room name instead of by a fixed physical network connection.
- The Admin controls access to the room, which makes the system more secure than open public chat access.
