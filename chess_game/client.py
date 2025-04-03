import pygame
import socket
import pickle
import threading
import sys
import time

# --- Pygame Setup (Mostly from your original code) ---
pygame.init()

WIDTH = 1000
HEIGHT = 900
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption("Networked Chess Client") # Changed caption
font = pygame.font.Font('freesansbold.ttf', 20)
medium_font = pygame.font.Font('freesansbold.ttf', 40)
big_font = pygame.font.Font('freesansbold.ttf', 50)
timer = pygame.time.Clock()
fps = 60

# --- Game State Variables (Client Side - updated by server) ---
# Initialize with defaults, server will overwrite
game_state = {
    'white_pieces': [], 'white_locations': [],
    'black_pieces': [], 'black_locations': [],
    'captured_white': [], 'captured_black': [],
    'turn_step': 0, 'game_over': False, 'winner': '',
    'white_options': [], 'black_options': [] # Store received options
}
game_state_lock = threading.Lock() # Lock for accessing/updating game_state
my_color = None # Will be 'white' or 'black', assigned by server
selection = 100 # Local index of selected piece (within my color's lists)
valid_moves_display = [] # List of moves to highlight for the selected piece

# --- Load Assets ---
try:
    # load in game piece images (queen, king, rook, bishop, knight, pawn) x 2
    black_queen = pygame.image.load('assets/images/black queen.png')
    black_queen = pygame.transform.scale(black_queen, (80, 80))
    black_queen_small = pygame.transform.scale(black_queen, (45, 45))
    black_king = pygame.image.load('assets/images/black king.png')
    black_king = pygame.transform.scale(black_king, (80, 80))
    black_king_small = pygame.transform.scale(black_king, (45, 45))
    black_rook = pygame.image.load('assets/images/black rook.png')
    black_rook = pygame.transform.scale(black_rook, (80, 80))
    black_rook_small = pygame.transform.scale(black_rook, (45, 45))
    black_bishop = pygame.image.load('assets/images/black bishop.png')
    black_bishop = pygame.transform.scale(black_bishop, (80, 80))
    black_bishop_small = pygame.transform.scale(black_bishop, (45, 45))
    black_knight = pygame.image.load('assets/images/black knight.png')
    black_knight = pygame.transform.scale(black_knight, (80, 80))
    black_knight_small = pygame.transform.scale(black_knight, (45, 45))
    black_pawn = pygame.image.load('assets/images/black pawn.png')
    black_pawn = pygame.transform.scale(black_pawn, (65, 65))
    black_pawn_small = pygame.transform.scale(black_pawn, (45, 45))
    white_queen = pygame.image.load('assets/images/white queen.png')
    white_queen = pygame.transform.scale(white_queen, (80, 80))
    white_queen_small = pygame.transform.scale(white_queen, (45, 45))
    white_king = pygame.image.load('assets/images/white king.png')
    white_king = pygame.transform.scale(white_king, (80, 80))
    white_king_small = pygame.transform.scale(white_king, (45, 45))
    white_rook = pygame.image.load('assets/images/white rook.png')
    white_rook = pygame.transform.scale(white_rook, (80, 80))
    white_rook_small = pygame.transform.scale(white_rook, (45, 45))
    white_bishop = pygame.image.load('assets/images/white bishop.png')
    white_bishop = pygame.transform.scale(white_bishop, (80, 80))
    white_bishop_small = pygame.transform.scale(white_bishop, (45, 45))
    white_knight = pygame.image.load('assets/images/white knight.png')
    white_knight = pygame.transform.scale(white_knight, (80, 80))
    white_knight_small = pygame.transform.scale(white_knight, (45, 45))
    white_pawn = pygame.image.load('assets/images/white pawn.png')
    white_pawn = pygame.transform.scale(white_pawn, (65, 65))
    white_pawn_small = pygame.transform.scale(white_pawn, (45, 45))

    white_images = [white_pawn, white_queen, white_king, white_knight, white_rook, white_bishop]
    small_white_images = [white_pawn_small, white_queen_small, white_king_small, white_knight_small,
                          white_rook_small, white_bishop_small]
    black_images = [black_pawn, black_queen, black_king, black_knight, black_rook, black_bishop]
    small_black_images = [black_pawn_small, black_queen_small, black_king_small, black_knight_small,
                          black_rook_small, black_bishop_small]
    piece_list = ['pawn', 'queen', 'king', 'knight', 'rook', 'bishop']

