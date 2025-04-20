# ######## server.py code ########
import socket
import threading
import pickle
import time # <-- Import time module
from datetime import datetime # <-- Keep for chat timestamps

# --- Constants ---
INITIAL_TIME_SECONDS = 120.0 # 20 minutes * 60 seconds/minute
BROADCAST_INTERVAL = 1.0 # Seconds between state broadcasts for timer updates

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
game_started = False # <-- Flag to know when to start timers

# --- Timer Variables ---
white_time = INITIAL_TIME_SECONDS
black_time = INITIAL_TIME_SECONDS
last_timer_update = None # <-- Timestamp of the last update
last_periodic_broadcast_time = 0 # <-- Timestamp for periodic broadcast control

# --- Helper Functions (Keep existing check_... functions) ---
def check_options(pieces, locations, turn_color):
    # (Keep the original check_options function exactly as it is)
    global white_locations, black_locations
    moves_list = []
    all_moves_list = []
    # Make copies to prevent modification during calculation if needed, though current check funcs don't modify
    current_white_locations = white_locations[:]
    current_black_locations = black_locations[:]

    for i in range(len(pieces)):
        location = locations[i]
        piece = pieces[i]
        # Basic validation to prevent errors if lists get mismatched temporarily
        if not (0 <= i < len(locations)): continue
        if piece not in ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']: continue

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
    moves_list = []
    if color == 'white':
        # Forward 1
        if (position[0], position[1] + 1) not in w_locs and \
           (position[0], position[1] + 1) not in b_locs and position[1] < 7:
            moves_list.append((position[0], position[1] + 1))
        # Forward 2 (from starting row)
        if position[1] == 1 and \
           (position[0], position[1] + 1) not in w_locs and \
           (position[0], position[1] + 1) not in b_locs and \
           (position[0], position[1] + 2) not in w_locs and \
           (position[0], position[1] + 2) not in b_locs and position[1] < 6: # Ensure not moving off board
            moves_list.append((position[0], position[1] + 2))
        # Diagonal capture
        if position[0] < 7 and position[1] < 7 and (position[0] + 1, position[1] + 1) in b_locs:
            moves_list.append((position[0] + 1, position[1] + 1))
        if position[0] > 0 and position[1] < 7 and (position[0] - 1, position[1] + 1) in b_locs:
            moves_list.append((position[0] - 1, position[1] + 1))
        # Add En Passant later if needed
    else: # Black's turn
        # Forward 1
        if (position[0], position[1] - 1) not in w_locs and \
           (position[0], position[1] - 1) not in b_locs and position[1] > 0:
            moves_list.append((position[0], position[1] - 1))
        # Forward 2 (from starting row)
        if position[1] == 6 and \
           (position[0], position[1] - 1) not in w_locs and \
           (position[0], position[1] - 1) not in b_locs and \
           (position[0], position[1] - 2) not in w_locs and \
           (position[0], position[1] - 2) not in b_locs and position[1] > 1: # Ensure not moving off board
            moves_list.append((position[0], position[1] - 2))
        # Diagonal capture
        if position[0] < 7 and position[1] > 0 and (position[0] + 1, position[1] - 1) in w_locs:
            moves_list.append((position[0] + 1, position[1] - 1))
        if position[0] > 0 and position[1] > 0 and (position[0] - 1, position[1] - 1) in w_locs:
            moves_list.append((position[0] - 1, position[1] - 1))
        # Add En Passant later if needed
    return moves_list


def check_rook(position, color, w_locs, b_locs):
    # (Keep the original check_rook function exactly as it is)
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    enemies_list = b_locs if color == 'white' else w_locs
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Up, Down, Right, Left
    for dx, dy in directions:
        for i in range(1, 8): # Max 7 steps in any direction
            target_x, target_y = position[0] + i * dx, position[1] + i * dy
            target_coords = (target_x, target_y)
            if 0 <= target_x <= 7 and 0 <= target_y <= 7: # Check if on board
                if target_coords not in friends_list:
                    moves_list.append(target_coords)
                    if target_coords in enemies_list: # Path blocked by enemy capture
                        break # Stop checking further in this direction
                else: # Path blocked by friend
                    break # Stop checking further in this direction
            else: # Off board
                break # Stop checking further in this direction
    return moves_list


