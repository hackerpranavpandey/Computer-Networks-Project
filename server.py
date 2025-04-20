# ######## server.py (Multi-Game Version with Framing - Complete) ########
import socket
import threading
import pickle
import time
from datetime import datetime
import uuid # Using UUID for more robust game IDs
import struct # For message framing

# --- Constants ---
INITIAL_TIME_SECONDS = 1200.0 # 20 minutes
BROADCAST_INTERVAL = 1.0 # Seconds between state broadcasts for timer updates
SERVER_IP = '0.0.0.0'
PORT = 5555
MAX_PLAYERS_OVERALL = 10 # Max connections server will handle
MAX_PLAYERS_PER_GAME = 2
HEADER_SIZE = struct.calcsize('>I') # Size of the length prefix (4 bytes)

# --- Game Logic Helper Functions ---
def check_options(pieces, locations, turn_color, white_locations_global, black_locations_global):
    moves_list = []
    all_moves_list = []
    current_white_locations = white_locations_global
    current_black_locations = black_locations_global

    for i in range(len(pieces)):
        if not (0 <= i < len(locations)): continue # Safety check
        location = locations[i]
        piece = pieces[i]
        if piece not in ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']: continue

        w_locs_context = current_white_locations
        b_locs_context = current_black_locations

        if piece == 'pawn':
            moves_list = check_pawn(location, turn_color, w_locs_context, b_locs_context)
        elif piece == 'rook':
            moves_list = check_rook(location, turn_color, w_locs_context, b_locs_context)
        elif piece == 'knight':
            moves_list = check_knight(location, turn_color, w_locs_context, b_locs_context)
        elif piece == 'bishop':
            moves_list = check_bishop(location, turn_color, w_locs_context, b_locs_context)
        elif piece == 'queen':
            moves_list = check_queen(location, turn_color, w_locs_context, b_locs_context)
        elif piece == 'king':
            moves_list = check_king(location, turn_color, w_locs_context, b_locs_context)
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
           (position[0], position[1] + 2) not in b_locs and position[1] < 6:
            moves_list.append((position[0], position[1] + 2))
        if position[0] < 7 and position[1] < 7 and (position[0] + 1, position[1] + 1) in b_locs:
            moves_list.append((position[0] + 1, position[1] + 1))
        if position[0] > 0 and position[1] < 7 and (position[0] - 1, position[1] + 1) in b_locs:
            moves_list.append((position[0] - 1, position[1] + 1))
    else: # Black's turn
        if (position[0], position[1] - 1) not in w_locs and \
           (position[0], position[1] - 1) not in b_locs and position[1] > 0:
            moves_list.append((position[0], position[1] - 1))
        if position[1] == 6 and \
           (position[0], position[1] - 1) not in w_locs and \
           (position[0], position[1] - 1) not in b_locs and \
           (position[0], position[1] - 2) not in w_locs and \
           (position[0], position[1] - 2) not in b_locs and position[1] > 1:
            moves_list.append((position[0], position[1] - 2))
        if position[0] < 7 and position[1] > 0 and (position[0] + 1, position[1] - 1) in w_locs:
            moves_list.append((position[0] + 1, position[1] - 1))
        if position[0] > 0 and position[1] > 0 and (position[0] - 1, position[1] - 1) in w_locs:
            moves_list.append((position[0] - 1, position[1] - 1))
    return moves_list

def check_rook(position, color, w_locs, b_locs):
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    enemies_list = b_locs if color == 'white' else w_locs
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    for dx, dy in directions:
        for i in range(1, 8):
            target_x, target_y = position[0] + i * dx, position[1] + i * dy
            target_coords = (target_x, target_y)
            if 0 <= target_x <= 7 and 0 <= target_y <= 7:
                if target_coords not in friends_list:
                    moves_list.append(target_coords)
                    if target_coords in enemies_list: break
                else: break
            else: break
    return moves_list