except pygame.error as e:
    print(f"Error loading assets: {e}")
    print("Make sure the 'assets/images' folder is in the same directory as client.py")
    pygame.quit()
    sys.exit()
except FileNotFoundError as e:
    print(f"Asset file not found: {e}")
    print("Make sure the 'assets/images' folder and all image files exist.")
    pygame.quit()
    sys.exit()


# check variables / flashing counter
counter = 0 # Used for check flashing

# --- Drawing Functions (Adapted for server state) ---

def draw_board(current_turn_step):
    for i in range(32):
        column = i % 4
        row = i // 4
        if row % 2 == 0:
            pygame.draw.rect(screen, 'light gray', [600 - (column * 200), row * 100, 100, 100])
        else:
            pygame.draw.rect(screen, 'light gray', [700 - (column * 200), row * 100, 100, 100])

    pygame.draw.rect(screen, 'gray', [0, 800, WIDTH, 100])
    pygame.draw.rect(screen, 'gold', [0, 800, WIDTH, 100], 5)
    pygame.draw.rect(screen, 'gold', [800, 0, 200, HEIGHT], 5)

    status_text = ['White\'s Turn', 'White Moving', 'Black\'s Turn', 'Black Moving']
    # Adjust status based on turn step and whose turn it *really* is
    turn_indicator = status_text[0] if current_turn_step == 0 else status_text[2]
    screen.blit(big_font.render(turn_indicator, True, 'black'), (20, 820))
    if my_color:
         screen.blit(font.render(f"You are: {my_color.capitalize()}", True, 'black'), (400, 820))


    for i in range(9):
        pygame.draw.line(screen, 'black', (0, 100 * i), (800, 100 * i), 2)
        pygame.draw.line(screen, 'black', (100 * i, 0), (100 * i, 800), 2)
    screen.blit(medium_font.render('FORFEIT', True, 'black'), (810, 830)) # Forfeit needs server logic

# Draw pieces onto board using state received from server
def draw_pieces(state):
    w_pieces = state['white_pieces']
    w_locs = state['white_locations']
    b_pieces = state['black_pieces']
    b_locs = state['black_locations']
    current_turn_step = state['turn_step']

    for i in range(len(w_pieces)):
        try:
            index = piece_list.index(w_pieces[i])
            if w_pieces[i] == 'pawn':
                screen.blit(white_pawn, (w_locs[i][0] * 100 + 22, w_locs[i][1] * 100 + 30))
            else:
                screen.blit(white_images[index], (w_locs[i][0] * 100 + 10, w_locs[i][1] * 100 + 10))
        except (ValueError, IndexError) as e:
            # print(f"Error drawing white piece {i}: {e}, Piece: {w_pieces[i] if i<len(w_pieces) else 'OOB'}, Loc: {w_locs[i] if i<len(w_locs) else 'OOB'}")
            continue # Skip drawing if data is inconsistent

        # Highlight the selected piece *if* it's white's turn and this client is white
        if my_color == 'white' and current_turn_step < 2 and selection == i:
             pygame.draw.rect(screen, 'red', [w_locs[i][0] * 100 + 1, w_locs[i][1] * 100 + 1, 100, 100], 2)

    for i in range(len(b_pieces)):
        try:
            index = piece_list.index(b_pieces[i])
            if b_pieces[i] == 'pawn':
                screen.blit(black_pawn, (b_locs[i][0] * 100 + 22, b_locs[i][1] * 100 + 30))
            else:
                screen.blit(black_images[index], (b_locs[i][0] * 100 + 10, b_locs[i][1] * 100 + 10))
        except (ValueError, IndexError) as e:
            # print(f"Error drawing black piece {i}: {e}, Piece: {b_pieces[i] if i<len(b_pieces) else 'OOB'}, Loc: {b_locs[i] if i<len(b_locs) else 'OOB'}")
            continue # Skip drawing if data is inconsistent

        # Highlight the selected piece *if* it's black's turn and this client is black
        if my_color == 'black' and current_turn_step >= 2 and selection == i:
             pygame.draw.rect(screen, 'blue', [b_locs[i][0] * 100 + 1, b_locs[i][1] * 100 + 1, 100, 100], 2)

