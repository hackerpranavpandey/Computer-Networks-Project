import pygame
import socket
import pickle
import threading
import sys
import time
from datetime import datetime

# --- Pygame Setup ---
pygame.init()

WIDTH = 1000
HEIGHT = 900
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption("Networked Chess Client")
font = pygame.font.Font('freesansbold.ttf', 20)
small_font = pygame.font.Font('freesansbold.ttf', 14)
medium_font = pygame.font.Font('freesansbold.ttf', 40)
big_font = pygame.font.Font('freesansbold.ttf', 50)
timer = pygame.time.Clock()
fps = 60

# --- Game State Variables ---
game_state = {
    'white_pieces': [], 'white_locations': [],
    'black_pieces': [], 'black_locations': [],
    'captured_white': [], 'captured_black': [],
    'turn_step': 0, 'game_over': False, 'winner': '',
    'white_options': [], 'black_options': [],
    'chat_history': []
}
game_state_lock = threading.Lock()
my_color = None
selection = 100
valid_moves_display = []

# --- Chat Variables ---
CHAT_WIDTH = 200
CHAT_HEIGHT = 300
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

# --- Load Assets ---
try:
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

# --- Drawing Functions ---

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
    pygame.draw.rect(screen, 'gold', [CHAT_X, 0, CHAT_WIDTH, HEIGHT], 5)

    status_text = ['White\'s Turn', 'White Moving', 'Black\'s Turn', 'Black Moving']
    turn_indicator = status_text[0] if current_turn_step == 0 else status_text[2]
    screen.blit(big_font.render(turn_indicator, True, 'black'), (20, 820))
    if my_color:
        screen.blit(font.render(f"You are: {my_color.capitalize()}", True, 'black'), (400, 820))

    for i in range(9):
        pygame.draw.line(screen, 'black', (0, 100 * i), (800, 100 * i), 2)
        pygame.draw.line(screen, 'black', (100 * i, 0), (100 * i, 800), 2)
    screen.blit(medium_font.render('FORFEIT', True, 'black'), (760, 830))

def draw_pieces(state):
    w_pieces = state['white_pieces']
    w_locs = state['white_locations']
    b_pieces = state['black_pieces']
    b_locs = state['black_locations']
    current_turn_step = state['turn_step']

    for i in range(len(w_pieces)):
        try:
            if w_pieces[i] not in piece_list:
                print(f"Invalid white piece: {w_pieces[i]} at index {i}")
                continue
            index = piece_list.index(w_pieces[i])
            if w_pieces[i] == 'pawn':
                screen.blit(white_pawn, (w_locs[i][0] * 100 + 22, w_locs[i][1] * 100 + 30))
            else:
                screen.blit(white_images[index], (w_locs[i][0] * 100 + 10, w_locs[i][1] * 100 + 10))
            if my_color == 'white' and current_turn_step < 2 and selection == i:
                pygame.draw.rect(screen, 'red', [w_locs[i][0] * 100 + 1, w_locs[i][1] * 100 + 1, 100, 100], 2)
        except (ValueError, IndexError) as e:
            print(f"Error drawing white piece at index {i}: {e}")
            continue

    for i in range(len(b_pieces)):
        try:
            if b_pieces[i] not in piece_list:
                print(f"Invalid black piece: {b_pieces[i]} at index {i}")
                continue
            index = piece_list.index(b_pieces[i])
            if b_pieces[i] == 'pawn':
                screen.blit(black_pawn, (b_locs[i][0] * 100 + 22, b_locs[i][1] * 100 + 30))
            else:
                screen.blit(black_images[index], (b_locs[i][0] * 100 + 10, b_locs[i][1] * 100 + 10))
            if my_color == 'black' and current_turn_step >= 2 and selection == i:
                pygame.draw.rect(screen, 'blue', [b_locs[i][0] * 100 + 1, b_locs[i][1][1] * 100 + 1, 100, 100], 2)
        except (ValueError, IndexError) as e:
            print(f"Error drawing black piece at index {i}: {e}")
            continue

def draw_valid(moves):
    color = 'red' if my_color == 'white' else 'blue'
    for i in range(len(moves)):
        try:
            pygame.draw.circle(screen, color, (moves[i][0] * 100 + 50, moves[i][1] * 100 + 50), 5)
        except IndexError:
            print(f"Error drawing valid move circle for move: {moves[i]}")