def check_knight(position, color, w_locs, b_locs):
    # (Keep the original check_knight function exactly as it is)
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
    # (Keep the original check_bishop function exactly as it is)
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    enemies_list = b_locs if color == 'white' else w_locs
    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)] # Diagonal directions
    for dx, dy in directions:
        for i in range(1, 8):
            target_x, target_y = position[0] + i * dx, position[1] + i * dy
            target_coords = (target_x, target_y)
            if 0 <= target_x <= 7 and 0 <= target_y <= 7: # On board
                if target_coords not in friends_list:
                    moves_list.append(target_coords)
                    if target_coords in enemies_list: # Path blocked by enemy capture
                        break
                else: # Path blocked by friend
                    break
            else: # Off board
                break
    return moves_list


def check_queen(position, color, w_locs, b_locs):
    # (Keep the original check_queen function exactly as it is)
    moves_list = check_bishop(position, color, w_locs, b_locs)
    moves_list.extend(check_rook(position, color, w_locs, b_locs))
    return moves_list


def check_king(position, color, w_locs, b_locs):
    # (Keep the original check_king function exactly as it is)
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
    # Basic Castling Check Placeholder (Needs check validation)
    # if color == 'white' and position == (4, 0): # and king/rooks haven't moved
    #     if (5,0) not in w_locs and (6,0) not in w_locs and (7,0) in w_locs: moves_list.append((6,0)) # Kingside
    #     if (3,0) not in w_locs and (2,0) not in w_locs and (1,0) not in w_locs and (0,0) in w_locs: moves_list.append((2,0)) # Queenside
    # elif color == 'black' and position == (4, 7): # and king/rooks haven't moved
    #     if (5,7) not in b_locs and (6,7) not in b_locs and (7,7) in b_locs: moves_list.append((6,7)) # Kingside
    #     if (3,7) not in b_locs and (2,7) not in b_locs and (1,7) not in b_locs and (0,7) in b_locs: moves_list.append((2,7)) # Queenside
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
    """Calculates elapsed time and updates player timers. Must be called within game_state_lock."""
    global white_time, black_time, last_timer_update, game_over, winner, turn_step, game_started

    if not game_started or game_over or last_timer_update is None:
        return # Don't update timers if game hasn't started, is over, or first update hasn't happened

    now = time.time()
    elapsed = now - last_timer_update
    timer_changed = False

    # Only decrease time if elapsed > 0 to avoid issues on rapid calls
    if elapsed > 0:
        if turn_step < 2: # White's turn
            white_time -= elapsed
            timer_changed = True
            if white_time <= 0:
                white_time = 0
                if not game_over: # Ensure game over logic runs only once
                    winner = 'black'
                    game_over = True
                    print(f"Game Over! Black wins on time! (White: {white_time:.2f})")
        else: # Black's turn
            black_time -= elapsed
            timer_changed = True
            if black_time <= 0:
                black_time = 0
                if not game_over: # Ensure game over logic runs only once
                    winner = 'white'
                    game_over = True
                    print(f"Game Over! White wins on time! (Black: {black_time:.2f})")

    last_timer_update = now # Always update the timestamp for the next calculation
    return timer_changed or game_over # Indicate if state relevant to broadcast changed


def get_current_game_state():
    """Returns the complete current game state. Assumes timers are updated just before or handled by periodic updates."""
    global white_pieces, white_locations, black_pieces, black_locations
    global captured_pieces_white, captured_pieces_black
    global turn_step, game_over, winner, chat_history
    global white_options, black_options # These should be updated after moves
    global white_time, black_time

    # NOTE: Timer updates are now primarily handled by the periodic update mechanism.
    # This function now just reads the current state.
    # Options are recalculated here for safety, ensuring the sent state is always consistent.
    current_white_options = check_options(white_pieces, white_locations, 'white')
    current_black_options = check_options(black_pieces, black_locations, 'black')

    return {
        'white_pieces': white_pieces[:], # Send copies
        'white_locations': white_locations[:],
        'black_pieces': black_pieces[:],
        'black_locations': black_locations[:],
        'captured_white': captured_pieces_white[:],
        'captured_black': captured_pieces_black[:],
        'turn_step': turn_step,
        'game_over': game_over,
        'winner': winner,
        'white_options': current_white_options,
        'black_options': current_black_options,
        'chat_history': chat_history[:],
        'white_time': white_time,
        'black_time': black_time,
        'game_started': game_started
    }


