import socket
import threading
import time
from datetime import datetime
import traceback


class IRCServer:
    def __init__(self, host="127.0.0.1", port=9999):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.clients = {}  # {client_socket: nickname}
        self.channels = {"general": set()}  # {channel_name: set of nicknames}
        self.client_channels = {}  # {nickname: set of channels}
        self.lock = threading.Lock()

    def start(self):
        self.server_socket.listen(5)
        print(f"[*] Server started on {self.host}:{self.port}")

        while True:
            client_socket, address = self.server_socket.accept()
            print(f"[+] New connection from {address}")
            client_handler = threading.Thread(
                target=self.handle_client, args=(client_socket,)
            )
            client_handler.daemon = True
            client_handler.start()

    ## DEBUG : this not working
    def broadcast_to_channel(self, channel, message, exclude_socket=None):
        """Send message to all clients in a channel except the excluded socket"""

        print(f"[DEBUG] Broadcasting to channel: {channel}, Message: {message}")
        if channel not in self.channels:
            print(f"[DEBUG] Channel {channel} not found.")
            return

        print(f"[DEBUG] Broadcasting to channel: {channel}, Message: {message}")
        for nick in self.channels[channel]:
            print(f"[DEBUG] Trying to send to {nick}")
            client_socket = None
            for sock, nickname in self.clients.items():
                if nickname == nick:
                    client_socket = sock

                    break
            if client_socket and (
                exclude_socket is None or client_socket != exclude_socket
            ):
                try:
                    client_socket.send(message.encode("utf-8"))
                    print(f"[DEBUG] Sent message to {nick}")
                except Exception as e:
                    print(f"[ERROR] Failed to send message to {nick}: {e}")
                    self.remove_client(client_socket)

    def remove_client(self, client_socket):
        """Remove a client from all structures when they disconnect"""
        if client_socket in self.clients:
            nickname = self.clients[client_socket]

            # Remove from channels
            if nickname in self.client_channels:
                for channel in list(self.client_channels[nickname]):
                    if channel in self.channels:
                        self.channels[channel].discard(nickname)
                        # Notify others that user has left
                        self.broadcast_to_channel(
                            channel,
                            f"SYSTEM: {nickname} has left {channel}",
                            client_socket,
                        )

            # Clean up data structures
            if nickname in self.client_channels:
                del self.client_channels[nickname]
            del self.clients[client_socket]

            try:
                client_socket.close()
            except:
                pass

    def handle_client(self, client_socket):
        """Handle client connection, registration and commands"""
        # Initial registration
        client_socket.send(
            "Welcome to PyIRC Server! Please set your nickname with /nick <nickname>".encode(
                "utf-8"
            )
        )

        nickname = None

        while True:
            try:
                message = client_socket.recv(1024).decode("utf-8").strip()
                print(
                    f'Received message "{message}" from {client_socket.getpeername()}'
                )  # DEBUG

                if not message:
                    break

                # Handle commands
                if message.startswith("/"):
                    parts = message.split(" ", 1)
                    command = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""

                    if command == "/nick":
                        if not args:
                            client_socket.send(
                                "ERROR: Nickname cannot be empty".encode("utf-8")
                            )
                            continue

                        # Check if nickname is already taken
                        nickname = args
                        self.clients[client_socket] = nickname
                        self.client_channels[nickname] = set()

                        client_socket.send(
                            f"Welcome {nickname}! You have been added to #general".encode(
                                "utf-8"
                            )
                        )

                        # Add to general channel by default
                        self.channels["general"].add(nickname)
                        self.client_channels[nickname].add("general")
                        print(f'User "{nickname}" has joined the server')

                        print(self.channels["general"])
                        print(self.client_channels[nickname])

                        self.broadcast_to_channel(
                            "general",
                            f"SYSTEM: {nickname} has joined #general",
                            client_socket,
                        )

                    elif command == "/join":
                        if not nickname:
                            client_socket.send(
                                "ERROR: You must set a nickname first with /nick <nickname>".encode(
                                    "utf-8"
                                )
                            )
                            continue

                        if not args:
                            client_socket.send(
                                "ERROR: Please specify a channel to join".encode(
                                    "utf-8"
                                )
                            )
                            continue

                        # Check if channel exists
                        if args not in self.channels:
                            client_socket.send(
                                f"ERROR: Channel {args} does not exist. Only the admin can create new channels.".encode(
                                    "utf-8"
                                )
                            )
                            continue

                        # Join the channel
                        self.channels[args].add(nickname)
                        self.client_channels[nickname].add(args)

                        client_socket.send(f"You have joined {args}".encode("utf-8"))
                        self.broadcast_to_channel(
                            args,
                            f"SYSTEM: {nickname} has joined {args}",
                            client_socket,
                        )

                    elif command == "/leave" or command == "/part":
                        if not nickname:
                            client_socket.send(
                                "ERROR: You must set a nickname first".encode("utf-8")
                            )
                            continue

                        if not args:
                            client_socket.send(
                                "ERROR: Please specify a channel to leave".encode(
                                    "utf-8"
                                )
                            )
                            continue

                        if args in self.channels and nickname in self.channels[args]:
                            self.channels[args].remove(nickname)
                            self.client_channels[nickname].remove(args)

                            client_socket.send(f"You have left {args}".encode("utf-8"))
                            self.broadcast_to_channel(
                                args, f"SYSTEM: {nickname} has left {args}"
                            )
                        else:
                            client_socket.send(
                                f"ERROR: You are not in channel {args}".encode("utf-8")
                            )

                    elif command == "/list":
                        channel_list = ", ".join(
                            [
                                f"#{channel} ({len(members)} users)"
                                for channel, members in self.channels.items()
                            ]
                        )
                        client_socket.send(
                            f"Available channels: {channel_list}".encode("utf-8")
                        )

                    elif command == "/users":
                        if not args:
                            client_socket.send(
                                "ERROR: Please specify a channel".encode("utf-8")
                            )
                            continue

                        if args in self.channels:
                            users = ", ".join(sorted(self.channels[args]))
                            client_socket.send(
                                f"Users in {args}: {users}".encode("utf-8")
                            )
                        else:
                            client_socket.send(
                                f"ERROR: Channel {args} does not exist".encode("utf-8")
                            )

                    elif command == "/createchannel":
                        if not nickname:
                            client_socket.send(
                                "ERROR: You must set a nickname first".encode("utf-8")
                            )
                            continue

                        if nickname != "admin":
                            client_socket.send(
                                "ERROR: Only admin can create channels".encode("utf-8")
                            )
                            continue

                        if not args:
                            client_socket.send(
                                "ERROR: Please specify a channel name to create".encode(
                                    "utf-8"
                                )
                            )
                            continue

                        if args in self.channels:
                            client_socket.send(
                                f"ERROR: Channel {args} already exists".encode("utf-8")
                            )
                        else:
                            self.channels[args] = set()
                            client_socket.send(
                                f"Channel {args} created. Use /join {args} to join it.".encode(
                                    "utf-8"
                                )
                            )

                    elif command == "/msg":
                        if not nickname:
                            client_socket.send(
                                "ERROR: You must set a nickname first".encode("utf-8")
                            )
                            continue

                        parts = args.split(" ", 1)
                        if len(parts) < 2:
                            client_socket.send(
                                "ERROR: Usage: /msg <nickname> <message>".encode(
                                    "utf-8"
                                )
                            )
                            continue

                        target_nick, pm_message = parts

                        target_socket = None
                        for sock, nick in self.clients.items():
                            if nick == target_nick:
                                target_socket = sock
                                break

                        if target_socket:
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            target_socket.send(
                                f"[{timestamp}] PRIVATE from {nickname}: {pm_message}".encode(
                                    "utf-8"
                                )
                            )
                            client_socket.send(
                                f"[{timestamp}] PRIVATE to {target_nick}: {pm_message}".encode(
                                    "utf-8"
                                )
                            )
                        else:
                            client_socket.send(
                                f"ERROR: User {target_nick} not found".encode("utf-8")
                            )

                    elif command == "/help":
                        help_text = (
                            "Available commands:\n"
                            "/nick <nickname> - Set your nickname\n"
                            "/join <channel> - Join a channel\n"
                            "/leave <channel> - Leave a channel\n"
                            "/list - List available channels\n"
                            "/users <channel> - List users in a channel\n"
                            "/msg <nickname> <message> - Send a private message\n"
                            "/help - Show this help message\n"
                            "/quit - Disconnect from the server\n"
                        )
                        if nickname == "admin":
                            help_text += "/createchannel <channel> - Create a new channel (admin only)\n"

                        client_socket.send(help_text.encode("utf-8"))

                    elif command == "/quit":
                        client_socket.send("Goodbye!".encode("utf-8"))
                        break

                    else:
                        client_socket.send(
                            f"ERROR: Unknown command {command}".encode("utf-8")
                        )

                # Regular message - send to current channel
                else:
                    if not nickname:
                        client_socket.send(
                            "ERROR: You must set a nickname first with /nick <nickname>".encode(
                                "utf-8"
                            )
                        )
                        continue

                    # Find the active channel
                    target_channel = None

                    # Parse channel from message if format is "#channel message"
                    if message.startswith("#") and " " in message:
                        parts = message.split(" ", 1)
                        channel_name = parts[0][1:]  # Remove the # character
                        msg_content = parts[1]

                        if (
                            channel_name in self.channels
                            and nickname in self.channels[channel_name]
                        ):
                            target_channel = channel_name
                            message = msg_content

                    # If no explicit channel, find a joined channel
                    if not target_channel:
                        joined_channels = self.client_channels.get(nickname, set())
                        if joined_channels:
                            target_channel = next(iter(joined_channels))
                        else:
                            client_socket.send(
                                "ERROR: You haven't joined any channels".encode("utf-8")
                            )
                            continue

                    timestamp = datetime.now().strftime("%H:%M:%S")
                    formatted_message = (
                        f"[{timestamp}] [{target_channel}] {nickname}: {message}"
                    )

                    # Send to client's own socket to confirm message
                    client_socket.send(formatted_message.encode("utf-8"))

                    # Broadcast to channel
                    self.broadcast_to_channel(
                        target_channel, formatted_message, client_socket
                    )

            except Exception as e:
                print(f"Error handling client {nickname}: {e}")
                traceback.print_exc()  # Add traceback to see full error details
                break

        self.remove_client(client_socket)


if __name__ == "__main__":
    server = IRCServer()
    print(
        "IRC Server started. The first client to connect with nickname 'admin' will have admin privileges"
    )
    server.start()
