# Chat Application Version 1 Documentation

## Scripts Include 
### 1. server.py
### 2. client.py

## How to test this:
1. Open a terminal and run python server.py. (This is the central platform).

2. Open 5 separate terminal windows and run python client.py in each.

3. Type a username in each window (e.g., Alice, Bob, Charlie, Dave, Eve).

4. Notice how when you connect Dave (the 4th user), his display automatically downloads the shared chat_history from the server so his screen perfectly matches Alice's and Bob's screens.

5. When Eve sends a message, it is sent to the server, and the server's broadcast() function instantly loops through the other 4 connections and pushes the text to their displays.

## How to Exit the Chat?
What the user does: They simply type quit in their terminal and press Enter (or they can just forcefully close the terminal window).

What happens behind the scenes:

On the Client: In the write_to_server function, the script actively checks what the user types. If it equals "quit", it breaks the loop, cleanly closes the network connection (writer.close()), and shuts down the app.

On the Server: The server's event loop immediately detects that the network connection was severed. It stops trying to read messages and jumps straight down to the finally: block. It safely deletes that user from the active_users dictionary and broadcasts a message to the remaining group saying "🚪 [Username] left the chat."

## How to Rejoin the Chat
What the user does: They just open their terminal and run python client.py again.

What happens behind the scenes:

On the Server: The server treats this as a brand-new, fresh connection. It doesn't actually "remember" that this specific computer was connected 5 minutes ago.

The Sync: It asks for their username again. Then, it checks the shared central platform (the self.chat_history list). It instantly downloads all the past messages to the user's screen—including anything they missed while they were gone—so they are perfectly caught up.

The Announcement: Finally, it adds them back into the active routing list and announces to the group: "👋 [Username] joined the chat!"