def broadcast_state():
    """Sends the current game state to all connected clients."""
    # Get state OUTSIDE the client loop to avoid recalculating/locking repeatedly
    try:
        state_data = pickle.dumps(get_current_game_state())
    except Exception as e:
        print(f"Error pickling game state: {e}")
        return # Cannot broadcast if pickling fails

    with game_state_lock: # Lock only needed for accessing the clients list safely
        current_clients = clients[:] # Make a copy to iterate over

    #print(f"Broadcasting state to {len(current_clients)} clients.") # Debug print
    for client_conn in current_clients:
        try:
            client_conn.sendall(state_data)
        except (socket.error, BrokenPipeError) as e:
            print(f"Error sending state to client: {e}. Removing client.")
            # Schedule removal outside the loop if needed, or handle carefully
            # For simplicity, remove directly here, assuming `remove_client` is thread-safe enough
            remove_client(client_conn)

def remove_client(conn):
    """Removes a client connection and handles associated cleanup. MUST handle being called potentially multiple times for the same conn."""
    global game_started, last_timer_update, clients, player_assignments, game_over, winner
    with game_state_lock:
        if conn in clients:
            clients.remove(conn)
            disconnected_color = player_assignments.pop(conn, None) # Use pop with default

            if disconnected_color:
                print(f"Player {disconnected_color} disconnected.")
                # If a player disconnects during the game, the other player wins
                if len(clients) == 1 and game_started and not game_over:
                    remaining_conn = clients[0] # The only one left
                    remaining_color = player_assignments.get(remaining_conn)
                    winner = remaining_color # The remaining player wins
                    game_over = True
                    print(f"Game Over! {winner.capitalize()} wins by opponent disconnection.")
                    # Trigger a final broadcast to inform the winner
                    needs_broadcast_on_disconnect = True
                elif len(clients) < MAX_PLAYERS:
                     print("Waiting for new players...")
                     # Decide if game state should reset etc. For now, just waits.
                     game_started = False # Stop timers etc.
                     last_timer_update = None
                     # Reset game state? Optional.
                     # reset_game_state() # --> You would need to implement this function
                     needs_broadcast_on_disconnect = True # Inform remaining player game stopped/waiting
                else: # Both players still connected somehow? Should not happen often here.
                    needs_broadcast_on_disconnect = False
            else:
                print("Spectator or unassigned client disconnected.")
                needs_broadcast_on_disconnect = False

            # Close the socket outside the lock if possible, though usually done in handle_client exit
            try:
                 conn.close()
                 print(f"Socket for {disconnected_color or 'unknown'} closed.")
            except (socket.error, AttributeError):
                 pass # Ignore errors if already closed or invalid

    # Perform broadcast outside the lock if needed after state changes
    if needs_broadcast_on_disconnect:
        # Small delay might be needed for client thread to potentially exit cleanly first
        # time.sleep(0.1)
        broadcast_state()


