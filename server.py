import socket
import threading
import pickle
import time # <-- Import time module
from datetime import datetime # <-- Keep for chat timestamps

# --- Constants ---
INITIAL_TIME_SECONDS = 1200.0 # 20 minutes * 60 seconds/minute

# --- Game State Variables (Keep existing ones) ---
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
chat_history = []

turn_step = 0
winner = ''
game_over = False
game_started = False # <-- New flag to know when to start timers

# --- Timer Variables ---
white_time = INITIAL_TIME_SECONDS
black_time = INITIAL_TIME_SECONDS
last_timer_update = None # <-- Timestamp of the last update

# --- Helper Functions (Keep existing check_... functions) ---
def check_options(pieces, locations, turn_color):
    # (Keep the original check_options function exactly as it is)
    # ... (rest of the function remains the same)
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
    # (Keep the original check_pawn function exactly as it is)
    # ... (rest of the function remains the same)
    moves_list = []
    if color == 'white':
        if (position[0], position[1] + 1) not in w_locs and \
           (position[0], position[1] + 1) not in b_locs and position[1] < 7:
            moves_list.append((position[0], position[1] + 1))
        # Allow first move 2 squares
        if position[1] == 1 and \
           (position[0], position[1] + 1) not in w_locs and \
           (position[0], position[1] + 1) not in b_locs and \
           (position[0], position[1] + 2) not in w_locs and \
           (position[0], position[1] + 2) not in b_locs:
            moves_list.append((position[0], position[1] + 2))
        # Allow diagonal capture
        if (position[0] + 1, position[1] + 1) in b_locs:
            moves_list.append((position[0] + 1, position[1] + 1))
        if (position[0] - 1, position[1] + 1) in b_locs:
            moves_list.append((position[0] - 1, position[1] + 1))
    else: # Black's turn
        if (position[0], position[1] - 1) not in w_locs and \
           (position[0], position[1] - 1) not in b_locs and position[1] > 0:
            moves_list.append((position[0], position[1] - 1))
        # Allow first move 2 squares
        if position[1] == 6 and \
           (position[0], position[1] - 1) not in w_locs and \
           (position[0], position[1] - 1) not in b_locs and \
           (position[0], position[1] - 2) not in w_locs and \
           (position[0], position[1] - 2) not in b_locs:
            moves_list.append((position[0], position[1] - 2))
        # Allow diagonal capture
        if (position[0] + 1, position[1] - 1) in w_locs:
            moves_list.append((position[0] + 1, position[1] - 1))
        if (position[0] - 1, position[1] - 1) in w_locs:
            moves_list.append((position[0] - 1, position[1] - 1))
    return moves_list

def check_rook(position, color, w_locs, b_locs):
    # (Keep the original check_rook function exactly as it is)
    # ... (rest of the function remains the same)
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    enemies_list = b_locs if color == 'white' else w_locs
    # Check up, down, left, right
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
                    if target_coords in enemies_list: # Path blocked by enemy
                        path = False
                    chain += 1
                else: # Path blocked by friend
                    path = False
            else: # Off board
                path = False
    return moves_list


def check_knight(position, color, w_locs, b_locs):
    # (Keep the original check_knight function exactly as it is)
    # ... (rest of the function remains the same)
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    # 8 possible moves L-shape
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
    # (Keep the original check_bishop function exactly as it is)
    # ... (rest of the function remains the same)
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    enemies_list = b_locs if color == 'white' else w_locs
    # Check diagonals
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
                    if target_coords in enemies_list: # Path blocked by enemy
                        path = False
                    chain += 1
                else: # Path blocked by friend
                    path = False
            else: # Off board
                path = False
    return moves_list

def check_queen(position, color, w_locs, b_locs):
    # (Keep the original check_queen function exactly as it is)
    # ... (rest of the function remains the same)
    moves_list = check_bishop(position, color, w_locs, b_locs)
    moves_list.extend(check_rook(position, color, w_locs, b_locs))
    return moves_list

