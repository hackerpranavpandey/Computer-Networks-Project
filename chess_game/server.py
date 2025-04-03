import socket
import threading
import pickle
import time

# --- Game Logic (Copied and adapted from your original code) ---

# Initial Game State (Server is the source of truth)
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

turn_step = 0  # 0: white turn, 2: black turn
# selection/valid_moves are handled per move attempt, not permanent state here
winner = ''
game_over = False

# --- Helper Functions (Check Logic) ---
# (These functions are needed on the server for validation)

def check_options(pieces, locations, turn_color):
    # Need to pass the *current* state of all pieces for accurate checks
    global white_locations, black_locations
    moves_list = []
    all_moves_list = []
    current_white_locations = white_locations[:] # Use copies for checks
    current_black_locations = black_locations[:]

    for i in range(len(pieces)):
        location = locations[i]
        piece = pieces[i]
        # Pass all location lists to check functions
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
        # Move one forward
        if (position[0], position[1] + 1) not in w_locs and \
           (position[0], position[1] + 1) not in b_locs and position[1] < 7:
            moves_list.append((position[0], position[1] + 1))
        # Move two forward (initial move)
        if position[1] == 1 and \
           (position[0], position[1] + 1) not in w_locs and \
           (position[0], position[1] + 1) not in b_locs and \
           (position[0], position[1] + 2) not in w_locs and \
           (position[0], position[1] + 2) not in b_locs:
            moves_list.append((position[0], position[1] + 2))
        # Capture diagonally
        if (position[0] + 1, position[1] + 1) in b_locs:
            moves_list.append((position[0] + 1, position[1] + 1))
        if (position[0] - 1, position[1] + 1) in b_locs:
            moves_list.append((position[0] - 1, position[1] + 1))
    else: # color == 'black'
        # Move one forward
        if (position[0], position[1] - 1) not in w_locs and \
           (position[0], position[1] - 1) not in b_locs and position[1] > 0:
            moves_list.append((position[0], position[1] - 1))
        # Move two forward (initial move)
        if position[1] == 6 and \
           (position[0], position[1] - 1) not in w_locs and \
           (position[0], position[1] - 1) not in b_locs and \
           (position[0], position[1] - 2) not in w_locs and \
           (position[0], position[1] - 2) not in b_locs:
            moves_list.append((position[0], position[1] - 2))
        # Capture diagonally
        if (position[0] + 1, position[1] - 1) in w_locs:
            moves_list.append((position[0] + 1, position[1] - 1))
        if (position[0] - 1, position[1] - 1) in w_locs:
            moves_list.append((position[0] - 1, position[1] - 1))
    return moves_list

def check_rook(position, color, w_locs, b_locs):
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    enemies_list = b_locs if color == 'white' else w_locs
    # Directions: down, up, right, left
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
                    if target_coords in enemies_list: # Can capture, but path ends
                        path = False
                    chain += 1
                else: # Blocked by friend
                    path = False
            else: # Off board
                path = False
    return moves_list

def check_knight(position, color, w_locs, b_locs):
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    # Knight moves: 8 possible L-shapes
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
    # Directions: up-right, up-left, down-right, down-left
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
                    if target_coords in enemies_list: # Can capture, but path ends
                        path = False
                    chain += 1
                else: # Blocked by friend
                    path = False
            else: # Off board
                path = False
    return moves_list

def check_queen(position, color, w_locs, b_locs):
    # Queen moves are rook moves + bishop moves
    moves_list = check_bishop(position, color, w_locs, b_locs)
    moves_list.extend(check_rook(position, color, w_locs, b_locs))
    return moves_list

def check_king(position, color, w_locs, b_locs):
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    # King moves: 1 step in any of the 8 directions
    targets = [(1, 0), (1, 1), (1, -1), (-1, 0),
               (-1, 1), (-1, -1), (0, 1), (0, -1)]
    for dx, dy in targets:
        target_x, target_y = position[0] + dx, position[1] + dy
        target_coords = (target_x, target_y)
        if 0 <= target_x <= 7 and 0 <= target_y <= 7:
            if target_coords not in friends_list:
                moves_list.append(target_coords)
    # Basic castling check could be added here, but is complex
    return moves_list