def handle_client(conn, addr):
    """Handles communication with a single client."""
    global turn_step, game_over, winner
    global white_pieces, white_locations, black_pieces, black_locations
    global captured_pieces_white, captured_pieces_black, chat_history
    global white_options, black_options, last_timer_update, game_started # Make sure all globals are accessible

    player_color = "Unknown" # Default
    try:
        with game_state_lock:
            player_color = player_assignments.get(conn, "Unknown")
            print(f"Player {player_color} assigned to connection from {addr}")

        # Send initial color assignment
        conn.sendall(pickle.dumps(player_color))

        # Send initial game state (timers will be full initially, handled by periodic updates)
        # The initial state broadcast might happen via the periodic update or the connection of the second player
        # Send immediately for this client though
        initial_state_data = pickle.dumps(get_current_game_state())
        conn.sendall(initial_state_data)

    except (socket.error, pickle.PicklingError, BrokenPipeError) as e:
        print(f"Error during initial setup for {addr}: {e}")
        remove_client(conn)
        return

    buffer = b""
    while True:
        try:
            # Use non-blocking recv with timeout or select for better handling?
            # For simplicity, stick to blocking recv for now.
            chunk = conn.recv(4096 * 2) # Slightly larger buffer
            if not chunk:
                print(f"Client {player_color} ({addr}) disconnected (empty data).")
                remove_client(conn)
                break

            buffer += chunk

            # Process potential multiple messages in buffer (simple framing assumption)
            while True:
                try:
                    message, buffer = pickle.loads(buffer), b'' # Assume one message per buffer for now
                    # Proper framing needed for robustness: length prefix or delimiter

                    if not isinstance(message, dict) or 'type' not in message:
                        print(f"Invalid message format from {player_color}: {message}")
                        continue # Skip invalid message

                    message_type = message['type']
                    message_data = message.get('data') # Use .get for safety
                    needs_broadcast = False # Flag to check if state needs update

                    # --- Acquire lock only when modifying shared state ---
                    with game_state_lock:
                        current_player_color_locked = player_assignments.get(conn) # Re-check assignment
                        if not current_player_color_locked or current_player_color_locked == "Unknown":
                            print(f"Ignoring message from unassigned/disconnected client {addr}")
                            # Maybe force disconnect here?
                            needs_broadcast = False
                            continue # Skip processing


                        # --- Handle MOVE ---
                        if message_type == 'move':
                            if game_over:
                                print("Game is over, ignoring move.")
                                continue

                            is_white_turn = (turn_step < 2)
                            active_player_color = 'white' if is_white_turn else 'black'

                            if current_player_color_locked != active_player_color:
                                print(f"Invalid move: Not {current_player_color_locked}'s turn (It's {active_player_color}'s turn).")
                                continue # Ignore the move

                            # --- Move Validation ---
                            if not isinstance(message_data, (list, tuple)) or len(message_data) != 2:
                                print(f"Invalid move data format: {message_data}")
                                continue

                            selection_index, target_coords = message_data

                            # Ensure target_coords is a tuple of two integers
                            if not isinstance(target_coords, (list, tuple)) or len(target_coords) != 2 or \
                               not all(isinstance(c, int) for c in target_coords):
                                print(f"Invalid target coordinates format: {target_coords}")
                                continue

                            valid_move_found = False
                            pieces_list = white_pieces if active_player_color == 'white' else black_pieces
                            locations_list = white_locations if active_player_color == 'white' else black_locations

                            # Re-calculate options inside the lock just before validating
                            current_options = check_options(pieces_list, locations_list, active_player_color)

                            if 0 <= selection_index < len(pieces_list) and 0 <= selection_index < len(current_options):
                                piece_options = current_options[selection_index]
                                if target_coords in piece_options:
                                    valid_move_found = True
                                else:
                                    print(f"Invalid move: {target_coords} not in options {piece_options} for {active_player_color} piece {pieces_list[selection_index]} at index {selection_index}")
                            else:
                                print(f"Invalid selection index for {active_player_color}: {selection_index} (len={len(pieces_list)}, len_opts={len(current_options)})")


                            # --- Execute Valid Move ---
                            if valid_move_found:
                                print(f"Executing valid move for {active_player_color}: piece {selection_index} to {target_coords}")

                                # --- Timer handling: Reset timestamp for the *next* turn ---
                                # The time used for the current turn is accounted for by elapsed time until this point.
                                last_timer_update = time.time() # Reset timer start for the opponent

                                # --- Piece Capture Logic ---
                                opponent_color = 'black' if active_player_color == 'white' else 'white'
                                opponent_locations = black_locations if opponent_color == 'black' else white_locations
                                opponent_pieces = black_pieces if opponent_color == 'black' else white_pieces
                                captured_list = captured_pieces_white if active_player_color == 'white' else captured_pieces_black

                                if target_coords in opponent_locations:
                                    opponent_piece_index = opponent_locations.index(target_coords)
                                    captured_piece = opponent_pieces.pop(opponent_piece_index)
                                    captured_list.append(captured_piece)
                                    opponent_locations.pop(opponent_piece_index)
                                    print(f"{active_player_color.capitalize()} captured {captured_piece}")
                                    if captured_piece == 'king':
                                        winner = active_player_color
                                        game_over = True
                                        print(f"Game Over! {winner.capitalize()} wins by capturing king!")

                                # --- Move the piece ---
                                locations_list[selection_index] = target_coords

                                # --- Pawn Promotion ---
                                piece_moved = pieces_list[selection_index]
                                promote_row = 7 if active_player_color == 'white' else 0
                                if piece_moved == 'pawn' and target_coords[1] == promote_row:
                                    pieces_list[selection_index] = 'queen' # Auto-promote to queen
                                    print(f"{active_player_color.capitalize()} pawn promoted to Queen!")

                                # --- Switch turn ---
                                turn_step = (turn_step + 2) % 4 # Toggle between 0/1 (white) and 2/3 (black) phases

                                # --- Update options for the next state (Important!) ---
                                white_options = check_options(white_pieces, white_locations, 'white')
                                black_options = check_options(black_pieces, black_locations, 'black')

                                needs_broadcast = True # State changed

                            else: # Move was invalid
                                print(f"Move {message_data} from {current_player_color_locked} was invalid.")
                                needs_broadcast = False # Don't broadcast on invalid move attempt

                        # --- Handle CHAT ---
                        elif message_type == 'chat':
                            chat_message = message_data
                            # Basic validation
                            if isinstance(chat_message, dict) and \
                               chat_message.get('sender') == current_player_color_locked and \
                               chat_message.get('text'):

                                # Ensure timestamp exists (client should add it ideally)
                                if 'timestamp' not in chat_message:
                                    chat_message['timestamp'] = datetime.now().strftime("%I:%M %p")

                                chat_history.append(chat_message)
                                # Limit chat history size
                                if len(chat_history) > 100:
                                    chat_history.pop(0)
                                print(f"Chat from {current_player_color_locked}: {chat_message['text']}")
                                needs_broadcast = True # Chat is a state change
                            else:
                                print(f"Invalid chat message format/sender from {current_player_color_locked}: {chat_message}")
                                needs_broadcast = False

                        # --- Add other message types if needed ---

                    # --- End of lock scope ---

                    # --- Broadcast state IF needed (outside the lock) ---
                    if needs_broadcast:
                        # print("Broadcasting state after event...") # Debug
                        broadcast_state()

                except (pickle.UnpicklingError, EOFError, IndexError, TypeError):
                    # Not enough data in buffer for a complete message, break inner loop
                    break
                except Exception as e: # Catch unexpected errors during message processing
                    print(f"Error processing message from {player_color}: {e}")
                    import traceback
                    traceback.print_exc()
                    buffer = b'' # Clear buffer on error? Risky.
                    # Consider disconnecting the client on processing errors
                    # remove_client(conn)
                    # break # Break inner loop

        except (socket.error, ConnectionResetError, BrokenPipeError) as e:
            print(f"Network error with client {player_color} ({addr}): {e}")
            remove_client(conn)
            break
        except Exception as e: # Catch broader exceptions in network loop
            print(f"Unexpected error handling client {player_color} ({addr}): {e}")
            import traceback
            traceback.print_exc()
            remove_client(conn)
            break

    print(f"Client handler thread for {addr} finished.")
    # Ensure socket is closed on thread exit, though remove_client might have done it
    try:
        conn.close()
    except socket.error:
        pass