def check_king(position, color, w_locs, b_locs):
    # (Keep the original check_king function exactly as it is)
    # ... (rest of the function remains the same)
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    # 8 possible moves 1 square away
    targets = [(1, 0), (1, 1), (1, -1), (-1, 0),
               (-1, 1), (-1, -1), (0, 1), (0, -1)]
    for dx, dy in targets:
        target_x, target_y = position[0] + dx, position[1] + dy
        target_coords = (target_x, target_y)
        if 0 <= target_x <= 7 and 0 <= target_y <= 7:
            if target_coords not in friends_list:
                moves_list.append(target_coords)
    # Need to add castling!
    # Need to add check checks
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
game_state_lock = threading.Lock() # Keep using the lock

# Calculate initial options (can be done once at start)
white_options = check_options(white_pieces, white_locations, 'white')
black_options = check_options(black_pieces, black_locations, 'black')

def update_timers():
    """Calculates elapsed time and updates player timers."""
    global white_time, black_time, last_timer_update, game_over, winner, turn_step, game_started

    if not game_started or game_over or last_timer_update is None:
        return # Don't update timers if game hasn't started, is over, or first update hasn't happened

    now = time.time()
    elapsed = now - last_timer_update

    if turn_step < 2:
        white_time -= elapsed
        if white_time <= 0:
            white_time = 0
            winner = 'black'
            game_over = True
            print("Game Over! Black wins on time!")
    else:
        black_time -= elapsed
        if black_time <= 0:
            black_time = 0
            winner = 'white'
            game_over = True
            print("Game Over! White wins on time!")

    last_timer_update = now

def get_current_game_state():
    """Updates timers and returns the complete current game state."""
    global white_pieces, white_locations, black_pieces, black_locations
    global captured_pieces_white, captured_pieces_black
    global turn_step, game_over, winner, chat_history
    global white_options, black_options
    global white_time, black_time

    update_timers() # This function now also checks for timeout game over

    # Recalculate options for the current state
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
        'white_options': current_white_options, # Send current valid options
        'black_options': current_black_options, # Send current valid options
        'chat_history': chat_history,
        # --- Add Timer Information ---
        'white_time': white_time,
        'black_time': black_time,
        'game_started': game_started # Client might want to know this
    }

def broadcast_state(sender_conn=None):
    """Sends the current game state to all connected clients."""
    state_data = pickle.dumps(get_current_game_state()) # get_current includes timer updates
    with game_state_lock: # Ensure thread safety when accessing clients list
        current_clients = clients[:] # Make a copy
    for client_conn in current_clients:
        #if client_conn == sender_conn: # Don't send back to sender? Optional. Usually good to send to all.
        #    continue
        try:
            client_conn.sendall(state_data)
        except socket.error as e:
            print(f"Error sending state to client: {e}. Removing client.")
            remove_client(client_conn) # Make sure remove_client handles potential KeyError

def remove_client(conn):
    """Removes a client connection and handles associated cleanup."""
    global game_started, last_timer_update, clients, player_assignments, game_over, winner
    with game_state_lock:
        if conn in clients:
            clients.remove(conn)
            disconnected_color = None
            if conn in player_assignments:
                disconnected_color = player_assignments[conn]
                print(f"Player {disconnected_color} disconnected.")
                del player_assignments[conn]
            else:
                print("Spectator or unassigned client disconnected.")

            # If a player disconnects during the game, the other player wins
            if len(clients) < MAX_PLAYERS and game_started and not game_over:
                 print("A player disconnected during the game.")
                 if disconnected_color == 'white':
                     winner = 'black'
                 elif disconnected_color == 'black':
                     winner = 'white'
                 else: # Should not happen if assignments are correct
                     winner = 'unknown'
                 game_over = True
                 print(f"Game Over! {winner.capitalize()} wins by opponent disconnection.")
                 broadcast_state() # Inform the remaining player

            elif len(clients) < MAX_PLAYERS:
                print("Waiting for new players...")
                # Optional: Reset game state if you want a fresh game when someone reconnects
                # Resetting might be complex if one player remains; for now, just wait or end.
                # Resetting timers if game restarts would be needed.