def check_knight(position, color, w_locs, b_locs):
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    targets = [(1, 2), (1, -2), (2, 1), (2, -1), (-1, 2), (-1, -2), (-2, 1), (-2, -1)]
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
    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for dx, dy in directions:
        for i in range(1, 8):
            target_x, target_y = position[0] + i * dx, position[1] + i * dy
            target_coords = (target_x, target_y)
            if 0 <= target_x <= 7 and 0 <= target_y <= 7:
                if target_coords not in friends_list:
                    moves_list.append(target_coords)
                    if target_coords in enemies_list: break
                else: break
            else: break
    return moves_list

def check_queen(position, color, w_locs, b_locs):
    moves_list = check_bishop(position, color, w_locs, b_locs)
    moves_list.extend(check_rook(position, color, w_locs, b_locs))
    return moves_list

def check_king(position, color, w_locs, b_locs):
    moves_list = []
    friends_list = w_locs if color == 'white' else b_locs
    targets = [(1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1)]
    for dx, dy in targets:
        target_x, target_y = position[0] + dx, position[1] + dy
        target_coords = (target_x, target_y)
        if 0 <= target_x <= 7 and 0 <= target_y <= 7:
            if target_coords not in friends_list:
                moves_list.append(target_coords)
    # Add check validation and castling later
    return moves_list


