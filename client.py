import pygame
import socket
import pickle
import threading
import sys
import time
from datetime import datetime
import math

pygame.init()

WIDTH = 1000
HEIGHT = 900
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption("Networked Chess Client")
font = pygame.font.Font('freesansbold.ttf', 20)
small_font = pygame.font.Font('freesansbold.ttf', 14)
medium_font = pygame.font.Font('freesansbold.ttf', 40)
big_font = pygame.font.Font('freesansbold.ttf', 50)
timer_display_font = pygame.font.Font('freesansbold.ttf', 24)
timer_label_font = pygame.font.Font('freesansbold.ttf', 16)
timer = pygame.time.Clock()
fps = 60

game_state = {
    'white_pieces': [], 'white_locations': [],
    'black_pieces': [], 'black_locations': [],
    'captured_white': [], 'captured_black': [],
    'turn_step': 0, 'game_over': False, 'winner': '',
    'white_options': [], 'black_options': [],
    'chat_history': [],
    'white_time': 1200.0,
    'black_time': 1200.0,
    'game_started': False
}
game_state_lock = threading.Lock()
my_color = None
selection = 100
valid_moves_display = []

# --- Chat Variables ---
CHAT_WIDTH = 200
CHAT_HEIGHT = HEIGHT - 100 # Let chat fill right panel above status bar
CHAT_X = 800
CHAT_Y = 0
chat_input = ""
chat_active = False
chat_scroll_offset = 0
text_offset = 0
cursor_visible = True
cursor_timer = 0
BUBBLE_PADDING = 10
BUBBLE_MARGIN = 5
BUBBLE_RADIUS = 8
MY_BUBBLE_COLOR = (240, 240, 240)
OPP_BUBBLE_COLOR = (50, 50, 50)
SHADOW_COLOR = (30, 30, 30, 100)
BG_COLOR_TOP = (180, 180, 180)
BG_COLOR_BOTTOM = (120, 120, 120)
last_chat_length = 0

# --- Constants ---
INITIAL_TIME_SECONDS = 1200.0

# --- Load Assets ---
# (Asset loading code remains unchanged)
try:
    black_queen = pygame.image.load('assets/images/black queen.png')
    black_queen = pygame.transform.scale(black_queen, (80, 80))
    # black_queen_small = pygame.transform.scale(black_queen, (45, 45)) # Not needed
    black_king = pygame.image.load('assets/images/black king.png')
    black_king = pygame.transform.scale(black_king, (80, 80))
    # black_king_small = pygame.transform.scale(black_king, (45, 45)) # Not needed
    black_rook = pygame.image.load('assets/images/black rook.png')
    black_rook = pygame.transform.scale(black_rook, (80, 80))
    # black_rook_small = pygame.transform.scale(black_rook, (45, 45)) # Not needed
    black_bishop = pygame.image.load('assets/images/black bishop.png')
    black_bishop = pygame.transform.scale(black_bishop, (80, 80))
    # black_bishop_small = pygame.transform.scale(black_bishop, (45, 45)) # Not needed
    black_knight = pygame.image.load('assets/images/black knight.png')
    black_knight = pygame.transform.scale(black_knight, (80, 80))
    # black_knight_small = pygame.transform.scale(black_knight, (45, 45)) # Not needed
    black_pawn = pygame.image.load('assets/images/black pawn.png')
    black_pawn = pygame.transform.scale(black_pawn, (65, 65))
    # black_pawn_small = pygame.transform.scale(black_pawn, (45, 45)) # Not needed
    white_queen = pygame.image.load('assets/images/white queen.png')
    white_queen = pygame.transform.scale(white_queen, (80, 80))
    # white_queen_small = pygame.transform.scale(white_queen, (45, 45)) # Not needed
    white_king = pygame.image.load('assets/images/white king.png')
    white_king = pygame.transform.scale(white_king, (80, 80))
    # white_king_small = pygame.transform.scale(white_king, (45, 45)) # Not needed
    white_rook = pygame.image.load('assets/images/white rook.png')
    white_rook = pygame.transform.scale(white_rook, (80, 80))
    # white_rook_small = pygame.transform.scale(white_rook, (45, 45)) # Not needed
    white_bishop = pygame.image.load('assets/images/white bishop.png')
    white_bishop = pygame.transform.scale(white_bishop, (80, 80))
    # white_bishop_small = pygame.transform.scale(white_bishop, (45, 45)) # Not needed
    white_knight = pygame.image.load('assets/images/white knight.png')
    white_knight = pygame.transform.scale(white_knight, (80, 80))
    # white_knight_small = pygame.transform.scale(white_knight, (45, 45)) # Not needed
    white_pawn = pygame.image.load('assets/images/white pawn.png')
    white_pawn = pygame.transform.scale(white_pawn, (65, 65))
    # white_pawn_small = pygame.transform.scale(white_pawn, (45, 45)) # Not needed

    white_images = [white_pawn, white_queen, white_king, white_knight, white_rook, white_bishop]
    # small_white_images = [...] # Not needed
    black_images = [black_pawn, black_queen, black_king, black_knight, black_rook, black_bishop]
    # small_black_images = [...] # Not needed
    piece_list = ['pawn', 'queen', 'king', 'knight', 'rook', 'bishop']