def handle_client(conn, addr):
    """Handles communication with a single client."""
    global turn_step, game_over, winner
    global white_pieces, white_locations, black_pieces, black_locations
    global captured_pieces_white, captured_pieces_black, chat_history
    global white_options, black_options, last_timer_update # Make sure last_timer_update is accessible

    player_color = player_assignments.get(conn, "Unknown") # Safer access
    print(f"Player {player_color} connected from {addr}")

    try:
        # Send initial color assignment
        conn.sendall(pickle.dumps(player_color))
        # Send initial game state (timers will be full initially)
        broadcast_state()
    except socket.error as e:
        print(f"Error sending initial data to {player_color}: {e}")
        remove_client(conn)
        return

    while True:
        try:
            data = conn.recv(4096) # Increased buffer size just in case state gets larger
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
            needs_broadcast = False # Flag to check if state needs update

            with game_state_lock: # Lock before modifying shared game state
                # --- Handle MOVE ---
                if message_type == 'move':
                    if game_over:
                        print("Game is over, ignoring move.")
                        continue

                    is_white_turn = (turn_step < 2) # Steps 0, 1 are white's turn/moving phase
                    current_player_color = 'white' if is_white_turn else 'black'

                    if player_color != current_player_color:
                        print(f"Invalid move: Not {player_color}'s turn (It's {current_player_color}'s turn).")
                        # Optional: Send an error message back to the client?
                        # try:
                        #     conn.sendall(pickle.dumps("error:not_your_turn"))
                        # except socket.error: pass
                        continue # Ignore the move

                    # --- Move Validation ---
                    selection_index, target_coords = message_data
                    valid_move_found = False
                    piece_options = []

                    # Recalculate options *just before* validating the move based on current state
                    if player_color == 'white':
                        current_white_options = check_options(white_pieces, white_locations, 'white')
                        if 0 <= selection_index < len(white_pieces) and 0 <= selection_index < len(current_white_options):
                            piece_options = current_white_options[selection_index]
                            if target_coords in piece_options:
                                valid_move_found = True
                            else:
                                 print(f"Invalid move: {target_coords} not in options {piece_options} for white piece {white_pieces[selection_index]} at index {selection_index}")
                        else:
                            print(f"Invalid selection index for white: {selection_index} (len={len(white_pieces)})")
                    else: # Black player
                        current_black_options = check_options(black_pieces, black_locations, 'black')
                        if 0 <= selection_index < len(black_pieces) and 0 <= selection_index < len(current_black_options):
                            piece_options = current_black_options[selection_index]
                            if target_coords in piece_options:
                                valid_move_found = True
                            else:
                                 print(f"Invalid move: {target_coords} not in options {piece_options} for black piece {black_pieces[selection_index]} at index {selection_index}")
                        else:
                             print(f"Invalid selection index for black: {selection_index} (len={len(black_pieces)})")

                    # --- Execute Valid Move ---
                    if valid_move_found:
                        print(f"Executing valid move for {player_color}: piece {selection_index} to {target_coords}")

                        # --- Timer update happens *before* state is sent via broadcast ---
                        # update_timers() is called within get_current_game_state()

                        # --- Piece Capture Logic ---
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
                                    print("Game Over! White wins by capturing king!")
                            # Move the piece
                            white_locations[selection_index] = target_coords
                            # --- Pawn Promotion (Basic Example) ---
                            if white_pieces[selection_index] == 'pawn' and target_coords[1] == 7:
                                white_pieces[selection_index] = 'queen' # Auto-promote to queen for now
                                print("White pawn promoted to Queen!")
                            # Switch turn
                            turn_step = 2 # Black's turn starts

                        else: # Black player's move
                            if target_coords in white_locations:
                                white_piece_index = white_locations.index(target_coords)
                                captured_piece = white_pieces.pop(white_piece_index)
                                captured_pieces_black.append(captured_piece)
                                white_locations.pop(white_piece_index)
                                print(f"Black captured {captured_piece}")
                                if captured_piece == 'king':
                                    winner = 'black'
                                    game_over = True
                                    print("Game Over! Black wins by capturing king!")
                            # Move the piece
                            black_locations[selection_index] = target_coords
                            # --- Pawn Promotion (Basic Example) ---
                            if black_pieces[selection_index] == 'pawn' and target_coords[1] == 0:
                                black_pieces[selection_index] = 'queen' # Auto-promote to queen for now
                                print("Black pawn promoted to Queen!")
                            # Switch turn
                            turn_step = 0 # White's turn starts

                        # Reset the timer update timestamp for the new turn
                        last_timer_update = time.time()
                        needs_broadcast = True # State changed, must broadcast

                    else: # Move was invalid
                        print(f"Move {message_data} from {player_color} was invalid.")
                        needs_broadcast = False

                # --- Handle CHAT ---
                elif message_type == 'chat':
                    chat_message = message_data
                    # Basic validation: Ensure sender matches connection and text exists
                    if chat_message.get('sender') == player_color and chat_message.get('text'):
                        # Add server-side timestamp if missing (client should add it ideally)
                        if 'timestamp' not in chat_message:
                             chat_message['timestamp'] = datetime.now().strftime("%I:%M %p")
                        chat_history.append(chat_message)
                        # Limit chat history size (optional)
                        if len(chat_history) > 100:
                            chat_history.pop(0)
                        print(f"Chat from {player_color}: {chat_message['text']}")
                        needs_broadcast = True
                    else:
                        print(f"Invalid chat message format/sender from {player_color}: {chat_message}")
                        needs_broadcast = False

                # --- Add other message types if needed (e.g., 'forfeit') ---
                # elif message_type == 'forfeit':
                #    if not game_over:
                #        winner = 'black' if player_color == 'white' else 'white'
                #        game_over = True
                #        print(f"Game Over! {player_color} forfeited. {winner.capitalize()} wins!")
                #        needs_broadcast = True

            # --- Broadcast state if changed ---
            if needs_broadcast:
                 print("Broadcasting updated game state...")
                 broadcast_state() # Broadcast happens outside the lock

        except (socket.error, EOFError, ConnectionResetError) as e:
            print(f"Network error with client {player_color} ({addr}): {e}")
            remove_client(conn)
            break
        except pickle.UnpicklingError as e:
            print(f"Error unpickling data from {player_color} ({addr}): {e}")
            # Decide if this warrants disconnecting the client
            remove_client(conn) # Probably best to disconnect on bad data
            break
        except Exception as e: # Catch broader exceptions
            print(f"Unexpected error handling client {player_color} ({addr}): {e}")
            import traceback
            traceback.print_exc() # Print stack trace for debugging
            remove_client(conn)
            break

    print(f"Client handler thread for {addr} finished.")
    try:
        conn.close()
    except socket.error:
        pass