# --- Game Class ---
class Game:
    def __init__(self, game_id):
        self.game_id = game_id
        self.players = {} # {conn: 'white'/'black', conn2: 'black'/'white'}
        self.player_conns = {'white': None, 'black': None}
        self.white_pieces = []
        self.white_locations = []
        self.black_pieces = []
        self.black_locations = []
        self.captured_pieces_white = []
        self.captured_pieces_black = []
        self.chat_history = []
        self.turn_step = 0 # 0,1: White; 2,3: Black
        self.winner = ''
        self.game_over = False
        self.game_started = False
        self.white_time = INITIAL_TIME_SECONDS
        self.black_time = INITIAL_TIME_SECONDS
        self.last_timer_update = None
        self.white_options = []
        self.black_options = []
        self.game_state_lock = threading.Lock()
        self._initialize_board()
        print(f"Game {self.game_id}: Initialized.")

    def _initialize_board(self):
        # Called within lock during __init__
        self.white_pieces = ['rook', 'knight', 'bishop', 'king', 'queen', 'bishop', 'knight', 'rook',
                        'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
        self.white_locations = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
                           (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)]
        self.black_pieces = ['rook', 'knight', 'bishop', 'king', 'queen', 'bishop', 'knight', 'rook',
                        'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
        self.black_locations = [(0, 7), (1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7),
                           (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6)]
        self.captured_pieces_white = []
        self.captured_pieces_black = []
        self.chat_history = []
        self.turn_step = 0
        self.winner = ''
        self.game_over = False
        self.game_started = False
        self.white_time = INITIAL_TIME_SECONDS
        self.black_time = INITIAL_TIME_SECONDS
        self.last_timer_update = None
        self.white_options = check_options(self.white_pieces, self.white_locations, 'white', self.white_locations, self.black_locations)
        self.black_options = check_options(self.black_pieces, self.black_locations, 'black', self.white_locations, self.black_locations)

    def add_player(self, conn, color):
        # Called within pairing_lock or game's lock context usually
        if color not in self.player_conns or self.player_conns[color] is None:
            self.players[conn] = color
            self.player_conns[color] = conn
            peer = "unknown"
            try: peer = conn.getpeername()
            except: pass
            print(f"Game {self.game_id}: Player {color} assigned to {peer}")
            return True
        else:
            print(f"Game {self.game_id}: Error - Color {color} already assigned.")
            return False

    def remove_player(self, conn):
        # Called within games_lock context usually
        needs_broadcast = False
        disconnected_color = None
        with self.game_state_lock: # Need internal lock to modify player dicts/state
            disconnected_color = self.players.pop(conn, None)
            if disconnected_color:
                print(f"Game {self.game_id}: Player {disconnected_color} removed internally.")
                self.player_conns[disconnected_color] = None
                if self.game_started and not self.game_over:
                    self.game_over = True
                    self.winner = 'black' if disconnected_color == 'white' else 'white'
                    print(f"Game {self.game_id}: Over! {self.winner.capitalize()} wins by opponent disconnection.")
                    needs_broadcast = True
                elif not self.game_started:
                    print(f"Game {self.game_id}: Player left before start.")
                    self.game_over = True # Mark as over to facilitate cleanup
            else:
                # print(f"Game {self.game_id}: Conn not found in players list during removal.") # Reduce noise
                pass
        return needs_broadcast, disconnected_color

    def is_ready(self):
        # Called within lock context usually
        return self.player_conns.get('white') is not None and self.player_conns.get('black') is not None

    def start_game(self):
        # Called within lock context usually
        with self.game_state_lock:
            if self.is_ready() and not self.game_started:
                self.game_started = True
                self.last_timer_update = time.time()
                print(f"Game {self.game_id}: Started.")
                return True
            elif self.game_started:
                print(f"Game {self.game_id}: Already started.")
                return True # Idempotent?
            else:
                print(f"Game {self.game_id}: Cannot start, not ready.")
                return False

    def update_timers(self):
        game_ended_by_time = False
        with self.game_state_lock:
            if not self.game_started or self.game_over or self.last_timer_update is None:
                return False

            now = time.time()
            elapsed = now - self.last_timer_update
            timer_changed = False

            if elapsed > 0:
                if self.turn_step < 2: # White's turn
                    self.white_time -= elapsed
                    timer_changed = True
                    if self.white_time <= 0:
                        self.white_time = 0
                        if not self.game_over:
                            self.winner = 'black'
                            self.game_over = True
                            game_ended_by_time = True
                            print(f"Game {self.game_id}: Over! Black wins on time!")
                else: # Black's turn
                    self.black_time -= elapsed
                    timer_changed = True
                    if self.black_time <= 0:
                        self.black_time = 0
                        if not self.game_over:
                            self.winner = 'white'
                            self.game_over = True
                            game_ended_by_time = True
                            print(f"Game {self.game_id}: Over! White wins on time!")

            self.last_timer_update = now # Update timestamp regardless
        return game_ended_by_time

    def apply_move(self, player_color, selection_index, target_coords):
        with self.game_state_lock:
            if self.game_over: return False

            is_white_turn = (self.turn_step < 2)
            active_player_color = 'white' if is_white_turn else 'black'

            if player_color != active_player_color:
                print(f"Game {self.game_id}: Invalid move - Not {player_color}'s turn.")
                return False

            pieces_list = self.white_pieces if active_player_color == 'white' else self.black_pieces
            locations_list = self.white_locations if active_player_color == 'white' else self.black_locations
            # Use the *current* options stored in the game state
            options_list = self.white_options if active_player_color == 'white' else self.black_options

            valid_move_found = False
            if 0 <= selection_index < len(pieces_list) and 0 <= selection_index < len(options_list):
                 # Ensure options_list[selection_index] is actually a list of moves
                 if isinstance(options_list[selection_index], list):
                     piece_options = options_list[selection_index]
                     if target_coords in piece_options:
                         valid_move_found = True
                     else:
                         print(f"Game {self.game_id}: Invalid move {target_coords} for {active_player_color} piece index {selection_index}. Options: {piece_options}")
                 else:
                     print(f"Game {self.game_id}: Options for piece index {selection_index} is not a list: {options_list[selection_index]}")
            else:
                print(f"Game {self.game_id}: Invalid selection index {selection_index} for {active_player_color}. Piece count: {len(pieces_list)}, Options count: {len(options_list)}")


            if not valid_move_found: return False

            # Execute Move
            print(f"Game {self.game_id}: Applying valid move for {active_player_color} from {locations_list[selection_index]} to {target_coords}")
            self.last_timer_update = time.time()

            # Capture Logic
            opponent_color = 'black' if active_player_color == 'white' else 'white'
            opponent_locations = self.black_locations if opponent_color == 'black' else self.white_locations
            opponent_pieces = self.black_pieces if opponent_color == 'black' else self.white_pieces
            captured_list = self.captured_pieces_white if active_player_color == 'white' else self.captured_pieces_black

            if target_coords in opponent_locations:
                try:
                    opponent_piece_index = opponent_locations.index(target_coords)
                    # Ensure indices align before popping
                    if 0 <= opponent_piece_index < len(opponent_pieces):
                         captured_piece = opponent_pieces.pop(opponent_piece_index)
                         captured_list.append(captured_piece)
                         opponent_locations.pop(opponent_piece_index) # Pop location *after* piece
                         print(f"Game {self.game_id}: {active_player_color.capitalize()} captured {captured_piece}")
                         if captured_piece == 'king':
                             self.winner = active_player_color
                             self.game_over = True
                             print(f"Game {self.game_id}: Over! {self.winner.capitalize()} wins by capturing king!")
                    else:
                         print(f"Game {self.game_id}: Error - Opponent index mismatch during capture. Idx: {opponent_piece_index}, Len: {len(opponent_pieces)}")
                except ValueError:
                     print(f"Game {self.game_id}: Error - Target coords {target_coords} not found in opponent locations during capture.")


            # Move Piece (ensure index is valid)
            if 0 <= selection_index < len(locations_list):
                 locations_list[selection_index] = target_coords
            else:
                 print(f"Game {self.game_id}: Error - selection_index {selection_index} out of bounds for locations_list (len {len(locations_list)}) during move.")
                 return False # Abort move if index is bad

            # Promotion
            if 0 <= selection_index < len(pieces_list): # Check index again before accessing piece
                 piece_moved = pieces_list[selection_index]
                 promote_row = 7 if active_player_color == 'white' else 0
                 if piece_moved == 'pawn' and target_coords[1] == promote_row:
                     pieces_list[selection_index] = 'queen'
                     print(f"Game {self.game_id}: {active_player_color.capitalize()} pawn promoted!")
            else:
                  print(f"Game {self.game_id}: Error - selection_index {selection_index} out of bounds for pieces_list (len {len(pieces_list)}) during promotion check.")


            # Switch Turn
            self.turn_step = (self.turn_step + 2) % 4

            # Recalculate options
            self.white_options = check_options(self.white_pieces, self.white_locations, 'white', self.white_locations, self.black_locations)
            self.black_options = check_options(self.black_pieces, self.black_locations, 'black', self.white_locations, self.black_locations)

            return True

    def add_chat_message(self, sender_color, text, timestamp):
        with self.game_state_lock:
            if self.game_over: return False
            chat_message = {'sender': sender_color, 'text': text, 'timestamp': timestamp}
            self.chat_history.append(chat_message)
            if len(self.chat_history) > 100:
                self.chat_history.pop(0)
            print(f"Game {self.game_id} Chat from {sender_color}: {text}")
            return True

    def get_state(self):
        with self.game_state_lock:
            return {
                'game_id': self.game_id,
                'white_pieces': self.white_pieces[:],
                'white_locations': self.white_locations[:],
                'black_pieces': self.black_pieces[:],
                'black_locations': self.black_locations[:],
                'captured_white': self.captured_pieces_white[:],
                'captured_black': self.captured_pieces_black[:],
                'turn_step': self.turn_step,
                'game_over': self.game_over,
                'winner': self.winner,
                'white_options': self.white_options[:], # Shallow copy options lists
                'black_options': self.black_options[:],
                'chat_history': self.chat_history[:],
                'white_time': self.white_time,
                'black_time': self.black_time,
                'game_started': self.game_started
            }

    def get_player_connections(self):
        with self.game_state_lock:
            # Return only non-None connections
            return [conn for conn in self.players.keys() if conn and conn.fileno() != -1]


# --- Server Globals ---
games = {} # {game_id: Game_instance}
waiting_players = {} # {conn: addr}
client_to_game = {} # {conn: game_id}
server_socket = None
pairing_lock = threading.Lock()
games_lock = threading.Lock()
last_periodic_broadcast_time = 0

# --- Server Functions ---

def send_framed_message(sock, message_obj):
    """Serializes message object, prefixes with length, and sends."""
    try:
        pickled_data = pickle.dumps(message_obj)
        message_length = len(pickled_data)
        length_prefix = struct.pack('>I', message_length)
        sock.sendall(length_prefix + pickled_data)
        return True
    except (socket.error, BrokenPipeError, pickle.PicklingError, struct.error, AttributeError) as e:
        # AttributeError can happen if sock is already closed/invalid
        # print(f"Error sending framed message: {e}") # Reduce noise
        return False
    except Exception as e:
        print(f"Unexpected error in send_framed_message: {e}")
        return False


def broadcast_game_state(game_id):
    """Sends the state of a specific game to its participants using framing."""
    global games
    game = None
    with games_lock:
        game = games.get(game_id)
        if not game: return

    try:
        state_dict = game.get_state()
        player_conns = game.get_player_connections() # Needs internal lock
    except Exception as e:
        print(f"Error getting state/conns for game {game_id} (broadcast): {e}")
        return

    if not player_conns: return

    disconnected_during_broadcast = []
    for conn in player_conns:
        if not send_framed_message(conn, state_dict):
            peer = "unknown"
            try: peer = conn.getpeername()
            except: pass
            print(f"Failed to send state to client {peer} in game {game_id}. Marking for removal.")
            disconnected_during_broadcast.append(conn)

    for conn_to_remove in disconnected_during_broadcast:
        with games_lock:
             if game_id in games: # Check game still exists
                  remove_client_from_game(conn_to_remove, game_id) # remove_client needs games_lock


def remove_client_from_game(conn, game_id):
    """Handles removing a client, updating game state, and cleaning up mappings."""
    global games, client_to_game
    # Assumes games_lock is held externally when called

    game_ended_by_disconnect = False
    disconnected_color = None
    game_exists_during_removal = False

    # 1. Remove from client_to_game mapping (needs separate lock)
    with pairing_lock:
        client_to_game.pop(conn, None)

    # 2. Remove player from the Game object (games_lock is already held)
    game = games.get(game_id)
    if game:
        game_exists_during_removal = True
        needs_broadcast, disconnected_color = game.remove_player(conn) # Needs internal lock
        if needs_broadcast:
            game_ended_by_disconnect = True

        player_conns_after_remove = game.get_player_connections() # Needs internal lock
        if not player_conns_after_remove or game.game_over:
             print(f"Game {game_id} is now empty or over. Removing from active games.")
             games.pop(game_id, None) # Remove game instance
             game_exists_during_removal = False
    # else: Game already removed

    # 3. Close the connection (outside locks if possible, but difficult here)
    peername = "unknown"
    try: peername = conn.getpeername()
    except: pass
    try:
        conn.close()
        print(f"Closed connection for {disconnected_color or 'unknown'} from {peername} (Game: {game_id})")
    except (socket.error, OSError): pass

    # 4. Broadcast final state (outside lock if was possible, but difficult)
    # If we broadcast here, it must be done carefully to avoid deadlock if broadcast calls remove_client again
    # For now, rely on the next periodic update or calling function to handle broadcast if needed.
    # if game_ended_by_disconnect and game_exists_during_removal:
    #    print(f"Triggering final broadcast for game {game_id} due to disconnect.")
    #    # Potential issue: broadcast_game_state might try to re-acquire games_lock
    #    # Consider scheduling broadcast outside the lock.


def handle_client(conn, addr):
    """Handles initial setup and finds/assigns client to a game."""
    global waiting_players, games, client_to_game
    print(f"Handling connection from {addr}")
    assigned_game_id = None
    player_color = None
    initial_send_failed = False

    try:
        with pairing_lock:
            if waiting_players:
                # Pair found!
                wait_conn, wait_addr = waiting_players.popitem()
                print(f"Pairing {addr} with waiting player {wait_addr}")

                game_id = str(uuid.uuid4())
                new_game = Game(game_id)

                # Assign players and add to game object (needs internal game lock)
                with new_game.game_state_lock:
                    add_ok_1 = new_game.add_player(wait_conn, 'white')
                    add_ok_2 = new_game.add_player(conn, 'black')

                if not (add_ok_1 and add_ok_2):
                     print(f"Error adding players to game {game_id}.")
                     # Cleanup
                     try: wait_conn.close()
                     except: pass
                     try: conn.close()
                     except: pass
                     return # Exit thread

                # Update mappings
                client_to_game[wait_conn] = game_id
                client_to_game[conn] = game_id

                with games_lock:
                    games[game_id] = new_game
                    print(f"Game {game_id} created.")

                assigned_game_id = game_id
                player_color = 'black'

                # Start game (needs internal game lock)
                game_started_ok = new_game.start_game()

                # Send color assignments using framing
                if not send_framed_message(wait_conn, 'white'): initial_send_failed = True
                if not send_framed_message(conn, 'black'): initial_send_failed = True

                if initial_send_failed:
                    print(f"Error sending initial assignments for game {game_id}.")
                    # Enhanced cleanup
                    client_to_game.pop(wait_conn, None)
                    client_to_game.pop(conn, None)
                    with games_lock: games.pop(game_id, None)
                    try: wait_conn.close()
                    except: pass
                    try: conn.close()
                    except: pass
                    return # Exit thread
                else:
                     # Initial broadcast (safe to call here)
                     print(f"Broadcasting initial state for game {game_id}")
                     broadcast_game_state(game_id)

            else:
                # Add to waiting queue
                waiting_players[conn] = addr
                print(f"Added {addr} to waiting queue.")
                # Optionally send waiting status
                # send_framed_message(conn, {"status": "waiting"})

        # --- Continue to communication loop ---
        if initial_send_failed: return

        if assigned_game_id and player_color:
            run_game_communication(conn, addr, assigned_game_id, player_color)
        elif conn in waiting_players: # Check if still waiting
            run_game_communication(conn, addr, None, None) # Loop handles waiting state
        # else: Pairing failed, already cleaned up

    except Exception as e:
        print(f"Unexpected error during client handling/pairing for {addr}: {e}")
        import traceback
        traceback.print_exc()
        # General cleanup
        with pairing_lock:
            waiting_players.pop(conn, None)
        final_game_id = None
        with pairing_lock: final_game_id = client_to_game.get(conn)
        if final_game_id:
             with games_lock: remove_client_from_game(conn, final_game_id)
        else:
             try:
                 if conn and conn.fileno() != -1: conn.close()
             except: pass


def run_game_communication(conn, addr, initial_game_id, initial_player_color):
    """Handles receiving messages from a client and interacting with their game."""
    global client_to_game, games
    current_game_id = initial_game_id
    player_color = initial_player_color
    buffer = b""

    while True:
        try:
            chunk = conn.recv(4096)
            if not chunk:
                print(f"Client {addr} (Color: {player_color}, Game: {current_game_id}) disconnected (empty data).")
                break

            buffer += chunk

            while True: # Process buffer for simple pickle
                try:
                    message, buffer = pickle.loads(buffer), b''
                except (pickle.UnpicklingError, EOFError, IndexError, TypeError, ValueError):
                    break # Need more data

                # Get current game ID for this client
                with pairing_lock:
                    current_game_id = client_to_game.get(conn)

                if not current_game_id: continue # Still waiting

                # Get game instance
                game = None
                with games_lock:
                    game = games.get(current_game_id)

                if not game: break # Game ended/removed while processing

                # Get player color within game context
                # No lock needed if Game.players is read-only here, but safer with game lock
                with game.game_state_lock:
                     player_color = game.players.get(conn)
                if not player_color: break # Should not happen if assigned


                # Process Message
                if not isinstance(message, dict) or 'type' not in message: continue

                message_type = message['type']
                message_data = message.get('data')
                needs_broadcast = False

                if message_type == 'move':
                    if isinstance(message_data, (list, tuple)) and len(message_data) == 2:
                         selection_index, target_coords = message_data
                         if isinstance(target_coords, (list, tuple)) and len(target_coords) == 2 and \
                            all(isinstance(c, int) for c in target_coords):
                              # apply_move handles its own locking
                              move_applied = game.apply_move(player_color, selection_index, target_coords)
                              if move_applied: needs_broadcast = True
                         # else: Invalid target coords format
                    # else: Invalid move data format

                elif message_type == 'chat':
                    if isinstance(message_data, dict) and message_data.get('text'):
                         timestamp = message_data.get('timestamp', datetime.now().strftime("%I:%M %p"))
                         text = message_data['text']
                         # add_chat_message handles its own locking
                         chat_added = game.add_chat_message(player_color, text, timestamp)
                         if chat_added: needs_broadcast = True
                    # else: Invalid chat data format

                # Broadcast if needed
                if needs_broadcast:
                    broadcast_game_state(current_game_id)

        except (socket.error, ConnectionResetError, BrokenPipeError) as e:
            print(f"Network error with client {addr} (Game: {current_game_id}): {e}")
            break
        except Exception as e:
            print(f"Unexpected error processing data for client {addr} (Game: {current_game_id}): {e}")
            import traceback
            traceback.print_exc()
            break

    # Cleanup
    print(f"Communication loop finished for {addr}.")
    final_game_id = None
    with pairing_lock:
        final_game_id = client_to_game.get(conn)
        waiting_players.pop(conn, None)

    if final_game_id:
        with games_lock: # Need lock to call remove_client
             if final_game_id in games: # Check game exists before removal
                  remove_client_from_game(conn, final_game_id)
             else: # Game already gone, just close socket if needed
                 try:
                      if conn and conn.fileno() != -1: conn.close()
                 except: pass
    else:
        # Was waiting or already removed
        try:
            if conn and conn.fileno() != -1: conn.close()
        except: pass


def periodic_updates():
    """Periodically updates timers for all active games and broadcasts."""
    global games, last_periodic_broadcast_time
    while True:
        try:
            start_time = time.time()
            games_to_update = []
            with games_lock: games_to_update = list(games.keys())

            games_needing_broadcast = set()

            for game_id in games_to_update:
                game = None # Reset game var
                with games_lock: # Need lock to safely get game instance
                    game = games.get(game_id)
                    if not game: continue # Skip if game was removed

                # update_timers handles its own internal lock
                game_ended_by_time = game.update_timers()
                if game_ended_by_time:
                    games_needing_broadcast.add(game_id)

            current_time = time.time()
            if current_time - last_periodic_broadcast_time >= BROADCAST_INTERVAL:
                 for game_id in games_to_update:
                      game = None
                      with games_lock: game = games.get(game_id) # Check again if game exists
                      # Broadcast state if game is active
                      if game and game.game_started and not game.game_over:
                           games_needing_broadcast.add(game_id)
                 last_periodic_broadcast_time = current_time

            if games_needing_broadcast:
                 # print(f"Periodic: Broadcasting for {games_needing_broadcast}") # Debug
                 for game_id in games_needing_broadcast:
                      broadcast_game_state(game_id) # Handles its own locks internally

            elapsed = time.time() - start_time
            sleep_time = max(0.1, BROADCAST_INTERVAL - elapsed)
            time.sleep(sleep_time)

        except Exception as e:
            print(f"!!! FATAL ERROR IN PERIODIC UPDATE THREAD: {e} !!!")
            import traceback
            traceback.print_exc()
            time.sleep(5)


# --- Main Server Execution ---
if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((SERVER_IP, PORT))
        server_socket.listen(MAX_PLAYERS_OVERALL)
        print(f"Chess Server Started on {SERVER_IP}:{PORT}. Waiting for connections...")
    except socket.error as e:
        print(f"Socket bind/listen error: {e}")
        exit()

    update_thread = threading.Thread(target=periodic_updates, daemon=True)
    update_thread.start()
    print("Periodic timer update thread started.")

    while True:
        try:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()
        except socket.error as e:
            print(f"Error accepting connection: {e}")
            time.sleep(0.5) # Reduce busy wait on persistent error
        except Exception as e:
            print(f"Unexpected error in main accept loop: {e}")
            time.sleep(0.5)