# Draw valid moves for the locally selected piece
def draw_valid(moves):
    color = 'red' if my_color == 'white' else 'blue'
    for i in range(len(moves)):
        try:
            pygame.draw.circle(screen, color, (moves[i][0] * 100 + 50, moves[i][1] * 100 + 50), 5)
        except IndexError:
             print(f"Error drawing valid move circle for move: {moves[i]}")


# Draw captured pieces on side of screen
def draw_captured(state):
    cap_w = state['captured_white'] # Pieces white captured (black pieces)
    cap_b = state['captured_black'] # Pieces black captured (white pieces)

    for i in range(len(cap_w)):
        try:
            captured_piece = cap_w[i]
            index = piece_list.index(captured_piece)
            screen.blit(small_black_images[index], (825, 5 + 50 * i))
        except (ValueError, IndexError):
             continue
    for i in range(len(cap_b)):
        try:
            captured_piece = cap_b[i]
            index = piece_list.index(captured_piece)
            screen.blit(small_white_images[index], (925, 5 + 50 * i))
        except (ValueError, IndexError):
            continue

# Draw a flashing square around king if in check (using server options)
def draw_check(state):
    global counter # Use the flashing counter
    w_locs = state['white_locations']
    w_pieces = state['white_pieces']
    b_locs = state['black_locations']
    b_pieces = state['black_pieces']
    w_opts = state['white_options']
    b_opts = state['black_options']
    current_turn_step = state['turn_step']

    king_in_check = False
    king_location = None
    check_color = None

    # Check if white king is in check (using black's options)
    if 'king' in w_pieces:
        king_index = w_pieces.index('king')
        king_location_w = w_locs[king_index]
        for i in range(len(b_opts)): # Iterate through black's pieces/options
            if king_location_w in b_opts[i]:
                 king_in_check = True
                 king_location = king_location_w
                 check_color = 'dark red'
                 # print(f"White King at {king_location} in check by black piece {i}")
                 break # Found one attacker, enough for highlight

    # Check if black king is in check (using white's options)
    if not king_in_check and 'king' in b_pieces:
        king_index = b_pieces.index('king')
        king_location_b = b_locs[king_index]
        for i in range(len(w_opts)): # Iterate through white's pieces/options
            if king_location_b in w_opts[i]:
                 king_in_check = True
                 king_location = king_location_b
                 check_color = 'dark blue'
                 # print(f"Black King at {king_location} in check by white piece {i}")
                 break

    if king_in_check and king_location:
         # Flash the check indicator
         if counter < 15:
             pygame.draw.rect(screen, check_color, [king_location[0] * 100 + 1,
                                                    king_location[1] * 100 + 1, 100, 100], 5)

def draw_game_over(state):
    winner = state['winner']
    if winner != '':
        pygame.draw.rect(screen, 'black', [200, 350, 400, 100]) # Centered better
        message = f'{winner.capitalize()} won the game!'
        screen.blit(medium_font.render(message, True, 'white'), (220, 365))
        screen.blit(font.render('Click anywhere to exit', True, 'white'), (260, 415))


# --- Networking Code ---
SERVER_IP = '127.0.0.1' # Change to server's actual IP if not running locally
PORT = 5555
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
network_error = None

