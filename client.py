# ######## client.py (with Framing fix - Complete) ########
import pygame
import socket
import pickle
import threading
import sys
import time
from datetime import datetime
import math
import struct # For message framing

pygame.init()

# --- Constants and Setup ---
WIDTH = 1000
HEIGHT = 900
CHAT_X = 800
CHAT_WIDTH = 200
CHAT_Y = 0
CHAT_HEIGHT = HEIGHT - 100 # Assuming status bar height is 100
INITIAL_TIME_SECONDS = 1200.0 # Default for display if state is missing

screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption("Networked Chess Client")
try:
    font = pygame.font.Font('freesansbold.ttf', 20)
    small_font = pygame.font.Font('freesansbold.ttf', 14)
    medium_font = pygame.font.Font('freesansbold.ttf', 40)
    big_font = pygame.font.Font('freesansbold.ttf', 50)
    timer_display_font = pygame.font.Font('freesansbold.ttf', 24)
    timer_label_font = pygame.font.Font('freesansbold.ttf', 16)
except FileNotFoundError:
    print("Error: 'freesansbold.ttf' not found. Using default font.")
    # Fallback to default font
    font = pygame.font.SysFont(None, 24)
    small_font = pygame.font.SysFont(None, 18)
    medium_font = pygame.font.SysFont(None, 48)
    big_font = pygame.font.SysFont(None, 60)
    timer_display_font = pygame.font.SysFont(None, 30)
    timer_label_font = pygame.font.SysFont(None, 20)

timer = pygame.time.Clock()
fps = 60

# Default initial state
game_state = {
    'white_pieces': [], 'white_locations': [],
    'black_pieces': [], 'black_locations': [],
    'captured_white': [], 'captured_black': [],
    'turn_step': 0, 'game_over': False, 'winner': '',
    'white_options': [], 'black_options': [],
    'chat_history': [],
    'white_time': INITIAL_TIME_SECONDS, 'black_time': INITIAL_TIME_SECONDS,
    'game_started': False, 'game_id': None
}
game_state_lock = threading.Lock()
my_color = None # 'white' or 'black' or None (if waiting)
selection = 100 # Index of selected piece, 100 means nothing selected
valid_moves_display = [] # Moves for the selected piece

# Chat Variables
chat_input = ""
chat_active = False
chat_scroll_offset = 0
text_offset = 0
cursor_visible = True
cursor_timer = 0
last_chat_length = 0
BUBBLE_PADDING = 10
BUBBLE_MARGIN = 5
BUBBLE_RADIUS = 8
MY_BUBBLE_COLOR = (240, 240, 240)
OPP_BUBBLE_COLOR = (50, 50, 50)
BG_COLOR_TOP = (180, 180, 180)
BG_COLOR_BOTTOM = (120, 120, 120)

# Networking Variables
SERVER_IP = '127.0.0.1' # Change if server is elsewhere
PORT = 5555
client_socket = None
connected = False
network_error = None
HEADER_SIZE = struct.calcsize('>I') # Size of the length prefix (4 bytes)

# Asset Loading
white_images = []
black_images = []
piece_list = ['pawn', 'queen', 'king', 'knight', 'rook', 'bishop']
try:
    base_path = 'assets/images/' # Adjust if your path is different
    white_pawn = pygame.image.load(base_path + 'white pawn.png')
    white_pawn = pygame.transform.scale(white_pawn, (65, 65))
    white_queen = pygame.image.load(base_path + 'white queen.png')
    white_queen = pygame.transform.scale(white_queen, (80, 80))
    white_king = pygame.image.load(base_path + 'white king.png')
    white_king = pygame.transform.scale(white_king, (80, 80))
    white_knight = pygame.image.load(base_path + 'white knight.png')
    white_knight = pygame.transform.scale(white_knight, (80, 80))
    white_rook = pygame.image.load(base_path + 'white rook.png')
    white_rook = pygame.transform.scale(white_rook, (80, 80))
    white_bishop = pygame.image.load(base_path + 'white bishop.png')
    white_bishop = pygame.transform.scale(white_bishop, (80, 80))

    black_pawn = pygame.image.load(base_path + 'black pawn.png')
    black_pawn = pygame.transform.scale(black_pawn, (65, 65))
    black_queen = pygame.image.load(base_path + 'black queen.png')
    black_queen = pygame.transform.scale(black_queen, (80, 80))
    black_king = pygame.image.load(base_path + 'black king.png')
    black_king = pygame.transform.scale(black_king, (80, 80))
    black_knight = pygame.image.load(base_path + 'black knight.png')
    black_knight = pygame.transform.scale(black_knight, (80, 80))
    black_rook = pygame.image.load(base_path + 'black rook.png')
    black_rook = pygame.transform.scale(black_rook, (80, 80))
    black_bishop = pygame.image.load(base_path + 'black bishop.png')
    black_bishop = pygame.transform.scale(black_bishop, (80, 80))

    # Ensure order matches piece_list
    white_images = [white_pawn, white_queen, white_king, white_knight, white_rook, white_bishop]
    black_images = [black_pawn, black_queen, black_king, black_knight, black_rook, black_bishop]

