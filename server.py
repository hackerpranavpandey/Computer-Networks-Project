import socket
import threading
from queue import Queue

class ClientHandler(threading.Thread):
    def __init__(self, client_socket, address):
        super().__init__()
        self.client_socket = client_socket
        self.address = address
        self.opponent = None
        self.is_my_turn = False

    def run(self):
        while True:
            try:
                move = self.client_socket.recv(1024).decode('utf-8')
                if move:
                    if self.is_my_turn:
                        print(f"Received move from {self.address}: {move}")
                        if self.validate_move(move):
                            if self.opponent:
                                self.opponent.send_move(move)
                                self.is_my_turn = False
                                self.opponent.is_my_turn = True
                        else:
                            self.send_move("Invalid move! Please try again.")
                    else:
                        self.send_move("Wait for your opponent to make a move.")
                else:
                    break
            except ConnectionResetError:
                break
        self.client_socket.close()

    def validate_move(self, move):
        # (this will validate all the moves by any player in order to make sure that it follow the rules of chess game)
        return True if len(move) > 0 else False

    def send_move(self, move):
        self.client_socket.send(move.encode('utf-8'))

class ChessServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        print(f"Server listening on {host}:{port}")
        
        self.waiting_players = Queue()

    def accept_clients(self):
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Accepted connection from {address}")
            client_handler = ClientHandler(client_socket, address)

            if not self.waiting_players.empty():
                opponent_handler = self.waiting_players.get()
                client_handler.opponent = opponent_handler
                opponent_handler.opponent = client_handler
                
                # Start both threads and set the first player to have the turn
                client_handler.is_my_turn = True
                client_handler.start()
                opponent_handler.start()
                
                client_handler.send_move("Opponent found! You can start playing.")
                opponent_handler.send_move("Opponent found! You can start playing.")
            else:
                self.waiting_players.put(client_handler)
                client_handler.send_move("Waiting for an opponent...")

server = ChessServer()
server.accept_clients()