def draw_captured(state):
    cap_w = state['captured_white']
    cap_b = state['captured_black']
    for i in range(len(cap_w)):
        try:
            captured_piece = cap_w[i]
            index = piece_list.index(captured_piece)
            screen.blit(small_black_images[index], (775, 420 + 50 * i))
        except (ValueError, IndexError):
            continue
    for i in range(len(cap_b)):
        try:
            captured_piece = cap_b[i]
            index = piece_list.index(captured_piece)
            screen.blit(small_white_images[index], (875, 420 + 50 * i))
        except (ValueError, IndexError):
            continue

def draw_check(state):
    global counter
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

    if 'king' in w_pieces:
        king_index = w_pieces.index('king')
        king_location_w = w_locs[king_index]
        for i in range(len(b_opts)):
            if king_location_w in b_opts[i]:
                king_in_check = True
                king_location = king_location_w
                check_color = 'dark red'
                break

    if not king_in_check and 'king' in b_pieces:
        king_index = b_pieces.index('king')
        king_location_b = b_locs[king_index]
        for i in range(len(w_opts)):
            if king_location_b in w_opts[i]:
                king_in_check = True
                king_location = king_location_b
                check_color = 'dark blue'
                break

    if king_in_check and king_location:
        if counter < 15:
            pygame.draw.rect(screen, check_color, [king_location[0] * 100 + 1,
                                                  king_location[1] * 100 + 1, 100, 100], 5)

def draw_game_over(state):
    winner = state['winner']
    if winner != '':
        pygame.draw.rect(screen, 'black', [200, 350, 400, 100])
        message = f'{winner.capitalize()} won the game!'
        screen.blit(medium_font.render(message, True, 'white'), (220, 365))
        screen.blit(font.render('Click anywhere to exit', True, 'white'), (260, 415))