except pygame.error as e:
    print(f"Pygame Error loading assets: {e}")
    pygame.quit(); sys.exit()
except FileNotFoundError as e:
    print(f"Asset file not found: {e}. Make sure assets/images directory exists and contains the png files.")
    pygame.quit(); sys.exit()


# --- Helper Functions ---
def format_time(seconds):
    if not isinstance(seconds, (int, float)) or seconds < 0: seconds = 0
    minutes = int(seconds // 60)
    remaining_seconds = int(math.ceil(seconds % 60))
    # Prevent 19:60, make it 20:00
    if remaining_seconds == 60 and minutes < 99:
        minutes += 1
        remaining_seconds = 0
    elif remaining_seconds == 60 and minutes >= 99: # Handle edge case
         remaining_seconds = 59
    return f"{minutes:02d}:{remaining_seconds:02d}"

# --- Drawing Functions ---
def draw_board(state):
    for r in range(8):
        for c in range(8):
            color = 'light gray' if (r + c) % 2 == 0 else 'dark gray'
            pygame.draw.rect(screen, color, [c * 100, r * 100, 100, 100])

    pygame.draw.rect(screen, 'gray', [0, 800, WIDTH, 100])
    pygame.draw.rect(screen, 'gold', [0, 800, WIDTH, 100], 5)
    pygame.draw.rect(screen, 'gold', [CHAT_X, CHAT_Y, CHAT_WIDTH, CHAT_HEIGHT + 100], 5) # Border around full right panel

    status_text = ['White\'s Turn', 'White Moving', 'Black\'s Turn', 'Black Moving']
    current_turn_step = state.get('turn_step', 0)
    turn_idx = current_turn_step if 0 <= current_turn_step < len(status_text) else 0
    turn_indicator = status_text[turn_idx]
    turn_color = 'white' if turn_idx < 2 else 'black'
    screen.blit(big_font.render(turn_indicator, True, turn_color), (20, 820))

    if my_color:
        screen.blit(font.render(f"You are: {my_color.capitalize()}", True, 'black'), (350, 820)) # Adjusted X pos
    elif state.get('game_started'):
         screen.blit(font.render("Assigning...", True, 'orange'), (350, 820))
    else: # Waiting state
         screen.blit(font.render("Waiting for opponent...", True, 'yellow'), (350, 820))


    for i in range(9):
        pygame.draw.line(screen, 'black', (0, 100 * i), (800, 100 * i), 2)
        pygame.draw.line(screen, 'black', (100 * i, 0), (100 * i, 800), 2)

def draw_pieces(state):
    global selection, my_color
    w_pieces = state.get('white_pieces', [])
    w_locs = state.get('white_locations', [])
    b_pieces = state.get('black_pieces', [])
    b_locs = state.get('black_locations', [])
    current_turn_step = state.get('turn_step', 0)

    if len(w_pieces) != len(w_locs): return
    if len(b_pieces) != len(b_locs): return

    for i in range(len(w_pieces)):
        try:
            loc = w_locs[i]; piece = w_pieces[i]
            if not isinstance(loc, (tuple, list)) or len(loc) != 2: continue
            if piece not in piece_list: continue
            index = piece_list.index(piece)
            if not (0 <= index < len(white_images)): continue
            image = white_images[index]
            x_pos = loc[0] * 100 + (17 if piece == 'pawn' else 10)
            y_pos = loc[1] * 100 + (17 if piece == 'pawn' else 10)
            screen.blit(image, (x_pos, y_pos))
            if my_color == 'white' and current_turn_step < 2 and selection == i:
                pygame.draw.rect(screen, 'red', [loc[0] * 100 + 1, loc[1] * 100 + 1, 98, 98], 3)
        except Exception as e: print(f"Error drawing white piece {i}: {e}")

    for i in range(len(b_pieces)):
        try:
            loc = b_locs[i]; piece = b_pieces[i]
            if not isinstance(loc, (tuple, list)) or len(loc) != 2: continue
            if piece not in piece_list: continue
            index = piece_list.index(piece)
            if not (0 <= index < len(black_images)): continue
            image = black_images[index]
            x_pos = loc[0] * 100 + (17 if piece == 'pawn' else 10)
            y_pos = loc[1] * 100 + (17 if piece == 'pawn' else 10)
            screen.blit(image, (x_pos, y_pos))
            if my_color == 'black' and current_turn_step >= 2 and selection == i:
                pygame.draw.rect(screen, 'blue', [loc[0] * 100 + 1, loc[1] * 100 + 1, 98, 98], 3)
        except Exception as e: print(f"Error drawing black piece {i}: {e}")

def draw_valid(moves):
    global my_color
    color = 'red' if my_color == 'white' else 'blue'
    if not isinstance(moves, list): return

    for move in moves:
        try:
            if isinstance(move, (list, tuple)) and len(move) == 2 and \
               all(isinstance(c, int) for c in move) and \
               0 <= move[0] <= 7 and 0 <= move[1] <= 7:
                 pygame.draw.circle(screen, color, (move[0] * 100 + 50, move[1] * 100 + 50), 10)
        except Exception as e: print(f"Error drawing valid move indicator: {e}")

counter = 0 # Global counter for blinking effects
def draw_check(state):
    global counter
    w_locs = state.get('white_locations', [])
    w_pieces = state.get('white_pieces', [])
    b_locs = state.get('black_locations', [])
    b_pieces = state.get('black_pieces', [])
    w_opts = state.get('white_options', [])
    b_opts = state.get('black_options', [])
    w_opts_flat = [move for sublist in w_opts if isinstance(sublist, list) for move in sublist if isinstance(move, (tuple, list)) and len(move) == 2]
    b_opts_flat = [move for sublist in b_opts if isinstance(sublist, list) for move in sublist if isinstance(move, (tuple, list)) and len(move) == 2]

    king_in_check = False
    king_location = None
    check_color = 'dark red'

    try: # Check White King
        if 'king' in w_pieces:
            king_index_w = w_pieces.index('king')
            if 0 <= king_index_w < len(w_locs):
                king_location_w = w_locs[king_index_w]
                if king_location_w in b_opts_flat:
                    king_in_check = True
                    king_location = king_location_w
                    check_color = 'dark red'
    except (ValueError, IndexError, TypeError): pass

    try: # Check Black King (only if white not in check)
        if not king_in_check and 'king' in b_pieces:
            king_index_b = b_pieces.index('king')
            if 0 <= king_index_b < len(b_locs):
                king_location_b = b_locs[king_index_b]
                if king_location_b in w_opts_flat:
                    king_in_check = True
                    king_location = king_location_b
                    check_color = 'dark blue'
    except (ValueError, IndexError, TypeError): pass

    if king_in_check and king_location and isinstance(king_location, (list, tuple)) and len(king_location) == 2:
        if counter < 15: # Blinking effect
            try:
                 pygame.draw.rect(screen, check_color, [king_location[0] * 100 + 1, king_location[1] * 100 + 1, 98, 98], 5)
            except Exception as e: print(f"Error drawing check rect: {e}")

def draw_game_over(state):
    winner = state.get('winner', '')
    if winner != '':
        try:
            pygame.draw.rect(screen, 'black', [200, 350, 600, 100])
            message = f'{winner.capitalize()} won the game'
            white_time = state.get('white_time', -1)
            black_time = state.get('black_time', -1)

            if winner == 'white' and black_time == 0: message += " (on time)!"
            elif winner == 'black' and white_time == 0: message += " (on time)!"
            # Add other win reasons if server sends them (e.g., disconnect)
            else: message += "!"

            screen.blit(medium_font.render(message, True, 'white'), (220, 360))
            screen.blit(font.render('Click anywhere to exit', True, 'white'), (380, 410))
        except Exception as e: print(f"Error rendering game over text: {e}")

def draw_chat(state):
    global text_offset, chat_scroll_offset, last_chat_length, my_color, chat_input, chat_active, cursor_visible
    chat_area_rect = pygame.Rect(CHAT_X, CHAT_Y, CHAT_WIDTH, CHAT_HEIGHT)

    # Background Gradient
    for i in range(CHAT_HEIGHT):
        ratio = i / CHAT_HEIGHT
        r = int(BG_COLOR_TOP[0] * (1 - ratio) + BG_COLOR_BOTTOM[0] * ratio)
        g = int(BG_COLOR_TOP[1] * (1 - ratio) + BG_COLOR_BOTTOM[1] * ratio)
        b = int(BG_COLOR_TOP[2] * (1 - ratio) + BG_COLOR_BOTTOM[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (CHAT_X, CHAT_Y + i), (CHAT_X + CHAT_WIDTH, CHAT_Y + i))
    pygame.draw.rect(screen, 'black', chat_area_rect, 2)

    # Message Rendering
    chat_history = state.get('chat_history', [])
    if not isinstance(chat_history, list): chat_history = []

    max_text_width = CHAT_WIDTH - 2 * BUBBLE_MARGIN - 2 * BUBBLE_PADDING - 10
    message_data = []
    line_height = font.get_linesize()

    for i, message in enumerate(chat_history):
         if not isinstance(message, dict): continue
         is_mine = message.get('sender') == my_color
         text = message.get('text', ''); timestamp = message.get('timestamp', '')
         words = text.split(' '); lines = []; current_line = ""
         # Word wrap logic (same as before)
         for word in words:
            if not word: continue
            test_line = current_line + word + " "
            try:
                 test_surface = font.render(test_line.strip(), True, 'black')
                 if test_surface.get_width() <= max_text_width: current_line = test_line
                 else:
                     if current_line: lines.append(current_line.strip())
                     if font.render(word, True, 'black').get_width() > max_text_width:
                          cutoff = 0
                          for k in range(len(word)):
                               if font.render(word[:k+1], True, 'black').get_width() > max_text_width: cutoff = k; break
                          if cutoff > 0: lines.append(word[:cutoff]) # Add cut part
                          current_line = word[cutoff:] + " " # Start new line with remainder
                     else: current_line = word + " "
            except Exception: current_line = word + " " # Fallback
         if current_line: lines.append(current_line.strip())
         if not lines and text: lines = [text]
         # Bubble size calculation (same as before)
         bubble_height = len(lines) * line_height + BUBBLE_PADDING * 2
         max_line_wd = 0
         if lines: max_line_wd = max(font.render(line, True, 'black').get_width() for line in lines)
         bubble_width = max(50, min(max_line_wd + BUBBLE_PADDING * 2, max_text_width + BUBBLE_PADDING * 2))
         try: ts_surf = small_font.render(timestamp, True, (0,0,0)); bubble_height += ts_surf.get_height() + 5
         except Exception: pass
         message_data.append({'is_mine': is_mine, 'lines': lines, 'ts': timestamp, 'w': bubble_width, 'h': bubble_height})


    # Scrolling (same as before)
    total_content_height = sum(md['h'] + BUBBLE_MARGIN for md in message_data)
    input_box_height = 50
    visible_message_area_height = CHAT_HEIGHT - input_box_height
    if len(chat_history) > last_chat_length:
        if chat_scroll_offset >= -(total_content_height - visible_message_area_height + 2 * line_height) or total_content_height <= visible_message_area_height :
             chat_scroll_offset = -max(0, total_content_height - visible_message_area_height)
    last_chat_length = len(chat_history)
    max_scroll = max(0, total_content_height - visible_message_area_height)
    chat_scroll_offset = max(-max_scroll, min(0, chat_scroll_offset))

    # Draw Messages (same as before)
    current_y = CHAT_Y + BUBBLE_MARGIN + chat_scroll_offset
    clip_rect_messages = pygame.Rect(CHAT_X, CHAT_Y, CHAT_WIDTH, visible_message_area_height)
    screen.set_clip(clip_rect_messages)
    for md in message_data:
        if current_y + md['h'] > CHAT_Y and current_y < CHAT_Y + visible_message_area_height:
            bubble_x = (CHAT_X + CHAT_WIDTH - md['w'] - BUBBLE_MARGIN) if md['is_mine'] else (CHAT_X + BUBBLE_MARGIN)
            bubble_rect = pygame.Rect(bubble_x, current_y, md['w'], md['h'])
            bubble_color = MY_BUBBLE_COLOR if md['is_mine'] else OPP_BUBBLE_COLOR
            try:
                pygame.draw.rect(screen, bubble_color, bubble_rect, border_radius=BUBBLE_RADIUS)
                text_y = current_y + BUBBLE_PADDING
                text_color = 'black' if md['is_mine'] else 'white'
                for line in md['lines']:
                    text_surface = font.render(line, True, text_color)
                    screen.blit(text_surface, (bubble_x + BUBBLE_PADDING, text_y))
                    text_y += line_height
                ts_surf = small_font.render(md['ts'], True, (100,100,100) if md['is_mine'] else (180,180,180))
                screen.blit(ts_surf, (bubble_x + BUBBLE_PADDING, text_y + 2))
            except Exception as e: print(f"Error drawing message bubble: {e}")
        current_y += md['h'] + BUBBLE_MARGIN
    screen.set_clip(None)

    # Draw Input Box (same as before)
    input_area_y = CHAT_Y + CHAT_HEIGHT - input_box_height + 5
    input_box_width = CHAT_WIDTH - 40
    input_box_rect = pygame.Rect(CHAT_X + 5, input_area_y, input_box_width, 30)
    visible_text_area_width = input_box_width - 10
    try:
        pygame.draw.rect(screen, (220, 220, 220), input_box_rect)
        pygame.draw.rect(screen, 'black', input_box_rect, 2 if not chat_active else 4)
        input_surface = font.render(chat_input, True, 'black')
        input_width = input_surface.get_width()
        if input_width > visible_text_area_width: text_offset = input_width - visible_text_area_width
        else: text_offset = 0
        cursor_screen_x = CHAT_X + 10 + input_width - text_offset
        clip_rect_input = pygame.Rect(CHAT_X + 10, input_area_y + 5, visible_text_area_width, 20)
        screen.set_clip(clip_rect_input)
        screen.blit(input_surface, (CHAT_X + 10 - text_offset, input_area_y + 5))
        screen.set_clip(None)
        if chat_active and cursor_visible:
            if CHAT_X + 10 <= cursor_screen_x <= CHAT_X + 10 + visible_text_area_width:
                pygame.draw.line(screen, 'black', (cursor_screen_x, input_area_y + 8), (cursor_screen_x, input_area_y + 22), 2)
        send_button_cx = CHAT_X + CHAT_WIDTH - 20; send_button_cy = input_area_y + 15; send_button_radius = 12
        pygame.draw.circle(screen, (0, 128, 0), (send_button_cx, send_button_cy), send_button_radius)
        pygame.draw.polygon(screen, 'white', [(send_button_cx - 4, send_button_cy - 5), (send_button_cx + 5, send_button_cy), (send_button_cx - 4, send_button_cy + 5)])
    except Exception as e: print(f"Error drawing chat input: {e}")


def draw_timers(state):
    white_time = state.get('white_time', INITIAL_TIME_SECONDS)
    black_time = state.get('black_time', INITIAL_TIME_SECONDS)
    timer_area_y = 810; timer_box_height = 80; timer_width_each = 130; spacing = 15
    black_timer_x = WIDTH - timer_width_each - 15
    white_timer_x = black_timer_x - timer_width_each - spacing
    white_timer_rect = pygame.Rect(white_timer_x, timer_area_y, timer_width_each, timer_box_height)
    black_timer_rect = pygame.Rect(black_timer_x, timer_area_y, timer_width_each, timer_box_height)
    try:
        pygame.draw.rect(screen, (210, 210, 210), white_timer_rect); pygame.draw.rect(screen, (40, 40, 40), black_timer_rect)
        pygame.draw.rect(screen, 'black', white_timer_rect, 2); pygame.draw.rect(screen, 'white', black_timer_rect, 2)
        white_time_str = format_time(white_time); black_time_str = format_time(black_time)
        white_label_surface = timer_label_font.render("White", True, 'black'); black_label_surface = timer_label_font.render("Black", True, 'white')
        white_timer_surface = timer_display_font.render(white_time_str, True, 'black'); black_timer_surface = timer_display_font.render(black_time_str, True, 'white')
        white_label_rect = white_label_surface.get_rect(centerx=white_timer_rect.centerx, top=white_timer_rect.top + 5)
        black_label_rect = black_label_surface.get_rect(centerx=black_timer_rect.centerx, top=black_timer_rect.top + 5)
        label_height = white_label_rect.height + 5
        white_text_rect = white_timer_surface.get_rect(centerx=white_timer_rect.centerx, centery=white_timer_rect.top + label_height + (white_timer_rect.height - label_height)/2)
        black_text_rect = black_timer_surface.get_rect(centerx=black_timer_rect.centerx, centery=black_timer_rect.top + label_height + (black_timer_rect.height - label_height)/2)
        screen.blit(white_label_surface, white_label_rect); screen.blit(black_label_surface, black_label_rect)
        screen.blit(white_timer_surface, white_text_rect); screen.blit(black_timer_surface, black_text_rect)
    except Exception as e: print(f"Error drawing timers: {e}")

# --- Networking Code ---

def receive_bytes(sock, num_bytes):
    data = b""
    while len(data) < num_bytes:
        try:
            # Check if socket is still valid before recv
            if sock.fileno() == -1: return None # Socket closed
            chunk = sock.recv(num_bytes - len(data))
            if not chunk: return None # Connection closed
            data += chunk
        except (socket.error, ConnectionResetError, OSError) as e: # Added OSError for fileno() check
             # print(f"Socket error/reset during receive_bytes: {e}") # Reduce noise
             return None
    return data

def receive_one_message(sock):
    if not sock or sock.fileno() == -1: return None # Check socket validity upfront

    header_data = receive_bytes(sock, HEADER_SIZE)
    if header_data is None: return None

    try: message_length = struct.unpack('>I', header_data)[0]
    except struct.error: return None

    message_data = receive_bytes(sock, message_length)
    if message_data is None: return None

    try:
        message = pickle.loads(message_data)
        return message
    except (pickle.UnpicklingError, ValueError, TypeError) as e: # Catch more potential unpickling errors
        print(f"Error unpickling message (length {message_length}): {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during unpickling: {e}")
        return None


def receive_updates():
    global game_state, connected, network_error, client_socket, game_state_lock, my_color
    print("Receive thread started.")
    while connected and client_socket:
        message = receive_one_message(client_socket)

        if message is None:
            if connected: network_error = "Connection lost."
            connected = False
            break

        # Process message
        if isinstance(message, dict):
            # Late assignment check
            if my_color is None and message.get('my_color_late'): # Example key
                 my_color = message['my_color_late']
                 print(f"Received late assignment: {my_color}")

            # Game state check (basic)
            if 'turn_step' in message and 'white_pieces' in message:
                 with game_state_lock: game_state = message
            # elif message.get('status') == 'waiting': # Example status msg
            #      print("Server update: Still waiting for opponent.")
            # else: Handle other dict messages

        elif isinstance(message, str) and message in ['white', 'black'] and my_color is None:
             # Handle initial assignment if received after 'waiting' status
             my_color = message
             print(f"Received assignment after waiting: {my_color}")
             # Optionally update display immediately?

        elif isinstance(message, str) and "error:" in message:
            err_msg = message.split(':', 1)[1]
            print(f"Received server error: {err_msg}")
            if err_msg == "server_full": network_error = "Server is full."; connected = False
            # Handle other errors

        # else: Ignore unexpected message types silently? or log warning.

    # Cleanup after loop
    print("Receive thread stopped.")
    connected = False
    if client_socket:
        try: client_socket.close()
        except: pass
        client_socket = None

# Server expects unframed messages from client for now
def send_message(message_type, data):
    global network_error, connected, client_socket
    if connected and client_socket and client_socket.fileno() != -1: # Check socket validity
        try:
            if message_type == 'chat' and isinstance(data, dict):
                data['timestamp'] = datetime.now().strftime("%I:%M %p")
            message = {'type': message_type, 'data': data}
            serialized_message = pickle.dumps(message)
            client_socket.sendall(serialized_message)
        except (socket.error, pickle.PicklingError, BrokenPipeError) as e:
            print(f"Send Error: {e}"); network_error = "Send failed"; connected = False
        except Exception as e:
            print(f"Unexpected Send Error: {e}"); network_error = "Send failed"; connected = False
    # else: Cannot send


def connect_to_server():
    global connected, my_color, network_error, client_socket, game_state_lock, game_state
    if client_socket:
        try: client_socket.close()
        except: pass
    try:
        print("Attempting connect...")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10.0) # Increased timeout
        client_socket.connect((SERVER_IP, PORT))
        client_socket.settimeout(None)
        print("Connected. Waiting for assignment...")

        assignment_data = receive_one_message(client_socket)

        if assignment_data is None: raise socket.error("No assignment received.")

        if isinstance(assignment_data, str) and assignment_data in ['white', 'black']:
            my_color = assignment_data
            print(f"Assigned color: {my_color}")
            connected = True; network_error = None
            threading.Thread(target=receive_updates, daemon=True).start()
        # Handle potential waiting status from server more explicitly if needed
        # elif isinstance(assignment_data, dict) and assignment_data.get("status") == "waiting": ...
        elif isinstance(assignment_data, str) and "error:" in assignment_data:
            network_error = f"Server Error: {assignment_data.split(':', 1)[1]}"
            print(network_error); connected = False; client_socket.close(); client_socket = None
        else: # Includes potential "waiting" status if not handled explicitly
            network_error = f"Unexpected assignment/status: {assignment_data}"
            print(network_error); connected = False; client_socket.close(); client_socket = None

    except socket.timeout: network_error = "Timeout connecting"; print(network_error); connected = False; client_socket = None
    except socket.error as e: network_error = f"Connection Error: {e}"; print(network_error); connected = False; client_socket = None
    except Exception as e: network_error = f"Connect Error: {e}"; print(network_error); connected = False; client_socket = None


# --- Main Game Loop ---
connect_to_server() # Attempt initial connection

run = True
while run:
    timer.tick(fps)
    elapsed_time = timer.get_time() / 1000.0

    # Cursor blinking
    cursor_timer += elapsed_time
    if cursor_timer >= 0.5:
        cursor_visible = not cursor_visible
        cursor_timer %= 0.5

    # Blinking for check indicator
    counter = (counter + 1) % 30

    # Get current state safely
    if connected:
        with game_state_lock: current_frame_state = game_state.copy()
    else:
        # Use default state if not connected
        current_frame_state = {
             'white_pieces': [], 'white_locations': [], 'black_pieces': [], 'black_locations': [],
             'captured_white': [], 'captured_black': [], 'turn_step': 0, 'game_over': False,
             'winner': '', 'white_options': [], 'black_options': [], 'chat_history': [],
             'white_time': 0, 'black_time': 0, 'game_started': False, 'game_id': None
        }

    # Drawing
    screen.fill((40, 40, 40))
    if not connected and network_error:
        # Draw Error Screen
        screen.fill('dark gray')
        try:
            err_surf = medium_font.render("Connection Failed", True, 'red')
            reason_surf = font.render(network_error, True, 'white')
            retry_surf = font.render("Click to retry, Q to Quit", True, 'yellow')
            screen.blit(err_surf, (WIDTH // 2 - err_surf.get_width() // 2, HEIGHT // 2 - 60))
            screen.blit(reason_surf, (WIDTH // 2 - reason_surf.get_width() // 2, HEIGHT // 2 - 20))
            screen.blit(retry_surf, (WIDTH // 2 - retry_surf.get_width() // 2, HEIGHT // 2 + 20))
        except Exception as e: print(f"Error drawing error screen: {e}")
    elif not connected and not network_error:
        # Draw Connecting Screen
        screen.fill('dark gray')
        try:
            conn_surf = medium_font.render("Connecting...", True, 'white')
            screen.blit(conn_surf, (WIDTH // 2 - conn_surf.get_width() // 2, HEIGHT // 2 - 20))
        except Exception as e: print(f"Error drawing connecting screen: {e}")
    # elif connected and my_color is None and not current_frame_state.get('game_started', False):
        # Draw Waiting Screen (handled by draw_board status text now)
        # pass
    elif connected: # Includes waiting, assigning, and playing states
        try:
            draw_board(current_frame_state)
            draw_pieces(current_frame_state)
            draw_check(current_frame_state)
            draw_chat(current_frame_state)
            draw_timers(current_frame_state)

            if selection != 100:
                if isinstance(valid_moves_display, list):
                    draw_valid(valid_moves_display)
                else: valid_moves_display = [] # Reset if invalid

            if current_frame_state.get('game_over', False):
                draw_game_over(current_frame_state)
        except Exception as draw_err:
             print(f"!!! Error during main drawing phase: {draw_err} !!!")


    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT: run = False

        if event.type == pygame.KEYDOWN:
            if not connected and network_error and event.key == pygame.K_q: run = False
            elif chat_active:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if chat_input.strip(): send_message('chat', {'text': chat_input.strip()}) # Sender added server-side/auto? Add here if needed.
                    chat_input = ""; text_offset = 0; cursor_visible = True; cursor_timer = 0
                elif event.key == pygame.K_BACKSPACE: chat_input = chat_input[:-1]
                elif event.key == pygame.K_ESCAPE: chat_active = False; text_offset = 0; cursor_visible = True; cursor_timer = 0
                else:
                    if len(chat_input) < 100 and event.unicode.isprintable(): chat_input += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN:
            x_coord, y_coord = event.pos
            if event.button == 1: # Left Click
                if not connected and network_error: # Click to retry
                    network_error = None; connect_to_server(); continue
                if connected and current_frame_state.get('game_over', False): # Click to exit after game over
                    run = False; continue

                # Check Chat Area Clicks
                input_area_y = CHAT_Y + CHAT_HEIGHT - 50 + 5
                input_box_rect = pygame.Rect(CHAT_X + 5, input_area_y, CHAT_WIDTH - 40, 30)
                send_button_cx = CHAT_X + CHAT_WIDTH - 20; send_button_cy = input_area_y + 15; send_button_radius_sq = 12**2
                clicked_chat_area = False
                if input_box_rect.collidepoint(x_coord, y_coord):
                     chat_active = True; cursor_visible = True; cursor_timer = 0; selection = 100; valid_moves_display = []; clicked_chat_area = True
                elif (x_coord - send_button_cx)**2 + (y_coord - send_button_cy)**2 <= send_button_radius_sq:
                    if chat_input.strip(): send_message('chat', {'text': chat_input.strip()})
                    chat_input = ""; text_offset = 0; cursor_visible = True; cursor_timer = 0; clicked_chat_area = True
                elif chat_active and CHAT_X <= x_coord < CHAT_X + CHAT_WIDTH : # Clicked somewhere in chat panel while active, but not input/send
                      # Potentially keep active, or deactivate based on exact location? For now, assume click outside input deactivates.
                      # If click is above input box, it might be message interaction (not implemented) or just deselect input
                      if y_coord < input_area_y: chat_active = False
                      clicked_chat_area = True # Handled chat click, don't process board
                elif CHAT_X <= x_coord < CHAT_X + CHAT_WIDTH: # Clicked in chat area while inactive
                     clicked_chat_area = True # Prevent board interaction


                # Check Board Clicks (Only if not a chat click and game is running)
                if connected and my_color and not clicked_chat_area and \
                   current_frame_state.get('game_started', False) and \
                   not current_frame_state.get('game_over', False) and \
                   0 <= x_coord < 800 and 0 <= y_coord < 800:
                    click_coords = (x_coord // 100, y_coord // 100)
                    is_my_turn = (my_color == 'white' and current_frame_state.get('turn_step', 0) < 2) or \
                                 (my_color == 'black' and current_frame_state.get('turn_step', 0) >= 2)

                    if is_my_turn:
                        my_pieces = current_frame_state.get(f'{my_color}_pieces', [])
                        my_locs = current_frame_state.get(f'{my_color}_locations', [])
                        my_opts = current_frame_state.get(f'{my_color}_options', [])

                        clicked_my_piece = False
                        clicked_piece_index = -1
                        if click_coords in my_locs:
                            try:
                                clicked_piece_index = my_locs.index(click_coords)
                                clicked_my_piece = True
                            except ValueError: pass # Should not happen if in my_locs

                        if clicked_my_piece:
                            if clicked_piece_index == selection: # Deselect
                                selection = 100; valid_moves_display = []
                            else: # Select new piece
                                selection = clicked_piece_index
                                # Validate options format before assigning
                                if 0 <= selection < len(my_opts) and isinstance(my_opts[selection], list):
                                     valid_moves_display = my_opts[selection]
                                else:
                                     valid_moves_display = []
                                     # print(f"Warn: No/invalid options for {my_color} piece {selection}") # Reduce noise
                        elif selection != 100: # Piece already selected, clicked elsewhere
                            if click_coords in valid_moves_display: # Clicked valid move
                                send_message('move', (selection, click_coords))
                                selection = 100; valid_moves_display = []
                            else: # Clicked invalid square, deselect
                                selection = 100; valid_moves_display = []
                        else: # Clicked empty/opponent square with nothing selected
                             selection = 100; valid_moves_display = []
                    else:
                        # print("Not your turn!") # Clicked out of turn
                        selection = 100; valid_moves_display = []

            # Chat Scroll Wheel
            elif event.button == 4: # Scroll Up
                 if CHAT_X <= x_coord <= CHAT_X + CHAT_WIDTH and CHAT_Y <= y_coord <= CHAT_Y + CHAT_HEIGHT - 50: # In chat message area
                      chat_scroll_offset = min(0, chat_scroll_offset + 30)
            elif event.button == 5: # Scroll Down
                 if CHAT_X <= x_coord <= CHAT_X + CHAT_WIDTH and CHAT_Y <= y_coord <= CHAT_Y + CHAT_HEIGHT - 50:
                      # Max scroll clamped in draw_chat, just decrease offset here
                      chat_scroll_offset -= 30


    pygame.display.flip()

# Cleanup
print("Exiting.")
connected = False
if client_socket:
    try: client_socket.close(); print("Socket closed.")
    except: pass
pygame.quit()
sys.exit()