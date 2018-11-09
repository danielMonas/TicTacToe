import socket
from threading import Thread
import struct
import os

LEN_SIZE = 4
CLIENT_DICT = {}
AVAILABLE_PLAYERS = []
MATCHES = []
# CODES:
QUIT = "1"
LOGIN_FAIL = "2"
LOGIN_SUCCESS = "3"
MATCH_READY = "4"
TURN = "5"
END_GAME = "6"
TIE = "7"
RESET = "8"


def accept_client(server_sock):
    """ Accepting new incoming connection attempts """
    while True:
        client_socket, client_address = server_sock.accept()
        print("%s:%s has connected." % client_address)

        code, name = receive(client_socket)
        while code not in (QUIT, LOGIN_SUCCESS) or name in CLIENT_DICT.keys() or ' ' in name:
            send(client_socket, LOGIN_FAIL)
            code, name = receive(client_socket)

        if code != QUIT:
            send(client_socket, LOGIN_SUCCESS)
            CLIENT_DICT[client_socket] = name
            AVAILABLE_PLAYERS.append(client_socket)
            Thread(target=handle_client, args=(client_socket,)).start()


def handle_client(client_socket):
    """ Handling existing client's messages, as long as the connection exists """
    code = ""
    match_index = -1
    while code != QUIT:
        if client_socket in AVAILABLE_PLAYERS and len(AVAILABLE_PLAYERS) > 1:
            match_index = set_match(client_socket)

        code, data = receive(client_socket)
        if client_socket not in AVAILABLE_PLAYERS:
            if match_index == -1:
                for i in range(len(MATCHES)):
                    if MATCHES[i].is_player_in_match(client_socket):
                        match_index = i
            send(MATCHES[match_index].get_opponent(client_socket), code, data)
            if code == TURN:
                MATCHES[match_index].board[int(data[:-1])] = data[-1]
                if check_win(MATCHES[match_index]):
                    match_index = -1
    disconnect_client(client_socket)


def disconnect_client(socket):
    """ Function disconnects a client and closes the active socket """
    if socket in AVAILABLE_PLAYERS:
        AVAILABLE_PLAYERS.remove(socket)
    for match in MATCHES:
        if match.is_player_in_match(socket):
            send(match.get_opponent(socket), RESET)
            end_match(match)
    print("Client {} disconnected".format(CLIENT_DICT[socket]))
    socket.close()
    del CLIENT_DICT[socket]


def send(sock, code, msg=""):
    """Sends the message to the client """
    msg = code.rjust(LEN_SIZE, '0') + msg
    print("Sending to {0}: {1}".format(sock.getpeername(), msg))
    try:
        sock.send(bytes(str(len(msg)).rjust(LEN_SIZE, '0'), "utf8"))
        sock.send(bytes(msg, "utf8"))
    except socket.error:
        disconnect_client(sock)


def receive(sock):
    """ Receiving the clients' messages
        sock = origin sock representing the client"""
    try:
        data_len = struct.unpack("!I", sock.recv(LEN_SIZE))[0]
        data = sock.recv(data_len).decode("utf8")
        print("Received message from {0}:{1}".format(sock.getpeername(), data))
        return data[:LEN_SIZE].lstrip("0"), data[LEN_SIZE:]
    except socket.error:
        return QUIT, ""


def set_match(sock1):
    """ Setting up a match with one player and another waiting player
        player1 = name of player looking for a match"""
    AVAILABLE_PLAYERS.remove(sock1)
    sock2 = AVAILABLE_PLAYERS.pop(0)
    for s in [sock1, sock2]:
        send(s, MATCH_READY, CLIENT_DICT[sock1] + " VS " + CLIENT_DICT[sock2])
    MATCHES.append(Match(sock1, sock2))
    return len(MATCHES) - 1


def end_match(match):
    """ Put the players back to the waiting list when the game is over """
    for s in match.s1, match.s2:
        if s not in AVAILABLE_PLAYERS:
            AVAILABLE_PLAYERS.append(socket)
    MATCHES.remove(match)


def check_win(match):
    """ Checking if the game is over by a tie or someone won """
    ways_to_win = [(0, 1, 2), (3, 4, 5), (6, 7, 8),  # horizontal
                   (0, 3, 6), (1, 4, 7), (2, 5, 8),  # vertical
                   (0, 4, 8), (2, 4, 6)]             # diagonal

    for i in range(len(ways_to_win)):
        a, b, c = ways_to_win[i]
        if match.board[a] == match.board[b] == match.board[c] != "":
            match.end_game(END_GAME, match.board[a])
            return True

    for slot in match.board:
        if slot == "":
            return False
    match.end_game(TIE)
    return True


class Match():
    def __init__(self, sock1, sock2):
        self.s1 = sock1
        self.s2 = sock2
        self.board = [''] * 9

    def get_opponent(self, socket):
        """ Returns the a player's enemy """
        if socket == self.s1:
            return self.s2
        return self.s1

    def is_player_in_match(self, socket):
        """ Check if a player is part of this match """
        return socket in (self.s1, self.s2)

    def end_game(self, code, data=""):
        """ The game ended with a tie or someone winning. """
        for p in (self.s1, self.s2):
            send(p, code, data)
        end_match(self)


def main():
    os.system('cls')
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("localhost", 12345))
    server_sock.listen(5)
    print("Server is active ...")
    listener_thread = Thread(target=accept_client, args=(server_sock,))
    listener_thread.start()
    listener_thread.join()
    server_sock.close()


if __name__ == '__main__':
    main()
