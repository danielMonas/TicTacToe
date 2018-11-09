import socket
import struct

# CODES:
QUIT = "1"
LOGIN_FAIL = "2"
LOGIN_SUCCESS = "3"
MATCH_READY = "4"
TURN = "5"
END_GAME = "6"
TIE = "7"
RESET = "8"
LEN_SIZE = 4


class Communicator():
    def __init__(self):
        # Connecting to server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("localhost", 12345))

    def login(self, name):
        """ Establishing connection to the server, and selecting player name """
        self.send(LOGIN_SUCCESS, name)
        return self.receive()[0]

    def receive(self):
        """ Receiving a message from the server. If it fails, client is disconnected """
        try:
            msg_len = int(self.sock.recv(LEN_SIZE).decode("utf8"))
            code = self.sock.recv(LEN_SIZE).decode("utf8").lstrip("0")
            data = self.sock.recv(msg_len-LEN_SIZE).decode("utf8")
        except socket.error:
            code, data = QUIT, ""
        return code, data

    def send(self, code, data=""):
        """Sending message to server according to the server message protocol """
        data = code.rjust(LEN_SIZE, '0') + data
        self.sock.send(struct.pack("!I", len(data)))
        self.sock.send(bytes(data, "utf8"))