# --- Networking Setup ---
SERVER_IP = '0.0.0.0' # Listen on all available network interfaces
PORT = 5555
MAX_PLAYERS = 2

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow address reuse

try:
    server_socket.bind((SERVER_IP, PORT))
except socket.error as e:
    print(f"Socket bind error: {e}")
    exit()

server_socket.listen(MAX_PLAYERS)
print("Chess Server Started. Waiting for connections...")

clients = [] # List to store client connection objects
player_assignments = {} # Dictionary {conn: 'white'/'black'}
game_state_lock = threading.Lock() # To prevent race conditions when modifying game state

# --- Game State Calculation ---
# Calculate initial options (needed for check validation later if implemented)
white_options = check_options(white_pieces, white_locations, 'white')
black_options = check_options(black_pieces, black_locations, 'black')

def get_current_game_state():
    """Packages the current game state for sending."""
    global white_pieces, white_locations, black_pieces, black_locations
    global captured_pieces_white, captured_pieces_black
    global turn_step, game_over, winner
    global white_options, black_options # Send valid moves too for check display

    # Recalculate options before sending, ensures they are current
    # Note: This is slightly inefficient, could optimize later
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
        'white_options': current_white_options, # Client needs this for check display
        'black_options': current_black_options, # Client needs this for check display
    }

def broadcast_state(sender_conn=None):
    """Sends the current game state to all connected clients."""
    state_data = pickle.dumps(get_current_game_state())
    with game_state_lock: # Access clients list safely
        current_clients = clients[:] # Make a copy to iterate over

    for client_conn in current_clients:
        # Optionally skip sending back to the sender if needed, but often state update is needed everywhere
        try:
            client_conn.sendall(state_data)
        except socket.error as e:
            print(f"Error sending state to client: {e}. Removing client.")
            remove_client(client_conn)

def remove_client(conn):
    """Removes a client connection."""
    with game_state_lock:
        if conn in clients:
            clients.remove(conn)
            if conn in player_assignments:
                print(f"Player {player_assignments[conn]} disconnected.")
                del player_assignments[conn]
                # Handle game termination if a player leaves mid-game (optional)
                # For now, just print and remove
            else:
                print("Spectator or unassigned client disconnected.")
        # If only one player left, maybe end game?
        if len(clients) < MAX_PLAYERS and not game_over:
             print("A player disconnected. Waiting for new players...")
             # Could reset game state here if desired

