# PyIRC

## Fixes To be made

    - Currently we can join multiple channels but can only text in #general
    - Some auth issues
    - Need better way to implement the admin system # Authorizations
    - Better interface for the system

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Contributing](../CONTRIBUTING.md)

## About <a name = "about"></a>

PyIRC is a simple IRC (Internet Relay Chat) server and client implementation in Python. It allows users to connect to a server, join channels, and communicate with each other in real-time. The project demonstrates basic networking, threading, and socket programming concepts in Python.

## Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.

### Prerequisites

You need to have Python installed on your machine. You can download it from [python.org](https://www.python.org/).

### Installing

1. Clone the repository:

   ```
   git clone https://github.com/abhishek-03113/PyIRC.git
   cd PyIRC
   ```

2. (Optional) Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages (if any):

   ```
   pip install -r requirements.txt
   ```

4. Run the server:

   ```
   python server.py
   ```

5. Run the client:
   ```
   python client.py
   ```

End with an example of getting some data out of the system or using it for a little demo.

## Usage <a name = "usage"></a>

1. Start the server by running `python server.py`.
2. Start the client by running `python client.py`.
3. Follow the on-screen instructions to set your nickname and join channels.
4. Use commands like `/nick`, `/join`, `/leave`, `/msg`, etc., to interact with the server and other users.

For a list of available commands, type `/help` in the client.