def connect_to_server():
    global connected, my_color, network_error, client_socket
    try:
        print(f"Attempting to connect to {SERVER_IP}:{PORT}...")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Recreate socket
        client_socket.connect((SERVER_IP, PORT))
        print("Connected to server.")

        # Receive color assignment first
        color_data = client_socket.recv(1024)
        received_color = pickle.loads(color_data)

        if isinstance(received_color, str) and received_color in ['white', 'black']:
             my_color = received_color
             print(f"Assigned color: {my_color}")
             connected = True
             network_error = None
             # Start receiving game state in a separate thread
             receive_thread = threading.Thread(target=receive_updates, daemon=True)
             receive_thread.start()
        elif isinstance(received_color, str) and "error:" in received_color:
             network_error = f"Server Error: {received_color.split(':')[1]}"
             print(network_error)
             client_socket.close()
             connected = False
        else:
             network_error = "Received invalid color assignment from server."
             print(network_error)
             client_socket.close()
             connected = False

    except socket.error as e:
        network_error = f"Connection Error: {e}"
        print(network_error)
        connected = False
    except pickle.UnpicklingError:
         network_error = "Error decoding server assignment."
         print(network_error)
         connected = False
    except Exception as e: # Catch other potential errors during connect
         network_error = f"An unexpected error occurred during connection: {e}"
         print(network_error)
         connected = False


def receive_updates():
    """Runs in a thread to continuously receive game state updates."""
    global game_state, connected, network_error
    while connected:
        try:
            data = client_socket.recv(4096 * 2) # Increased buffer size for larger state
            if not data:
                print("Server disconnected (received empty data).")
                network_error = "Server disconnected."
                connected = False
                break

            new_state = pickle.loads(data)
            if isinstance(new_state, dict): # Check if it's the expected state dictionary
                with game_state_lock:
                    game_state = new_state
                # print("Received game state update.") # Debug print
            # Handle potential error messages from server if needed
            elif isinstance(new_state, str) and "error:" in new_state:
                 print(f"Received server message: {new_state}")
                 # Could display this error in Pygame status

        except (socket.error, EOFError, ConnectionResetError) as e:
            if connected: # Avoid printing error if we intentionally disconnected
                print(f"Network error receiving data: {e}")
                network_error = "Connection lost."
            connected = False
            break
        except pickle.UnpicklingError as e:
            print(f"Error decoding game state: {e}")
            # Continue trying to receive, maybe the next message is valid
        except Exception as e:
             print(f"Unexpected error in receive thread: {e}")
             network_error = "An unexpected error occurred."
             connected = False
             break
    print("Receive thread stopped.")
    # Attempt to close socket cleanly if loop exits
    try:
         client_socket.close()
         print("Client socket closed by receive thread.")
    except socket.error:
         pass # Socket might already be closed


def send_move(move):
    """Sends a move tuple (selection_index, target_coords) to the server."""
    # *** Move the global declaration here ***
    global network_error, connected

    if connected:
        try:
            data = pickle.dumps(move)
            client_socket.sendall(data)
            # print(f"Sent move: {move}") # Debug print
        except socket.error as e:
            print(f"Failed to send move: {e}")
            # Global declaration is already at the top
            network_error = "Failed to send move - Connection issue?"
            connected = False # Assume connection is lost if send fails
        except Exception as e:
             print(f"Unexpected error sending move: {e}")


# --- Main Game Loop ---
connect_to_server() # Initial connection attempt

