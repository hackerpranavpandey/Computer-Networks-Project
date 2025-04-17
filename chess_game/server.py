import socket
import threading
import pickle
import time

# --- Game State ---
white_pieces = ['rook', 'knight', 'bishop', 'king', 'queen', 'bishop', 'knight', 'rook',
                'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
white_locations = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
                   (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)]
black_pieces = ['rook', 'knight', 'bishop', 'king', 'queen', 'bishop', 'knight', 'rook',
                'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
black_locations = [(0, 7), (1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7),
                   (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6)]
captured_pieces_white = []
captured_pieces_black = []
chat_history = []  # New: Store chat messages

turn_step = 0
winner = ''
game_over = False

# --- Helper Functions ---
def check_options(pieces, locations, turn_color):
    global white_locations, black_locations
    moves_list = []
    all_moves_list = []
    current_white_locations = white_locations[:]
    current_black_locations = black_locations[:]

    for i in range(len(pieces)):
        location = locations[i]
        piece = pieces[i]
        if piece == 'pawn':
            moves_list = check_pawn(location, turn_color, current_white_locations, current_black_locations)
        elif piece == 'rook':
            moves_list = check_rook(location, turn_color, current_white_locations, current_black_locations)
        elif piece == 'knight':
            moves_list = check_knight(location, turn_color, current_white_locations, current_black_locations)
        elif piece == 'bishop':
            moves_list = check_bishop(location, turn_color, current_white_locations, current_black_locations)
        elif piece == 'queen':
            moves_list = check_queen(location, turn_color, current_white_locations, current_black_locations)
        elif piece == 'king':
            moves_list = check_king(location, turn_color, current_white_locations, current_black_locations)
        all_moves_list.append(moves_list)
    return all_moves_list

def check_pawn(position, color, w_locs, b_locs):
    moves_list = []
    if color == 'white':
        if (position[0], position[1] + 1) not in w_locs and \
           (position[0], position[1] + 1) not in b_locs and position[1] < 7:
            moves_list.append((position[0], position[1] + 1))
        if position[1] == 1 and \
           (position[0], position[1] + 1) not in w_locs and \
           (position[0], position[1] + 1) not in b_locs and \
           (position[0], position[1] + 2) not in w_locs and \
           (position[0], position[1] + 2) not in b_locs:
            moves_list.append((position[0], position[1] + 2))
        if (position[0] + 1, position[1] + 1) in b_locs:
            moves_list.append((position[0] + 1, position[1] + 1))
        if (position[0] - 1, position[1] + 1) in b_locs:
            moves_list.append((position[0] - 1, position[1] + 1))
    else:
        if (position[0], position[1] - 1) not in w_locs and \
           (position[0], position[1] - 1) not in b_locs and position[1] > 0:
            moves_list.append((position[0], position[1] - 1))
        if position[1] == 6 and \
           (position[0], position[1] - 1) not in w_locs and \
           (position[0], position[1] - 1) not in b_locs and \
           (position[0], position[1] - 2) not in w_locs and \
           (position[0], position[1] - 2) not in b_locs:
            moves_list.append((position[0], position[1] - 2))
        if (position[0] + 1, position[1] - 1) in w_locs:
            moves_list.append((position[0] + 1, position[1] - 1))
        if (position[0] - 1, position[1] - 1) in w_locs:
            moves_list.append((position[0] - 1, position[1] - 1))
    return moves_list

def check_rook(position, color, w_locs, b_locs):
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    enemies_list = b_locs if color == 'white' else w_locs
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    for dx, dy in directions:
        chain = 1
        path = True
        while path:
            target_x, target_y = position[0] + (chain * dx), position[1] + (chain * dy)
            target_coords = (target_x, target_y)
            if 0 <= target_x <= 7 and 0 <= target_y <= 7:
                if target_coords not in friends_list:
                    moves_list.append(target_coords)
                    if target_coords in enemies_list:
                        path = False
                    chain += 1
                else:
                    path = False
            else:
                path = False
    return moves_list

def check_knight(position, color, w_locs, b_locs):
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    targets = [(1, 2), (1, -2), (2, 1), (2, -1),
               (-1, 2), (-1, -2), (-2, 1), (-2, -1)]
    for dx, dy in targets:
        target_x, target_y = position[0] + dx, position[1] + dy
        target_coords = (target_x, target_y)
        if 0 <= target_x <= 7 and 0 <= target_y <= 7:
            if target_coords not in friends_list:
                moves_list.append(target_coords)
    return moves_list

def check_bishop(position, color, w_locs, b_locs):
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    enemies_list = b_locs if color == 'white' else w_locs
    directions = [(1, -1), (-1, -1), (1, 1), (-1, 1)]
    for dx, dy in directions:
        chain = 1
        path = True
        while path:
            target_x, target_y = position[0] + (chain * dx), position[1] + (chain * dy)
            target_coords = (target_x, target_y)
            if 0 <= target_x <= 7 and 0 <= target_y <= 7:
                if target_coords not in friends_list:
                    moves_list.append(target_coords)
                    if target_coords in enemies_list:
                        path = False
                    chain += 1
                else:
                    path = False
            else:
                path = False
    return moves_list

def check_queen(position, color, w_locs, b_locs):
    moves_list = check_bishop(position, color, w_locs, b_locs)
    moves_list.extend(check_rook(position, color, w_locs, b_locs))
    return moves_list

def check_king(position, color, w_locs, b_locs):
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    targets = [(1, 0), (1, 1), (1, -1), (-1, 0),
               (-1, 1), (-1, -1), (0, 1), (0, -1)]
    for dx, dy in targets:
        target_x, target_y = position[0] + dx, position[1] + dy
        target_coords = (target_x, target_y)
        if 0 <= target_x <= 7 and 0 <= target_y <= 7:
            if target_coords not in friends_list:
                moves_list.append(target_coords)
    return moves_list

# --- Networking Setup ---
SERVER_IP = '0.0.0.0'
PORT = 5555
MAX_PLAYERS = 2

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    server_socket.bind((SERVER_IP, PORT))
except socket.error as e:
    print(f"Socket bind error: {e}")
    exit()

server_socket.listen(MAX_PLAYERS)
print("Chess Server Started. Waiting for connections...")

clients = []
player_assignments = {}
game_state_lock = threading.Lock()

white_options = check_options(white_pieces, white_locations, 'white')
black_options = check_options(black_pieces, black_locations, 'black')

def get_current_game_state():
    global white_pieces, white_locations, black_pieces, black_locations
    global captured_pieces_white, captured_pieces_black
    global turn_step, game_over, winner, chat_history
    global white_options, black_options

    current_white_options = check_options(white_pieces, white_locations, 'white')
    current_black_options = check_options(black_pieces, black_locations, 'black')

    return {
        'white_pieces': white_pieces,
        'white_locations': white_locations,
        'black_pieces': black_pieces,
        'black_locations': black_locations,
        'captured_white': captured_pieces_white,
        'captured_black': captured_pieces_black,
        'turn_step': turn_step,
        'game_over': game_over,
        'winner': winner,
        'white_options': current_white_options,
        'black_options': current_black_options,
        'chat_history': chat_history
    }

def broadcast_state(sender_conn=None):
    state_data = pickle.dumps(get_current_game_state())
    with game_state_lock:
        current_clients = clients[:]
    for client_conn in current_clients:
        try:
            client_conn.sendall(state_data)
        except socket.error as e:
            print(f"Error sending state to client: {e}. Removing client.")
            remove_client(client_conn)

def remove_client(conn):
    with game_state_lock:
        if conn in clients:
            clients.remove(conn)
            if conn in player_assignments:
                print(f"Player {player_assignments[conn]} disconnected.")
                del player_assignments[conn]
            else:
                print("Spectator or unassigned client disconnected.")
            if len(clients) < MAX_PLAYERS and not game_over:
                 print("A player disconnected. Waiting for new players...")

def handle_client(conn, addr):
    global turn_step, game_over, winner
    global white_pieces, white_locations, black_pieces, black_locations
    global captured_pieces_white, captured_pieces_black, chat_history
    global white_options, black_options

    player_color = player_assignments[conn]
    print(f"Player {player_color} connected from {addr}")

    try:
        conn.sendall(pickle.dumps(player_color))
        broadcast_state()
    except socket.error as e:
        print(f"Error sending initial data to {player_color}: {e}")
        remove_client(conn)
        return

    while True:
        try:
            data = conn.recv(4096)
            if not data:
                print(f"Client {player_color} ({addr}) disconnected (empty data).")
                remove_client(conn)
                break

            message = pickle.loads(data)
            if not isinstance(message, dict) or 'type' not in message:
                print(f"Invalid message format from {player_color}")
                continue

            message_type = message['type']
            message_data = message['data']

            with game_state_lock:
                if message_type == 'move':
                    if game_over:
                        print("Game is over, ignoring move.")
                        continue

                    is_white_turn = (turn_step == 0)
                    if (player_color == 'white' and not is_white_turn) or \
                       (player_color == 'black' and is_white_turn):
                        print(f"Invalid move: Not {player_color}'s turn.")
                        continue

                    selection_index, target_coords = message_data
                    valid_move_found = False
                    piece_options = []

                    if player_color == 'white':
                        if 0 <= selection_index < len(white_pieces):
                            current_white_options = check_options(white_pieces, white_locations, 'white')
                            piece_options = current_white_options[selection_index]
                            if target_coords in piece_options:
                                valid_move_found = True
                            else:
                                 print(f"Invalid move: {target_coords} not in options for white piece {selection_index}")
                        else:
                            print(f"Invalid selection index for white: {selection_index}")
                    else:
                        if 0 <= selection_index < len(black_pieces):
                            current_black_options = check_options(black_pieces, black_locations, 'black')
                            piece_options = current_black_options[selection_index]
                            if target_coords in piece_options:
                                valid_move_found = True
                            else:
                                 print(f"Invalid move: {target_coords} not in options for black piece {selection_index}")
                        else:
                             print(f"Invalid selection index for black: {selection_index}")

                    if valid_move_found:
                        print(f"Executing valid move for {player_color}")
                        if player_color == 'white':
                            if target_coords in black_locations:
                                black_piece_index = black_locations.index(target_coords)
                                captured_piece = black_pieces.pop(black_piece_index)
                                captured_pieces_white.append(captured_piece)
                                black_locations.pop(black_piece_index)
                                print(f"White captured {captured_piece}")
                                if captured_piece == 'king':
                                    winner = 'white'
                                    game_over = True
                                    print("Game Over! White wins!")
                            white_locations[selection_index] = target_coords
                            turn_step = 2
                        else:
                            if target_coords in white_locations:
                                white_piece_index = white_locations.index(target_coords)
                                captured_piece = white_pieces.pop(white_piece_index)
                                captured_pieces_black.append(captured_piece)
                                white_locations.pop(white_piece_index)
                                print(f"Black captured {captured_piece}")
                                if captured_piece == 'king':
                                    winner = 'black'
                                    game_over = True
                                    print("Game Over! Black wins!")
                            black_locations[selection_index] = target_coords
                            turn_step = 0
                        needs_broadcast = True
                    else:
                        print(f"Move {message_data} from {player_color} was invalid.")
                        needs_broadcast = False

                elif message_type == 'chat':
                    chat_message = message_data
                    if chat_message['sender'] == player_color and chat_message['text']:
                        chat_history.append(chat_message)
                        print(f"Chat from {player_color}: {chat_message['text']}")
                        needs_broadcast = True
                    else:
                        print(f"Invalid chat message from {player_color}")
                        needs_broadcast = False

            if needs_broadcast:
                 print("Broadcasting updated game state...")
                 broadcast_state()

        except (socket.error, EOFError, ConnectionResetError, pickle.UnpicklingError) as e:
            print(f"Error with client {player_color} ({addr}): {e}")
            remove_client(conn)
            break

    print(f"Client handler thread for {addr} finished.")
    conn.close()

# --- Main Server Loop ---
player_count = 0
while True:
    if len(clients) < MAX_PLAYERS:
        try:
            conn, addr = server_socket.accept()
        except socket.error as e:
            print(f"Error accepting connection: {e}")
            time.sleep(1)
            continue

        with game_state_lock:
            if len(clients) < MAX_PLAYERS:
                clients.append(conn)
                player_id = 'white' if len(clients) == 1 else 'black'
                player_assignments[conn] = player_id
                print(f"Connection accepted from {addr}. Assigned: {player_id}")

                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()

                if len(clients) == MAX_PLAYERS:
                    print("Both players connected. Game can start.")
            else:
                print(f"Connection attempt from {addr} refused: Server full.")
                try:
                    conn.sendall(pickle.dumps("error:server_full"))
                except socket.error:
                    pass
                conn.close()
    else:
        time.sleep(1)