def draw_chat(state):
    global text_offset, chat_scroll_offset, last_chat_length
    # Draw gradient background
    for i in range(CHAT_HEIGHT):
        ratio = i / CHAT_HEIGHT
        r = int(BG_COLOR_TOP[0] * (1 - ratio) + BG_COLOR_BOTTOM[0] * ratio)
        g = int(BG_COLOR_TOP[1] * (1 - ratio) + BG_COLOR_BOTTOM[1] * ratio)
        b = int(BG_COLOR_TOP[2] * (1 - ratio) + BG_COLOR_BOTTOM[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (CHAT_X, CHAT_Y + i), (CHAT_X + CHAT_WIDTH, CHAT_Y + i))

    # Draw border
    pygame.draw.rect(screen, 'black', [CHAT_X, CHAT_Y, CHAT_WIDTH, CHAT_HEIGHT], 2)

    # Process all messages to calculate total height
    chat_history = state['chat_history']
    max_width = CHAT_WIDTH - 2 * BUBBLE_MARGIN - 2 * BUBBLE_PADDING - 20
    message_data = []

    for i in range(len(chat_history)):
        message = chat_history[i]
        is_mine = message['sender'] == my_color
        text = message['text']
        timestamp = message.get('timestamp', 'Unknown')

        text_surface = font.render(text, True, 'black' if is_mine else 'white')
        text_width = text_surface.get_width()
        if text_width > max_width:
            words = text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + word + " "
                test_surface = font.render(test_line, True, 'black' if is_mine else 'white')
                if test_surface.get_width() <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                lines.append(current_line.strip())
        else:
            lines = [text]

        bubble_height = len(lines) * 20 + BUBBLE_PADDING * 2
        bubble_width = max([font.render(line, True, 'black' if is_mine else 'white').get_width() for line in lines]) + BUBBLE_PADDING * 2
        bubble_width = min(bubble_width, max_width + BUBBLE_PADDING * 2)
        timestamp_surface = small_font.render(timestamp, True, (200, 200, 200))
        bubble_height += timestamp_surface.get_height() + 5

        message_data.append((i, is_mine, lines, timestamp, bubble_width, bubble_height))

    # Calculate total chat height
    total_height = sum(bubble_height + BUBBLE_MARGIN for _, _, _, _, _, bubble_height in message_data) if message_data else 0
    visible_height = CHAT_HEIGHT - 50

    # Auto-scroll to newest message if chat_history grew and user is near bottom
    if len(chat_history) > last_chat_length and chat_scroll_offset > -50:
        chat_scroll_offset = -max(0, total_height - visible_height)
    last_chat_length = len(chat_history)

    # Cap scroll offset
    max_scroll = max(0, total_height - visible_height)
    chat_scroll_offset = max(-max_scroll, min(0, chat_scroll_offset))

    # Render messages from oldest to newest
    current_y = CHAT_Y + chat_scroll_offset
    visible_messages = []

    for i, is_mine, lines, timestamp, bubble_width, bubble_height in message_data:
        if current_y + bubble_height + BUBBLE_MARGIN > CHAT_Y + CHAT_HEIGHT - 50:
            current_y += bubble_height + BUBBLE_MARGIN
            continue
        if current_y >= CHAT_Y - bubble_height:
            visible_messages.append((i, is_mine, lines, timestamp, bubble_width, bubble_height, current_y))
        current_y += bubble_height + BUBBLE_MARGIN

    # Render visible messages
    for i, is_mine, lines, timestamp, bubble_width, bubble_height, y_offset in visible_messages:
        if is_mine:
            bubble_x = CHAT_X + CHAT_WIDTH - bubble_width - BUBBLE_MARGIN
        else:
            bubble_x = CHAT_X + BUBBLE_MARGIN

        shadow_surface = pygame.Surface((bubble_width + 4, bubble_height + 4), pygame.SRCALPHA)
        shadow_surface.fill(SHADOW_COLOR)
        screen.blit(shadow_surface, (bubble_x + 2, y_offset + 2))

        pygame.draw.rect(screen, MY_BUBBLE_COLOR if is_mine else OPP_BUBBLE_COLOR,
                         [bubble_x, y_offset, bubble_width, bubble_height])
        for corner in [(bubble_x, y_offset), (bubble_x + bubble_width - BUBBLE_RADIUS * 2, y_offset),
                       (bubble_x, y_offset + bubble_height - BUBBLE_RADIUS * 2),
                       (bubble_x + bubble_width - BUBBLE_RADIUS * 2, y_offset + bubble_height - BUBBLE_RADIUS * 2)]:
            pygame.draw.circle(screen, MY_BUBBLE_COLOR if is_mine else OPP_BUBBLE_COLOR,
                               (corner[0] + BUBBLE_RADIUS, corner[1] + BUBBLE_RADIUS), BUBBLE_RADIUS)

        text_y = y_offset + BUBBLE_PADDING
        for line in lines:
            text_surface = font.render(line, True, 'black' if is_mine else 'white')
            screen.blit(text_surface, (bubble_x + BUBBLE_PADDING, text_y))
            text_y += 20

        timestamp_surface = small_font.render(timestamp, True, (200, 200, 200))
        screen.blit(timestamp_surface, (bubble_x + BUBBLE_PADDING, text_y + 5))

    # Draw input box
    input_y = CHAT_Y + CHAT_HEIGHT - 40
    input_box_width = CHAT_WIDTH - 40
    visible_width = input_box_width - 10
    pygame.draw.rect(screen, (220, 220, 220), [CHAT_X + 5, input_y, input_box_width, 30])
    pygame.draw.rect(screen, 'black', [CHAT_X + 5, input_y, input_box_width, 30], 2 if not chat_active else 4)

    input_surface = font.render(chat_input, True, 'black')
    tentative_cursor_x = CHAT_X + 10 + input_surface.get_width()
    if tentative_cursor_x > CHAT_X + 5 + visible_width:
        text_offset = input_surface.get_width() - visible_width
    elif input_surface.get_width() < visible_width:
        text_offset = 0

    cursor_x = CHAT_X + 10 + input_surface.get_width() - text_offset

    clip_rect = pygame.Rect(CHAT_X + 5, input_y, input_box_width, 30)
    screen.set_clip(clip_rect)
    screen.blit(input_surface, (CHAT_X + 10 - text_offset, input_y + 5))
    
    if chat_active and cursor_visible:
        if CHAT_X + 5 <= cursor_x <= CHAT_X + 5 + visible_width:
            pygame.draw.line(screen, 'black', (cursor_x, input_y + 8), (cursor_x, input_y + 22), 2)
    
    screen.set_clip(None)

    # Draw send button
    send_x = CHAT_X + CHAT_WIDTH - 30
    pygame.draw.circle(screen, (0, 128, 0), (send_x + 15, input_y + 15), 12)
    pygame.draw.polygon(screen, 'white', [(send_x + 10, input_y + 10), (send_x + 20, input_y + 15), (send_x + 10, input_y + 20)])

# --- Networking Code ---
SERVER_IP = '127.0.0.1'
PORT = 5555
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
network_error = None

def connect_to_server():
    global connected, my_color, network_error, client_socket
    try:
        print(f"Attempting to connect to {SERVER_IP}:{PORT}...")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, PORT))
        print("Connected to server.")

        color_data = client_socket.recv(1024)
        received_color = pickle.loads(color_data)

        if isinstance(received_color, str) and received_color in ['white', 'black']:
            my_color = received_color
            print(f"Assigned color: {my_color}")
            connected = True
            network_error = None
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
    except Exception as e:
        network_error = f"An unexpected error occurred during connection: {e}"
        print(network_error)
        connected = False