# --- Main Server Loop ---
while True:
    if len(clients) < MAX_PLAYERS:
        try:
            print(f"Waiting for player {len(clients) + 1}/{MAX_PLAYERS}...")
            conn, addr = server_socket.accept()
            print(f"Accepted connection from {addr}")
        except socket.error as e:
            print(f"Error accepting connection: {e}")
            time.sleep(1) # Avoid busy-waiting on error
            continue

        with game_state_lock: # Lock before modifying shared client/assignment lists
            if len(clients) < MAX_PLAYERS:
                clients.append(conn)
                player_id = 'white' if len(clients) == 1 else 'black'
                player_assignments[conn] = player_id
                print(f"Assigned color: {player_id} to {addr}")

                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()

                if len(clients) == MAX_PLAYERS:
                    print("Both players connected. Starting game and timers.")
                    game_started = True
                    last_timer_update = time.time() # Initialize timer timestamp
                    # Initial broadcast already happens in handle_client
            else:
                # This block should technically not be reached if the outer check works,
                # but it's good defense.
                print(f"Connection attempt from {addr} refused: Server full.")
                try:
                    # Send a rejection message
                    conn.sendall(pickle.dumps("error:server_full"))
                except socket.error as send_err:
                     print(f"Could not send 'server_full' message: {send_err}")
                finally:
                    conn.close() # Close the connection immediately
    else:
        # Server is full, just wait passively.
        # Check for game over state periodically? (update_timers handles timeout)
        # Maybe add a periodic check here if no clients are active for a long time?
        time.sleep(1) # Wait a second before checking again if server is full
