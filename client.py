import socket
import threading

class ChessClient:
    def __init__(self, host='127.0.0.1', port=12345):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        print("Connected to the server.")

    def receive_moves(self):
        while True:
            message = self.client_socket.recv(1024).decode('utf-8')
            print(message)

    def start_game(self):
        threading.Thread(target=self.receive_moves).start()        
        while True:
            move = input("Enter your move (e.g., e2-e4): ")
            self.client_socket.send(move.encode('utf-8'))

client = ChessClient()
client.start_game()
