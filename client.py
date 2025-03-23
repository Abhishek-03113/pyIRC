import socket
import threading
import sys
import time
import os


class IRCClient:
    def __init__(self, host="127.0.0.1", port=9999):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nickname = None
        self.current_channel = None
        self.running = False

    def connect(self):
        """Connect to the IRC server"""
        try:
            self.socket.connect((self.host, self.port))
            self.running = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def receive_messages(self):
        """Thread function to receive and display messages from the server"""
        while self.running:
            try:
                message = self.socket.recv(1024).decode("utf-8")
                print(f'\nreceived message "{message}"')  # Debug
                if not message:
                    print("\nDisconnected from server")
                    self.running = False
                    break

                # Clear the current line to display message cleanly
                sys.stdout.write("\r" + " " * 80 + "\r")
                print(message)

                # Update current channel if we joined one
                if "You have joined" in message:
                    try:
                        self.current_channel = message.split("You have joined ")[1].strip()
                    except:
                        pass

                # Update nickname if we set one
                if message.startswith("You are now known as "):
                    try:
                        self.nickname = message.split("You are now known as ")[1].strip()
                    except:
                        pass

                # Extract nickname from welcome message
                if message.startswith("Welcome ") and "!" in message:
                    try:
                        self.nickname = message.split("Welcome ")[1].split("!")[0].strip()
                    except:
                        pass

                # Show prompt again
                sys.stdout.write("> ")
                sys.stdout.flush()

            except Exception as e:
                print(f"\nError receiving message: {e}")
                self.running = False
                break

    def send_command(self, command):
        """Send a command to the server"""
        try:
            self.socket.send(command.encode("utf-8"))
            print(f'sent command "{command}"')

            # Update local state based on commands
            if command.startswith("/nick "):
                self.nickname = command.split(" ", 1)[1]
            elif command.startswith("/join "):
                self.current_channel = command.split(" ", 1)[1]
            elif command.startswith("/leave ") or command.startswith("/part "):
                channel = command.split(" ", 1)[1]
                if channel == self.current_channel:
                    self.current_channel = None

        except Exception as e:
            print(f"Error sending command: {e}")
            self.running = False

    def start(self):
        """Start the IRC client"""
        if not self.connect():
            return

        # Start a thread to receive messages
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        # Main input loop
        try:
            while self.running:
                user_input = input("> ")

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if user_input.lower() == "/quit":
                        self.send_command("/quit")
                        self.running = False
                        break
                    else:
                        self.send_command(user_input)
                else:
                    # If message doesn't start with /, it's a regular message
                    self.send_command(user_input)

        except KeyboardInterrupt:
            print("\nDisconnecting...")

        finally:
            self.socket.close()
            print("Disconnected from server")


def display_help():
    """Display help information"""
    help_text = """
    === PyIRC Client ===
    
    Connect to an IRC server and start chatting!
    
    Available commands:
    /nick <nickname> - Set your nickname
    /join <channel> - Join a channel
    /leave <channel> - Leave a channel
    /list - List available channels
    /users <channel> - List users in a channel
    /msg <nickname> <message> - Send a private message
    /help - Show this help message
    /quit - Disconnect from the server
    
    Admin commands:
    /createchannel <channel> - Create a new channel (admin only)
    
    To send a message to your current channel, just type the message.
    To send a message to a specific channel, use #channel message
    """
    print(help_text)


if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    print("=== PyIRC Client ===")
    print("Type /help for a list of commands")

    # Get server details
    server = input("Server address (default: 127.0.0.1): ")
    server = server if server else "127.0.0.1"

    port = input("Port (default: 9999): ")
    port = int(port) if port else 9999

    # Create and start client
    client = IRCClient(server, port)
    client.start()