run = True
while run:
    timer.tick(fps)
    if counter < 30:
        counter += 1
    else:
        counter = 0
    screen.fill('dark gray')

    # Get a consistent copy of the state for this frame
    with game_state_lock:
        current_state = game_state.copy() # Shallow copy is fine for dict structure

    # Display based on connection status and game state
    if not connected and network_error:
        # Display connection error message
        screen.fill('dark gray')
        error_text = medium_font.render("Connection Failed", True, 'red')
        reason_text = font.render(network_error, True, 'white')
        retry_text = font.render("Click to retry, Q to Quit", True, 'yellow')
        screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(reason_text, (WIDTH // 2 - reason_text.get_width() // 2, HEIGHT // 2))
        screen.blit(retry_text, (WIDTH // 2 - retry_text.get_width() // 2, HEIGHT // 2 + 40))

    elif not connected and not network_error:
         # Display connecting message
        screen.fill('dark gray')
        connecting_text = medium_font.render("Connecting to server...", True, 'white')
        screen.blit(connecting_text, (WIDTH // 2 - connecting_text.get_width() // 2, HEIGHT // 2 - 20))

    elif connected and my_color is None:
        # Display waiting for assignment message
        screen.fill('dark gray')
        waiting_text = medium_font.render("Connected. Waiting for assignment...", True, 'white')
        screen.blit(waiting_text, (WIDTH // 2 - waiting_text.get_width() // 2, HEIGHT // 2 - 20))

    elif connected and my_color:
        # Normal game drawing
        is_my_turn = (my_color == 'white' and current_state['turn_step'] < 2) or \
                     (my_color == 'black' and current_state['turn_step'] >= 2)

        draw_board(current_state['turn_step'])
        draw_pieces(current_state)
        draw_captured(current_state)
        draw_check(current_state)
        if selection != 100:
             draw_valid(valid_moves_display) # Draw highlights for selected piece

        if current_state['game_over']:
            draw_game_over(current_state)

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
             if not connected and event.key == pygame.K_q: # Quit from error screen
                  run = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x_coord = event.pos[0] // 100
            y_coord = event.pos[1] // 100
            click_coords = (x_coord, y_coord)

            if not connected and network_error:
                 # Clicked on error screen - try reconnecting
                 network_error = None # Clear error for retry message
                 connect_to_server()
                 continue # Skip rest of click handling

            if connected and current_state.get('game_over'): # Use .get for safety
                 # Click after game over - exit
                 run = False
                 continue

            if connected and my_color and is_my_turn and 0 <= x_coord <= 7 and 0 <= y_coord <= 7:
                current_locations = current_state['white_locations'] if my_color == 'white' else current_state['black_locations']
                current_options = current_state['white_options'] if my_color == 'white' else current_state['black_options']

                # --- Piece Selection ---
                if click_coords in current_locations:
                    new_selection = current_locations.index(click_coords)
                    # If selecting the same piece again, deselect
                    if new_selection == selection:
                        selection = 100
                        valid_moves_display = []
                    else:
                        selection = new_selection
                        # Get valid moves for the *selected* piece from the server state
                        if 0 <= selection < len(current_options):
                             valid_moves_display = current_options[selection]
                        else:
                             valid_moves_display = [] # Invalid selection index somehow
                             selection = 100 # Deselect if index is bad

                    # print(f"Selected piece index: {selection}, Valid moves: {valid_moves_display}") # Debug

                # --- Move Attempt ---
                elif selection != 100: # A piece is selected, and click is elsewhere on board
                     # Check if the target is in the *locally stored* valid moves for display
                     # The server will do the definitive validation
                    if click_coords in valid_moves_display:
                         print(f"Attempting move: Index {selection} to {click_coords}")
                         move_to_send = (selection, click_coords)
                         send_move(move_to_send)
                         # Deselect after sending attempt
                         selection = 100
                         valid_moves_display = []
                    else:
                         # Clicked somewhere invalid, deselect the piece
                         print("Invalid move click, deselecting.")
                         selection = 100
                         valid_moves_display = []

            elif connected and my_color and not is_my_turn and 0 <= x_coord <= 7 and 0 <= y_coord <= 7:
                 print("Not your turn!") # Feedback for clicking when it's not their turn

    pygame.display.flip()

# --- Cleanup ---
if connected:
    try:
        client_socket.shutdown(socket.SHUT_RDWR) # Signal closing
        client_socket.close()
        print("Client socket closed.")
    except socket.error as e:
        print(f"Error closing socket: {e}") # Might already be closed by thread

pygame.quit()
sys.exit()