def receive_updates():
    global game_state, connected, network_error
    while connected:
        try:
            data = client_socket.recv(4096 * 2)
            if not data:
                print("Server disconnected (received empty data).")
                network_error = "Server disconnected."
                connected = False
                break

            message = pickle.loads(data)
            if isinstance(message, dict):
                with game_state_lock:
                    for msg in message['chat_history']:
                        if 'timestamp' not in msg:
                            msg['timestamp'] = datetime.now().strftime("%I:%M %p")
                    game_state = message
            elif isinstance(message, str) and "error:" in message:
                print(f"Received server message: {message}")
                network_error = message.split(':')[1]

        except (socket.error, EOFError, ConnectionResetError) as e:
            if connected:
                print(f"Network error receiving data: {e}")
                network_error = "Connection lost."
            connected = False
            break
        except pickle.UnpicklingError as e:
            print(f"Error decoding message: {e}")
        except Exception as e:
            print(f"Unexpected error in receive thread: {e}")
            network_error = "An unexpected error occurred."
            connected = False
            break
    print("Receive thread stopped.")
    try:
        client_socket.close()
        print("Client socket closed by receive thread.")
    except socket.error:
        pass

def send_message(message_type, data):
    global network_error, connected, chat_scroll_offset
    if connected:
        try:
            if message_type == 'chat':
                data['timestamp'] = datetime.now().strftime("%I:%M %p")
            message = {'type': message_type, 'data': data}
            data = pickle.dumps(message)
            client_socket.sendall(data)
            # Scroll to newest message after sending chat
            if message_type == 'chat':
                # Defer scroll to draw_chat to use updated total_height
                pass
        except socket.error as e:
            print(f"Failed to send message: {e}")
            network_error = "Failed to send message - Connection issue?"
            connected = False
        except Exception as e:
            print(f"Unexpected error sending message: {e}")