def handle_client(conn, addr):
    """Handles communication with a single client."""
    global turn_step, game_over, winner
    global white_pieces, white_locations, black_pieces, black_locations
    global captured_pieces_white, captured_pieces_black
    global white_options, black_options # Allow modification

    player_color = player_assignments[conn]
    print(f"Player {player_color} connected from {addr}")

    # Send initial assignment
    try:
        conn.sendall(pickle.dumps(player_color))
        # Send initial game state after assignment
        broadcast_state()
    except socket.error as e:
        print(f"Error sending initial data to {player_color}: {e}")
        remove_client(conn)
        return # Exit thread if initial send fails

    while True:
        try:
            data = conn.recv(4096) # Receive move data (adjust buffer size if needed)
            if not data:
                print(f"Client {player_color} ({addr}) disconnected (empty data).")
                remove_client(conn)
                break # Exit loop

            move_data = pickle.loads(data) # Expecting (selection_index, target_coords)
            print(f"Received move attempt from {player_color}: {move_data}")

            # --- Move Processing ---
            with game_state_lock: # Lock before checking/modifying state
                if game_over:
                    print("Game is over, ignoring move.")
                    continue # Ignore moves if game is finished

                # 1. Check if it's the correct player's turn
                is_white_turn = (turn_step == 0)
                if (player_color == 'white' and not is_white_turn) or \
                   (player_color == 'black' and is_white_turn):
                    print(f"Invalid move: Not {player_color}'s turn.")
                    # Optionally send an "invalid turn" message back
                    # conn.sendall(pickle.dumps("error:not_your_turn"))
                    continue # Skip processing

                # 2. Validate the move
                selection_index, target_coords = move_data
                valid_move_found = False
                piece_options = [] # Store valid moves for the selected piece

                if player_color == 'white':
                    if 0 <= selection_index < len(white_pieces):
                        # Recalculate options for the current state *before* the move
                        current_white_options = check_options(white_pieces, white_locations, 'white')
                        piece_options = current_white_options[selection_index]
                        if target_coords in piece_options:
                            valid_move_found = True
                        else:
                             print(f"Invalid move: {target_coords} not in options for white piece {selection_index}")
                    else:
                        print(f"Invalid selection index for white: {selection_index}")
                else: # player_color == 'black'
                    if 0 <= selection_index < len(black_pieces):
                        # Recalculate options for the current state *before* the move
                        current_black_options = check_options(black_pieces, black_locations, 'black')
                        piece_options = current_black_options[selection_index]
                        if target_coords in piece_options:
                            valid_move_found = True
                        else:
                             print(f"Invalid move: {target_coords} not in options for black piece {selection_index}")
                    else:
                         print(f"Invalid selection index for black: {selection_index}")


                # 3. Execute Valid Move
                if valid_move_found:
                    print(f"Executing valid move for {player_color}")
                    if player_color == 'white':
                        # Check for capture
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
                        # Update white piece location
                        white_locations[selection_index] = target_coords
                        turn_step = 2 # Switch to black's turn

                    else: # player_color == 'black'
                        # Check for capture
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
                        # Update black piece location
                        black_locations[selection_index] = target_coords
                        turn_step = 0 # Switch to white's turn

                    # Update options lists after move (important for next turn's checks)
                    # These will be recalculated fully in get_current_game_state before broadcast
                    # white_options = check_options(white_pieces, white_locations, 'white')
                    # black_options = check_options(black_pieces, black_locations, 'black')

                    # 4. Broadcast updated state to ALL clients
                    # (Unlock happens after broadcast call)
                    # Need to unlock here before calling broadcast which might lock again
                    # No, broadcast handles its own locking for reading clients list
                    needs_broadcast = True


                else: # Invalid move logic
                    print(f"Move {move_data} from {player_color} was invalid.")
                    # Optionally send feedback
                    # conn.sendall(pickle.dumps("error:invalid_move"))
                    needs_broadcast = False # Don't broadcast if move was invalid

            # End of critical section (lock released automatically)

            # Broadcast outside the lock if a valid move occurred
            if needs_broadcast:
                 print("Broadcasting updated game state...")
                 broadcast_state()


        except (socket.error, EOFError, ConnectionResetError, pickle.UnpicklingError) as e:
            print(f"Error with client {player_color} ({addr}): {e}")
            remove_client(conn)
            break # Exit loop

    print(f"Client handler thread for {addr} finished.")
    conn.close()

# --- Main Server Loop ---
player_count = 0
while True: # Keep accepting connections (e.g., if a player drops)
    if len(clients) < MAX_PLAYERS:
        try:
            conn, addr = server_socket.accept()
        except socket.error as e:
            print(f"Error accepting connection: {e}")
            time.sleep(1) # Avoid busy-waiting on error
            continue

        with game_state_lock: # Protect clients list and assignments
            if len(clients) < MAX_PLAYERS:
                clients.append(conn)
                player_id = 'white' if len(clients) == 1 else 'black'
                player_assignments[conn] = player_id
                print(f"Connection accepted from {addr}. Assigned: {player_id}")

                # Start a new thread for the client
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()

                if len(clients) == MAX_PLAYERS:
                    print("Both players connected. Game can start.")
                    # Initial broadcast happens within handle_client after assignment
            else:
                print(f"Connection attempt from {addr} refused: Server full.")
                # Optionally send a 'server full' message and close
                try:
                    conn.sendall(pickle.dumps("error:server_full"))
                except socket.error:
                    pass # Ignore if send fails
                conn.close()
    else:
        # Server is full, just wait briefly before checking again
        time.sleep(1)

# server_socket.close() # Usually unreachable in this loop, add cleanup if loop condition changes