# --- Main Server Loop ---
while True:
    # --- Connection Acceptance Logic ---
    if len(clients) < MAX_PLAYERS:
        try:
            # Set a timeout for accept to allow periodic checks later if needed
            server_socket.settimeout(0.5) # Timeout after 0.5 seconds
            print(f"Waiting for player {len(clients) + 1}/{MAX_PLAYERS}...")
            conn, addr = server_socket.accept()
            print(f"Accepted connection from {addr}")
            server_socket.settimeout(None) # Remove timeout after successful accept

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
                        last_periodic_broadcast_time = time.time() # Init broadcast timestamp
                        # Initial broadcast happens in handle_client now, or subsequent periodic one
                else:
                    # Server became full between check and accept? Rare but possible.
                    print(f"Connection attempt from {addr} refused: Server full.")
                    try:
                        conn.sendall(pickle.dumps("error:server_full"))
                    except socket.error as send_err:
                        print(f"Could not send 'server_full' message: {send_err}")
                    finally:
                        conn.close()
        except socket.timeout:
            # No connection attempt within the timeout, just continue loop for periodic checks
            pass
        except socket.error as e:
            print(f"Error accepting connection: {e}")
            time.sleep(1) # Avoid busy-waiting on persistent accept error
            continue
        finally:
            server_socket.settimeout(None) # Ensure timeout is removed if accept failed/timed out

    # --- Periodic Timer Update and Broadcast ---
    current_time = time.time()
    # Check if game is active and enough time has passed since last *periodic* broadcast
    if game_started and not game_over and \
       (current_time - last_periodic_broadcast_time >= BROADCAST_INTERVAL):

        state_changed_by_timer = False
        with game_state_lock:
            state_changed_by_timer = update_timers() # Update timers, check game over

        # Broadcast if timer ticked or game ended on time
        # Even if timer didn't change much, broadcast keeps clients synced
        # print(f"Periodic check: game_started={game_started}, game_over={game_over}, state_changed={state_changed_by_timer}") # Debug
        broadcast_state()
        last_periodic_broadcast_time = current_time # Reset the periodic broadcast timer

    # --- Small sleep to prevent busy-waiting in the main loop ---
    # Especially important when the server is full and just doing periodic checks
    time.sleep(0.1) # Sleep for 100ms

# --- End of server (won't be reached in this loop structure) ---
# server_socket.close() # Consider adding cleanup if the loop could exit