except pygame.error as e:
    print(f"Error loading assets: {e}")
    pygame.quit(); sys.exit()
except FileNotFoundError as e:
    print(f"Asset file not found: {e}")
    pygame.quit(); sys.exit()


# --- Helper Functions ---
def format_time(seconds):
    # (format_time function remains unchanged)
    if seconds < 0: seconds = 0
    minutes = int(seconds // 60)
    remaining_seconds = int(math.ceil(seconds % 60))
    if remaining_seconds == 60:
        minutes += 1
        remaining_seconds = 0
    return f"{minutes:02d}:{remaining_seconds:02d}"

# --- Drawing Functions ---

def draw_board(state):
    # (Function is correct, no changes needed here from previous correction)
    # Draw checkered board
    for r in range(8):
        for c in range(8):
            color = 'light gray' if (r + c) % 2 == 0 else 'dark gray'
            pygame.draw.rect(screen, color, [c * 100, r * 100, 100, 100])

    # Bottom Status Bar Background and Border
    pygame.draw.rect(screen, 'gray', [0, 800, WIDTH, 100])
    pygame.draw.rect(screen, 'gold', [0, 800, WIDTH, 100], 5)
    # Right Panel Border (Chat only now)
    pygame.draw.rect(screen, 'gold', [CHAT_X, 0, CHAT_WIDTH, HEIGHT], 5) # Border around chat

    # Status Text (Turn Indicator)
    status_text = ['White\'s Turn', 'White Moving', 'Black\'s Turn', 'Black Moving']
    current_turn_step = state.get('turn_step', 0)
    turn_idx = current_turn_step if 0 <= current_turn_step < len(status_text) else 0
    turn_indicator = status_text[turn_idx]
    turn_color = 'white' if turn_idx < 2 else 'black'
    screen.blit(big_font.render(turn_indicator, True, turn_color), (20, 820))

    # Player Color Indicator
    if my_color:
        screen.blit(font.render(f"You are: {my_color.capitalize()}", True, 'black'), (400, 820))

    # Board Lines
    for i in range(9):
        pygame.draw.line(screen, 'black', (0, 100 * i), (800, 100 * i), 2)
        pygame.draw.line(screen, 'black', (100 * i, 0), (100 * i, 800), 2)

def draw_pieces(state):
    # (draw_pieces function remains unchanged)
    w_pieces = state.get('white_pieces', [])
    w_locs = state.get('white_locations', [])
    b_pieces = state.get('black_pieces', [])
    b_locs = state.get('black_locations', [])
    current_turn_step = state.get('turn_step', 0)

    for i in range(len(w_pieces)):
        try:
            if not (0 <= i < len(w_locs)): continue
            loc = w_locs[i]
            piece = w_pieces[i]
            if piece not in piece_list: continue
            index = piece_list.index(piece)
            image = white_images[index]
            x_pos = loc[0] * 100 + (10 if piece != 'pawn' else 17)
            y_pos = loc[1] * 100 + (10 if piece != 'pawn' else 17)
            screen.blit(image, (x_pos, y_pos))
            if my_color == 'white' and current_turn_step < 2 and selection == i:
                pygame.draw.rect(screen, 'red', [loc[0] * 100 + 1, loc[1] * 100 + 1, 98, 98], 3)
        except (ValueError, IndexError, TypeError) as e:
            print(f"Error drawing white piece {i}: {e}")

    for i in range(len(b_pieces)):
        try:
            if not (0 <= i < len(b_locs)): continue
            loc = b_locs[i]
            piece = b_pieces[i]
            if piece not in piece_list: continue
            index = piece_list.index(piece)
            image = black_images[index]
            x_pos = loc[0] * 100 + (10 if piece != 'pawn' else 17)
            y_pos = loc[1] * 100 + (10 if piece != 'pawn' else 17)
            screen.blit(image, (x_pos, y_pos))
            if my_color == 'black' and current_turn_step >= 2 and selection == i:
                pygame.draw.rect(screen, 'blue', [loc[0] * 100 + 1, loc[1] * 100 + 1, 98, 98], 3)
        except (ValueError, IndexError, TypeError) as e:
            print(f"Error drawing black piece {i}: {e}")


def draw_valid(moves):
    # (draw_valid function remains unchanged)
    color = 'red' if my_color == 'white' else 'blue'
    for move in moves:
        try:
            if isinstance(move, (list, tuple)) and len(move) == 2 and all(isinstance(coord, int) for coord in move):
                 pygame.draw.circle(screen, color, (move[0] * 100 + 50, move[1] * 100 + 50), 10)
            else:
                print(f"Error: Invalid move format: {move}")
        except (IndexError, TypeError) as e:
            print(f"Error drawing valid move: {move}. Error: {e}")


# THIS FUNCTION IS NOW OBSOLETE FOR DRAWING
def draw_captured(state):
    """(No longer draws captured pieces)"""
    pass

def draw_check(state):
    # (draw_check function remains unchanged)
    global counter
    w_locs = state.get('white_locations', [])
    w_pieces = state.get('white_pieces', [])
    b_locs = state.get('black_locations', [])
    b_pieces = state.get('black_pieces', [])
    w_opts_flat = [move for sublist in state.get('white_options', []) for move in sublist if isinstance(move, (tuple, list)) and len(move) == 2]
    b_opts_flat = [move for sublist in state.get('black_options', []) for move in sublist if isinstance(move, (tuple, list)) and len(move) == 2]

    king_in_check = False
    king_location = None
    check_color = 'dark red'

    try:
        if 'king' in w_pieces:
            king_index = w_pieces.index('king')
            if 0 <= king_index < len(w_locs):
                king_location_w = w_locs[king_index]
                if king_location_w in b_opts_flat:
                    king_in_check = True
                    king_location = king_location_w
                    check_color = 'dark red'
    except (ValueError, IndexError): pass

    try:
        if not king_in_check and 'king' in b_pieces:
            king_index = b_pieces.index('king')
            if 0 <= king_index < len(b_locs):
                king_location_b = b_locs[king_index]
                if king_location_b in w_opts_flat:
                    king_in_check = True
                    king_location = king_location_b
                    check_color = 'dark blue'
    except (ValueError, IndexError): pass

    if king_in_check and king_location and isinstance(king_location, (list, tuple)) and len(king_location) == 2:
        if counter < 15:
            pygame.draw.rect(screen, check_color, [king_location[0] * 100 + 1, king_location[1] * 100 + 1, 98, 98], 5)


def draw_game_over(state):
    # (draw_game_over function remains unchanged)
    winner = state.get('winner', '')
    if winner != '':
        pygame.draw.rect(screen, 'black', [200, 350, 600, 100])
        message = f'{winner.capitalize()} won the game!'
        white_time = state.get('white_time', 0)
        black_time = state.get('black_time', 0)
        if winner == 'white' and black_time <= 0: message += " (on time)"
        elif winner == 'black' and white_time <= 0: message += " (on time)"
        # ... (other win conditions)
        elif winner != 'unknown': message += "!" # Simplified end
        screen.blit(medium_font.render(message, True, 'white'), (220, 360))
        screen.blit(font.render('Click anywhere to exit', True, 'white'), (380, 410))


def draw_chat(state):
    # (draw_chat function remains unchanged - draws in right panel)
    global text_offset, chat_scroll_offset, last_chat_length
    chat_area_rect = pygame.Rect(CHAT_X, CHAT_Y, CHAT_WIDTH, CHAT_HEIGHT)

    # Draw gradient background for chat area
    for i in range(CHAT_HEIGHT):
        ratio = i / CHAT_HEIGHT
        r = int(BG_COLOR_TOP[0] * (1 - ratio) + BG_COLOR_BOTTOM[0] * ratio)
        g = int(BG_COLOR_TOP[1] * (1 - ratio) + BG_COLOR_BOTTOM[1] * ratio)
        b = int(BG_COLOR_TOP[2] * (1 - ratio) + BG_COLOR_BOTTOM[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (CHAT_X, CHAT_Y + i), (CHAT_X + CHAT_WIDTH, CHAT_Y + i))

    # Draw border for chat area
    pygame.draw.rect(screen, 'black', chat_area_rect, 2)

    # --- Message Rendering ---
    chat_history = state.get('chat_history', [])
    max_text_width = CHAT_WIDTH - 2 * BUBBLE_MARGIN - 2 * BUBBLE_PADDING - 10 # Available text width inside bubble
    message_data = []
    line_height = font.get_linesize()

    for i, message in enumerate(chat_history):
        # (Word wrapping and bubble calculation logic is unchanged)
        is_mine = message.get('sender') == my_color
        text = message.get('text', '')
        timestamp = message.get('timestamp', 'Unknown')
        words = text.split(' ')
        lines = []
        current_line = ""
        # (Word wrap loop...)
        for word in words:
            test_line = current_line + word + " "
            test_surface = font.render(test_line.strip(), True, 'black')
            if test_surface.get_width() <= max_text_width:
                current_line = test_line
            else:
                if current_line: lines.append(current_line.strip())
                # Handle long words...
                current_line = word + " "
        if current_line: lines.append(current_line.strip())
        if not lines and text: lines = [text]
        # (Calculate bubble size...)
        bubble_height = len(lines) * line_height + BUBBLE_PADDING * 2
        max_line_wd = 0
        if lines: max_line_wd = max(font.render(line, True, 'black').get_width() for line in lines)
        bubble_width = max_line_wd + BUBBLE_PADDING * 2
        bubble_width = min(bubble_width, max_text_width + BUBBLE_PADDING * 2)
        ts_surf = small_font.render(timestamp, True, (0,0,0))
        bubble_height += ts_surf.get_height() + 5
        message_data.append({'is_mine': is_mine, 'lines': lines, 'ts': timestamp, 'w': bubble_width, 'h': bubble_height})

    # --- Scrolling Calculation ---
    total_content_height = sum(md['h'] + BUBBLE_MARGIN for md in message_data)
    input_box_height = 50
    visible_message_area_height = CHAT_HEIGHT - input_box_height

    if len(chat_history) > last_chat_length:
        if chat_scroll_offset > -(total_content_height - visible_message_area_height + 50): # Auto-scroll if near bottom
             chat_scroll_offset = -max(0, total_content_height - visible_message_area_height)
    last_chat_length = len(chat_history)

    max_scroll = max(0, total_content_height - visible_message_area_height)
    chat_scroll_offset = max(-max_scroll, min(0, chat_scroll_offset))

    # --- Draw Visible Messages ---
    current_y = CHAT_Y + BUBBLE_MARGIN + chat_scroll_offset
    clip_rect_messages = pygame.Rect(CHAT_X, CHAT_Y, CHAT_WIDTH, visible_message_area_height)
    screen.set_clip(clip_rect_messages)

    for md in message_data:
        if current_y + md['h'] > CHAT_Y and current_y < CHAT_Y + visible_message_area_height: # Culling
            bubble_x = (CHAT_X + CHAT_WIDTH - md['w'] - BUBBLE_MARGIN) if md['is_mine'] else (CHAT_X + BUBBLE_MARGIN)
            bubble_rect = pygame.Rect(bubble_x, current_y, md['w'], md['h'])
            bubble_color = MY_BUBBLE_COLOR if md['is_mine'] else OPP_BUBBLE_COLOR
            pygame.draw.rect(screen, bubble_color, bubble_rect, border_radius=BUBBLE_RADIUS)

            # Draw text lines
            text_y = current_y + BUBBLE_PADDING
            text_color = 'black' if md['is_mine'] else 'white'
            for line in md['lines']:
                text_surface = font.render(line, True, text_color)
                screen.blit(text_surface, (bubble_x + BUBBLE_PADDING, text_y))
                text_y += line_height

            # Draw timestamp
            ts_surf = small_font.render(md['ts'], True, (100,100,100) if md['is_mine'] else (180,180,180))
            screen.blit(ts_surf, (bubble_x + BUBBLE_PADDING, text_y + 5))
        current_y += md['h'] + BUBBLE_MARGIN

    screen.set_clip(None) # Reset clip

    # --- Draw Input Box ---
    input_area_y = CHAT_Y + CHAT_HEIGHT - input_box_height + 5 # Position input box at bottom of chat area
    input_box_width = CHAT_WIDTH - 40
    input_box_rect = pygame.Rect(CHAT_X + 5, input_area_y, input_box_width, 30)
    visible_text_area_width = input_box_width - 10
    # (Draw input box background and border...)
    pygame.draw.rect(screen, (220, 220, 220), input_box_rect)
    pygame.draw.rect(screen, 'black', input_box_rect, 2 if not chat_active else 4)

    # (Text input rendering with scrolling...)
    input_surface = font.render(chat_input, True, 'black')
    input_width = input_surface.get_width()
    if input_width > visible_text_area_width: text_offset = input_width - visible_text_area_width
    else: text_offset = 0
    cursor_screen_x = CHAT_X + 10 + input_width - text_offset

    clip_rect_input = pygame.Rect(CHAT_X + 10, input_area_y + 5, visible_text_area_width, 20)
    screen.set_clip(clip_rect_input)
    screen.blit(input_surface, (CHAT_X + 10 - text_offset, input_area_y + 5))
    screen.set_clip(None)

    # (Draw cursor...)
    if chat_active and cursor_visible:
        if CHAT_X + 10 <= cursor_screen_x <= CHAT_X + 10 + visible_text_area_width:
            pygame.draw.line(screen, 'black', (cursor_screen_x, input_area_y + 8), (cursor_screen_x, input_area_y + 22), 2)

    # (Draw send button...)
    send_button_cx = CHAT_X + CHAT_WIDTH - 20
    send_button_cy = input_area_y + 15
    send_button_radius = 12
    pygame.draw.circle(screen, (0, 128, 0), (send_button_cx, send_button_cy), send_button_radius)
    pygame.draw.polygon(screen, 'white', [(send_button_cx - 4, send_button_cy - 5), (send_button_cx + 5, send_button_cy), (send_button_cx - 4, send_button_cy + 5)])


def draw_timers(state):
    """Draws the player timers in the bottom-right corner."""
    #print(f"Draw timers called. State time: W={state.get('white_time')}, B={state.get('black_time')}") # Debug print
    white_time = state.get('white_time', INITIAL_TIME_SECONDS)
    black_time = state.get('black_time', INITIAL_TIME_SECONDS)

    # Position within the bottom status bar (y=800 to y=900)
    timer_area_y = 810  # Start slightly below the top edge of the status bar
    timer_box_height = 80 # Height of the timer box
    timer_width_each = 130 # Width of each player's timer box
    spacing = 15        # Space between timer boxes

    # Calculate X positions dynamically based on WIDTH
    black_timer_x = WIDTH - timer_width_each - 15 # Black timer on the far right
    white_timer_x = black_timer_x - timer_width_each - spacing # White timer to the left

    # Define rects for easier drawing and potential click detection later
    white_timer_rect = pygame.Rect(white_timer_x, timer_area_y, timer_width_each, timer_box_height)
    black_timer_rect = pygame.Rect(black_timer_x, timer_area_y, timer_width_each, timer_box_height)

    # Draw background boxes for timers
    pygame.draw.rect(screen, (210, 210, 210), white_timer_rect) # White timer bg
    pygame.draw.rect(screen, (40, 40, 40), black_timer_rect)    # Black timer bg
    # Draw borders
    pygame.draw.rect(screen, 'black', white_timer_rect, 2)
    pygame.draw.rect(screen, 'white', black_timer_rect, 2)

    # Format and render time strings
    white_time_str = format_time(white_time)
    black_time_str = format_time(black_time)

    # Render using the specific timer fonts
    white_timer_surface = timer_display_font.render(white_time_str, True, 'black')
    black_timer_surface = timer_display_font.render(black_time_str, True, 'white')

    # Render labels
    white_label_surface = timer_label_font.render("White", True, 'black')
    black_label_surface = timer_label_font.render("Black", True, 'white')

    # Calculate positions for labels (top centered)
    white_label_rect = white_label_surface.get_rect(centerx=white_timer_rect.centerx, top=white_timer_rect.top + 5)
    black_label_rect = black_label_surface.get_rect(centerx=black_timer_rect.centerx, top=black_timer_rect.top + 5)

    # Calculate positions for times (centered below labels)
    label_height = white_label_rect.height + 5 # Include padding below label
    white_text_rect = white_timer_surface.get_rect(centerx=white_timer_rect.centerx, centery=white_timer_rect.top + label_height + (white_timer_rect.height - label_height)/2)
    black_text_rect = black_timer_surface.get_rect(centerx=black_timer_rect.centerx, centery=black_timer_rect.top + label_height + (black_timer_rect.height - label_height)/2)

    # Blit labels and times
    screen.blit(white_label_surface, white_label_rect)
    screen.blit(black_label_surface, black_label_rect)
    screen.blit(white_timer_surface, white_text_rect)
    screen.blit(black_timer_surface, black_text_rect)


# --- Networking Code ---
# (Networking code connect_to_server, receive_updates, send_message remains unchanged)
SERVER_IP = '127.0.0.1'
PORT = 5555
client_socket = None
connected = False
network_error = None

def connect_to_server():
    # (Function unchanged)
    global connected, my_color, network_error, client_socket, game_state, game_state_lock
    if client_socket:
        try: client_socket.close()
        except socket.error: pass
        client_socket = None
    try:
        print(f"Attempting connect...")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5.0)
        client_socket.connect((SERVER_IP, PORT))
        client_socket.settimeout(None)
        print("Connected.")
        color_data = client_socket.recv(1024)
        if not color_data: raise socket.error("No assignment received.")
        received_color = pickle.loads(color_data)
        if isinstance(received_color, str) and received_color in ['white', 'black']:
            my_color = received_color
            print(f"Assigned: {my_color}")
            connected = True; network_error = None
            threading.Thread(target=receive_updates, daemon=True).start()
        elif isinstance(received_color, str) and "error:" in received_color:
            network_error = f"Server Error: {received_color.split(':', 1)[1]}"
            print(network_error); client_socket.close(); client_socket = None; connected = False
        else:
            network_error = f"Invalid assignment: {received_color}"
            print(network_error); client_socket.close(); client_socket = None; connected = False
    except socket.timeout: network_error = f"Timeout connecting"; print(network_error); connected = False; client_socket = None
    except socket.error as e: network_error = f"Connection Error: {e}"; print(network_error); connected = False; client_socket = None
    except pickle.UnpicklingError as e: network_error = f"Decode Error: {e}"; print(network_error); connected = False; client_socket = None
    except Exception as e: network_error = f"Connect Error: {e}"; print(network_error); connected = False; client_socket = None

def receive_updates():
    # (Function unchanged - needs robust message framing ideally)
    global game_state, connected, network_error, client_socket
    buffer = b""
    while connected and client_socket:
        try:
            chunk = client_socket.recv(4096 * 2)
            if not chunk:
                if connected: network_error = "Server disconnected."
                connected = False; break
            buffer += chunk
            try:
                # WARNING: Still assumes one pickle object per chunk/buffer, needs framing
                message = pickle.loads(buffer)
                buffer = b"" # Clear buffer after assumed successful load
                if isinstance(message, dict):
                    with game_state_lock: game_state = message
                elif isinstance(message, str) and "error:" in message:
                    print(f"Server error: {message.split(':', 1)[1]}")
            except (pickle.UnpicklingError, EOFError, IndexError):
                # Incomplete message, wait for more data
                pass # Keep buffer and wait for next chunk
        except (socket.error, ConnectionResetError) as e:
            if connected: network_error = "Connection lost."
            connected = False; break
        except Exception as e:
            if connected: network_error = "Receive Error."
            print(f"Receive thread error: {e}"); connected = False; break
    print("Receive thread stopped.")
    if client_socket:
        try: client_socket.close()
        except socket.error: pass
        client_socket = None
    connected = False

def send_message(message_type, data):
    # (Function unchanged)
    global network_error, connected, client_socket
    if connected and client_socket:
        try:
            if message_type == 'chat' and isinstance(data, dict):
                data['timestamp'] = datetime.now().strftime("%I:%M %p")
            message = {'type': message_type, 'data': data}
            serialized_message = pickle.dumps(message)
            client_socket.sendall(serialized_message)
        except socket.error as e:
            print(f"Send Error: {e}"); network_error = "Send failed"; connected = False
        except Exception as e:
            print(f"Send Error: {e}"); network_error = "Send failed"; connected = False
    elif not connected: print("Cannot send: Not connected.")

# --- Main Game Loop ---
connect_to_server()
counter = 0
run = True
while run:
    timer.tick(fps)
    elapsed_time = timer.get_time() / 1000.0

    cursor_timer += elapsed_time
    if cursor_timer >= 0.5:
        cursor_visible = not cursor_visible
        cursor_timer %= 0.5

    counter = (counter + 1) % 30

    with game_state_lock:
        current_frame_state = game_state.copy()

    # --- Drawing ---
    screen.fill((40, 40, 40)) # Background

    # --- Handle Different States ---
    if not connected and network_error:
        # (Error screen drawing unchanged)
        screen.fill('dark gray')
        error_text = medium_font.render("Connection Failed", True, 'red')
        reason_text = font.render(network_error, True, 'white')
        retry_text = font.render("Click to retry, Q to Quit", True, 'yellow')
        screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, HEIGHT // 2 - 60))
        max_width = WIDTH - 100; words = network_error.split(' '); lines = []; current_line = ""
        for word in words: test_line = current_line + word + " "; # (Word wrap...)
        line_y = HEIGHT // 2 - 20; # (Draw lines...)
        screen.blit(retry_text, (WIDTH // 2 - retry_text.get_width() // 2, line_y + 20))

    elif not connected and not network_error:
        # (Connecting screen unchanged)
        screen.fill('dark gray'); connecting_text = medium_font.render("Connecting...", True, 'white')
        screen.blit(connecting_text, (WIDTH // 2 - connecting_text.get_width() // 2, HEIGHT // 2 - 20))

    elif connected and my_color is None:
         # (Waiting screen unchanged)
        screen.fill('dark gray'); waiting_text = medium_font.render("Waiting for assignment...", True, 'white')
        screen.blit(waiting_text, (WIDTH // 2 - waiting_text.get_width() // 2, HEIGHT // 2 - 20))

    elif connected and my_color:
        # --- Main Game Drawing ---
        draw_board(current_frame_state)
        draw_pieces(current_frame_state)
        draw_check(current_frame_state)
        draw_chat(current_frame_state)
        draw_timers(current_frame_state) # Draw timers in bottom right

        # REMOVED THE CALL TO draw_captured

        if selection != 100:
            if isinstance(valid_moves_display, list):
                draw_valid(valid_moves_display)
            else:
                valid_moves_display = [] # Reset if invalid

        if current_frame_state.get('game_over', False):
            draw_game_over(current_frame_state)

    # --- Event Handling ---
    # (Event handling loop remains largely unchanged)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: run = False

        # Keyboard Input
        if event.type == pygame.KEYDOWN:
            if not connected and event.key == pygame.K_q: run = False
            elif connected and chat_active:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if chat_input.strip(): send_message('chat', {'sender': my_color, 'text': chat_input.strip()})
                    chat_input = ""; text_offset = 0; cursor_visible = True; cursor_timer = 0
                elif event.key == pygame.K_BACKSPACE:
                    if chat_input: chat_input = chat_input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    chat_active = False; text_offset = 0; cursor_visible = True; cursor_timer = 0
                else:
                    if len(chat_input) < 100:
                         char = event.unicode
                         if char.isprintable(): chat_input += char

        # Mouse Input
        if event.type == pygame.MOUSEBUTTONDOWN:
            x_coord, y_coord = event.pos
            # Button 1 (Left Click)
            if event.button == 1:
                if not connected and network_error: network_error = None; connect_to_server(); continue
                if connected and current_frame_state.get('game_over', False): run = False; continue

                # Check Chat Area Clicks
                input_area_y = CHAT_Y + CHAT_HEIGHT - 50 + 5
                input_box_rect = pygame.Rect(CHAT_X + 5, input_area_y, CHAT_WIDTH - 40, 30)
                send_button_cx = CHAT_X + CHAT_WIDTH - 20; send_button_cy = input_area_y + 15; send_button_radius_sq = 12**2
                if input_box_rect.collidepoint(x_coord, y_coord):
                     chat_active = True; cursor_visible = True; cursor_timer = 0; selection = 100; valid_moves_display = []; continue
                elif (x_coord - send_button_cx)**2 + (y_coord - send_button_cy)**2 <= send_button_radius_sq:
                    if chat_input.strip(): send_message('chat', {'sender': my_color, 'text': chat_input.strip()})
                    chat_input = ""; text_offset = 0; cursor_visible = True; cursor_timer = 0; continue
                elif chat_active: # Clicked outside chat input while active
                     chat_active = False # Deactivate chat

                # Check Chess Board Clicks (only if not handled by chat)
                is_my_turn = (my_color == 'white' and current_frame_state.get('turn_step', 0) < 2) or \
                             (my_color == 'black' and current_frame_state.get('turn_step', 0) >= 2)
                if connected and my_color and not current_frame_state.get('game_over', False) and \
                   0 <= x_coord < 800 and 0 <= y_coord < 800: # Click is on the board
                    click_coords = (x_coord // 100, y_coord // 100)
                    if is_my_turn:
                        my_locs = current_frame_state.get(f'{my_color}_locations', [])
                        my_opts = current_frame_state.get(f'{my_color}_options', [])
                        if click_coords in my_locs:
                            idx = my_locs.index(click_coords)
                            if idx == selection: selection = 100; valid_moves_display = [] # Deselect
                            else: # Select new piece
                                selection = idx
                                if 0 <= selection < len(my_opts) and isinstance(my_opts[selection], list): valid_moves_display = my_opts[selection]
                                else: valid_moves_display = []; print(f"Warn: No/bad options for {my_color} piece {selection}")
                        elif selection != 100: # Piece already selected
                            if click_coords in valid_moves_display: # Valid move clicked
                                send_message('move', (selection, click_coords))
                                selection = 100; valid_moves_display = []
                            else: selection = 100; valid_moves_display = [] # Invalid move clicked, deselect
                        else: selection = 100; valid_moves_display = [] # Clicked empty/opponent square
                    else: print("Not your turn!"); selection = 100; valid_moves_display = [] # Clicked out of turn

            # Buttons 4/5 (Scroll Wheel for Chat)
            elif event.button == 4: # Scroll Up
                 if CHAT_X <= x_coord <= CHAT_X + CHAT_WIDTH and CHAT_Y <= y_coord <= CHAT_Y + CHAT_HEIGHT - 50:
                      chat_scroll_offset = min(0, chat_scroll_offset + 30)
            elif event.button == 5: # Scroll Down
                 if CHAT_X <= x_coord <= CHAT_X + CHAT_WIDTH and CHAT_Y <= y_coord <= CHAT_Y + CHAT_HEIGHT - 50:
                      # Max scroll clamping happens in draw_chat
                      chat_scroll_offset -= 30

    # --- Update Display ---
    pygame.display.flip()

# --- Cleanup ---
# (Cleanup code remains unchanged)
print("Exiting.")
connected = False
if client_socket:
    try: client_socket.close(); print("Socket closed.")
    except socket.error as e: print(f"Socket close error: {e}")
pygame.quit()
sys.exit()