# --- Main Game Loop ---
connect_to_server()
counter = 0
run = True
while run:
    timer.tick(fps)
    elapsed = 1 / fps

    # Update cursor blink
    cursor_timer += elapsed
    if cursor_timer >= 0.5:
        cursor_visible = not cursor_visible
        cursor_timer = 0

    if counter < 30:
        counter += 1
    else:
        counter = 0
    screen.fill('dark gray')

    with game_state_lock:
        current_state = game_state.copy()

    if not connected and network_error:
        screen.fill('dark gray')
        error_text = medium_font.render("Connection Failed", True, 'red')
        reason_text = font.render(network_error, True, 'white')
        retry_text = font.render("Click to retry, Q to Quit", True, 'yellow')
        screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(reason_text, (WIDTH // 2 - reason_text.get_width() // 2, HEIGHT // 2))
        screen.blit(retry_text, (WIDTH // 2 - retry_text.get_width() // 2, HEIGHT // 2 + 40))

    elif not connected and not network_error:
        screen.fill('dark gray')
        connecting_text = medium_font.render("Connecting to server...", True, 'white')
        screen.blit(connecting_text, (WIDTH // 2 - connecting_text.get_width() // 2, HEIGHT // 2 - 20))

    elif connected and my_color is None:
        screen.fill('dark gray')
        waiting_text = medium_font.render("Connected. Waiting for assignment...", True, 'white')
        screen.blit(waiting_text, (WIDTH // 2 - waiting_text.get_width() // 2, HEIGHT // 2 - 20))

    elif connected and my_color:
        is_my_turn = (my_color == 'white' and current_state['turn_step'] < 2) or \
                     (my_color == 'black' and current_state['turn_step'] >= 2)

        draw_board(current_state['turn_step'])
        draw_pieces(current_state)
        draw_captured(current_state)
        draw_check(current_state)
        draw_chat(current_state)
        if selection != 100:
            draw_valid(valid_moves_display)

        if current_state['game_over']:
            draw_game_over(current_state)

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if not connected and event.key == pygame.K_q:
                run = False
            elif connected and chat_active:
                if event.key == pygame.K_RETURN and chat_input.strip():
                    send_message('chat', {'sender': my_color, 'text': chat_input.strip()})
                    chat_input = ""
                    text_offset = 0
                    cursor_visible = True
                    cursor_timer = 0
                elif event.key == pygame.K_BACKSPACE:
                    if chat_input:
                        chat_input = chat_input[:-1]
                        input_surface = font.render(chat_input, True, 'black')
                        visible_width = CHAT_WIDTH - 50
                        cursor_x = input_surface.get_width()
                        if cursor_x < visible_width:
                            text_offset = 0
                        else:
                            text_offset = cursor_x - visible_width
                elif event.key == pygame.K_ESCAPE:
                    chat_active = False
                    chat_input = ""
                    text_offset = 0
                    cursor_visible = True
                    cursor_timer = 0
                else:
                    if len(chat_input) < 50:
                        char = event.unicode
                        if char.isprintable():
                            chat_input += char
                            input_surface = font.render(chat_input, True, 'black')
                            visible_width = CHAT_WIDTH - 50
                            cursor_x = input_surface.get_width()
                            if cursor_x > visible_width:
                                text_offset = cursor_x - visible_width
                            else:
                                text_offset = 0

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x_coord = event.pos[0]
            y_coord = event.pos[1]
            click_coords = (x_coord // 100, y_coord // 100)

            if not connected and network_error:
                network_error = None
                connect_to_server()
                continue

            if connected and current_state.get('game_over'):
                run = False
                continue

            input_y = CHAT_Y + CHAT_HEIGHT - 40
            send_x = CHAT_X + CHAT_WIDTH - 30
            if connected and (
                (CHAT_X + 5 <= x_coord <= CHAT_X + CHAT_WIDTH - 40 and input_y <= y_coord <= input_y + 30) or
                ((send_x <= x_coord <= send_x + 30 and input_y <= y_coord <= input_y + 30) and chat_input.strip())
            ):
                if (send_x <= x_coord <= send_x + 30 and input_y <= y_coord <= input_y + 30) and chat_input.strip():
                    send_message('chat', {'sender': my_color, 'text': chat_input.strip()})
                    chat_input = ""
                    chat_active = False
                    text_offset = 0
                    cursor_visible = True
                    cursor_timer = 0
                else:
                    chat_active = True
                    cursor_visible = True
                    cursor_timer = 0
                continue

            if connected and my_color and is_my_turn and 0 <= click_coords[0] <= 7 and 0 <= click_coords[1] <= 7:
                current_locations = current_state['white_locations'] if my_color == 'white' else current_state['black_locations']
                current_options = current_state['white_options'] if my_color == 'white' else current_state['black_options']

                if click_coords in current_locations:
                    new_selection = current_locations.index(click_coords)
                    if new_selection == selection:
                        selection = 100
                        valid_moves_display = []
                    else:
                        selection = new_selection
                        if 0 <= selection < len(current_options):
                            valid_moves_display = current_options[selection]
                        else:
                            valid_moves_display = []
                            selection = 100

                elif selection != 100:
                    if click_coords in valid_moves_display:
                        move_to_send = (selection, click_coords)
                        send_message('move', move_to_send)
                        selection = 100
                        valid_moves_display = []
                    else:
                        selection = 100
                        valid_moves_display = []

            elif connected and my_color and not is_my_turn and 0 <= click_coords[0] <= 7 and 0 <= click_coords[1] <= 7:
                print("Not your turn!")

        if event.type == pygame.MOUSEWHEEL and connected:
            mouse_pos = pygame.mouse.get_pos()
            if CHAT_X <= mouse_pos[0] <= CHAT_X + CHAT_WIDTH and CHAT_Y <= mouse_pos[1] <= CHAT_Y + CHAT_HEIGHT:
                chat_scroll_offset += event.y * 20  # Wheel down (-1) decreases offset (older), wheel up (+1) increases (newer)

    pygame.display.flip()

# --- Cleanup ---
if connected:
    try:
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()
        print("Client socket closed.")
    except socket.error as e:
        print(f"Error closing socket: {e}")

pygame.quit()
sys.exit()