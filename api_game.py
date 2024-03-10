import pygame
import sys
import requests
import random
import threading
import numpy as np
from time import time, sleep

pygame.mixer.init() 
pygame.mixer.music.set_volume(1.0)  

najz = pygame.mixer.Sound("components/najs.mp3")
najz.set_volume(7.0)
wall = pygame.mixer.Sound("components/wall.mp3")
wall.set_volume(1.0)
ghost = pygame.mixer.Sound("components/ghost.mp3")
ghost.set_volume(50.0)
swooshGhost = pygame.mixer.Sound("components/swoosh-ghost.mp3")
swooshGhost.set_volume(0.5)
diehard = pygame.mixer.Sound("components/diehard.mp3")
diehard.set_volume(1.0)

najz.play()

# API settings
ENDPOINT="http://127.0.0.1:5000"
MIN_VALUE = 20
MAX_VALUE = 80

# Initialize Pygame
pygame.init()
pygame.display.set_caption("TELEPRASE")
pygame.display.set_icon(pygame.image.load('components/flying_pig0.png'))
run = True
FRAME_RATE = 60
mode_attention = True # (True: attention, False: meditation)
difficulty = False # (True: easy, False: medium)
mode_counter = 1
MODE_SWAP_TRESHOLD = 3

# Set game window dimensions
WIN_WIDTH, WIN_HEIGHT = 1280, 720
win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

# Bird settings
BIRD_SCALE = 3
BIRD_WIDTH, BIRD_HEIGHT = 62*BIRD_SCALE, 56*BIRD_SCALE
bird_x, bird_y = 50, WIN_HEIGHT // 2
desired_bird_y = 50
y_desired_until = 0
FRAME_COUNT = 2
BIRD_FRAME_RATE = 15
ATTENTION_BIRD_FRAMES = [pygame.transform.scale(pygame.image.load(f'components/flying_shrek{i}.png'), (BIRD_WIDTH, BIRD_HEIGHT)) for i in range(FRAME_COUNT)]
MEDITATION_BIRD_FRAMES = [pygame.transform.scale(pygame.image.load(f'components/flying_pig{i}.png'), (BIRD_WIDTH, BIRD_HEIGHT)) for i in range(FRAME_COUNT)]
current_frame = 0
bird_frames = ATTENTION_BIRD_FRAMES

# scoreboard
score = 0
FONT = pygame.font.Font(None, 36)
font_color = (255, 255, 255)

# background
BACKGROUND_ATTENTION = pygame.image.load('components/wallpaper_attention.png')
BACKGROUND_MEDITATION = pygame.image.load('components/wallpaper_meditation.png')
bg1 = BACKGROUND_ATTENTION
bg2 = BACKGROUND_ATTENTION
bg_x1 = 0
bg_x2 = BACKGROUND_ATTENTION.get_width()

BIG_MONSTER_FRAMES = [pygame.transform.scale(pygame.image.load(f'components/big_monster{i}.png'), (WIN_HEIGHT, WIN_HEIGHT)) for i in range(FRAME_COUNT)]
monster_x = -BIG_MONSTER_FRAMES[0].get_width()

# Coin settings
coins = []
COIN_SIZE = 100
POSITIVE_COIN = pygame.transform.scale(pygame.image.load('components/coin.png'), (COIN_SIZE, COIN_SIZE))
NEGATIVE_COIN = pygame.transform.scale(pygame.image.load('components/monster.png'), (COIN_SIZE, COIN_SIZE - 20))
DOUBLE_COIN = pygame.transform.scale(pygame.image.load('components/coin2.png'), (COIN_SIZE, COIN_SIZE))


class Coin:
    def __init__(self, x, y, vel, score, decal):
        self.x = x
        self.y = y
        self.vel = vel
        self.score = score
        self.decal = decal

    def draw(self, win):
        win.blit(self.decal, (self.x, self.y))

    def update(self):
        self.x -= self.vel


def scale_value(value, old_min, old_max, new_min, new_max):
    return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min

# Set bird y position based on attention (runs on a separate thread)
def set_bird_y():
    global bird_y, run, mode_attention, mode_counter, font_color, desired_bird_y, y_desired_until, difficulty

    while run:
        response = requests.get(ENDPOINT + "/full")
        data = response.json()

        value = data['attention' if mode_attention else 'meditation']
        value = max(MIN_VALUE, min(MAX_VALUE, value))

        scaled_attention = scale_value(value, MIN_VALUE, MAX_VALUE, 0, 100)
        if difficulty:
            desired_bird_y = scaled_attention / 100
        else:
            desired_bird_y = WIN_HEIGHT - ((scaled_attention / 100)  * WIN_HEIGHT)
            desired_bird_y = max(0, min(WIN_HEIGHT - BIRD_HEIGHT, desired_bird_y))
            y_desired_until = time() + 0.5


def generate_coins():
    global score

    if difficulty:
        # Generate new coin based on polynomial approximation
        if random.randint(0, 100) < 3:
            offset = random.randint(-50, 50)
            coins.append(Coin(WIN_WIDTH, int(((45.0 + 45.0 * np.sin(time()))/ 100) * WIN_HEIGHT) + offset, 5, 1, POSITIVE_COIN))
        return

    # positive coin
    if random.randint(0, 100) < 2:
        y_pos = random.randint(0, WIN_HEIGHT * 0.4)
        coins.append(Coin(WIN_WIDTH, y_pos, 5, 1, POSITIVE_COIN))

    # enemies
    if score > 0 and random.randint(0, 100) < 2:
        y_pos = random.randint(0, (WIN_HEIGHT * 0.4 - COIN_SIZE)) + WIN_HEIGHT * 0.6
        coins.append(Coin(WIN_WIDTH, y_pos, 5, -1, NEGATIVE_COIN))

    # double coin
    if score > 25 and random.randint(0, 1000) < 5:
        y_pos = random.randint(0, WIN_HEIGHT * 0.3)
        coins.append(Coin(WIN_WIDTH, y_pos, 5, 2, DOUBLE_COIN))


def playGhost():
    sleep(5)
    ghost.play()

def swap_backgrounds():
    global bg_x1, bg_x2, bg1, bg2, monster_x, mode_attention, mode_counter, font_color, bird_frames

    # If the first image has moved off the screen, reset its position
    if bg_x1 <= -bg1.get_width():
        if mode_counter == 0:
            mode_attention = not mode_attention
            bg1 = BACKGROUND_ATTENTION if mode_attention else BACKGROUND_MEDITATION
            font_color = (255, 255, 255) if mode_attention else (0, 0, 0)
            bird_frames = ATTENTION_BIRD_FRAMES if mode_attention else MEDITATION_BIRD_FRAMES
            if mode_attention:
                wall.stop()
                najz.play()
            else:
                najz.stop()
                wall.play()
        bg_x1 = bg1.get_width()

    # If the second image has moved off the screen, reset its position
    if bg_x2 <= -bg2.get_width():
        mode_counter += 1

        if mode_counter == MODE_SWAP_TRESHOLD:
            mode_counter = 0
            monster_x = BACKGROUND_ATTENTION.get_width() - BIG_MONSTER_FRAMES[0].get_width() // 2
            bg2 = BACKGROUND_MEDITATION if mode_attention else BACKGROUND_ATTENTION
            threading.Thread(target=playGhost).start()

        bg_x2 = bg2.get_width()


def draw_background():
    global bg_x1, bg_x2, bg1, bg2, monster_x

    bg_x1 -= 5
    bg_x2 -= 5
    monster_x -= 5

    swap_backgrounds()

    # Draw the images
    win.blit(bg1, (bg_x1, 0))
    win.blit(bg2, (bg_x2, 0))

    if monster_x > -BIG_MONSTER_FRAMES[0].get_width():
        win.blit(BIG_MONSTER_FRAMES[current_frame > BIRD_FRAME_RATE], (monster_x, 0))


def draw_window():
    global current_frame, score, bird_y, mode_attention

    # Draw the background
    draw_background()

    # Draw the bird
    win.blit(bird_frames[current_frame > BIRD_FRAME_RATE], (bird_x, bird_y))
    current_frame = (current_frame + 1) % (FRAME_COUNT * BIRD_FRAME_RATE)
    bird_rect = pygame.Rect(bird_x, bird_y, BIRD_WIDTH, BIRD_HEIGHT)

    # Update and draw coins
    for coin in coins:
        coin.update()
        coin.draw(win)

        coin_rect = pygame.Rect(coin.x, coin.y, COIN_SIZE, COIN_SIZE)
        if bird_rect.colliderect(coin_rect):
            coins.remove(coin)
            if not difficulty:
                score += coin.score
            if coin.score < 0:
                swooshGhost.play()
        elif coin.x + COIN_SIZE < 0:
            coins.remove(coin)

    # Draw the UI
    draw_ui()

    pygame.display.update()  # Update the display


def draw_button(color, x, y, width, height, text):
    inverted_color = (255 - color[0], 255 - color[1], 255 - color[2])

    button = pygame.draw.rect(win, inverted_color, (x, y, width, height), border_radius=10)
    button = pygame.draw.rect(win, color, (x, y, width, height), 2, 10)
    button_text = FONT.render(text, True, color)
    win.blit(button_text, (x+20, y+12))

    return button


def draw_ui():
    global score, mode_attention, difficulty

    # info outline
    draw_button(font_color, WIN_WIDTH // 2 - 170, 10, 240, 75, "")

    # draw mode
    mode_text = FONT.render(f'Mode: {"Attention" if mode_attention else "Meditation"}', True, font_color)
    win.blit(mode_text, (WIN_WIDTH // 2 - 150, 20))

    # Draw the score
    score_text = FONT.render(f'Score: {score}', True, font_color)
    win.blit(score_text, (WIN_WIDTH // 2 - 100, 50))

    # buttons
    btn_hard = draw_button(font_color, WIN_WIDTH - 120, 10, 100, 50, "Hard")
    btn_medium = draw_button(font_color, WIN_WIDTH - 250, 10, 130, 50, "Medium")
    btn_easy = draw_button(font_color, WIN_WIDTH - 350, 10, 100, 50, "Demo")

    # button events
    if pygame.event.get(pygame.MOUSEBUTTONDOWN):
        mouse_pos = pygame.mouse.get_pos()

        if btn_hard.collidepoint(mouse_pos):
            print("Hard")
            hard_mode()
        if btn_medium.collidepoint(mouse_pos):
            print("Medium")
            difficulty = False
        if btn_easy.collidepoint(mouse_pos):
            print("Demo")
            difficulty = True


def die():
    global run, score, bird_y

    bird = "shrek" if mode_attention else "pig"
    frames = 12 if mode_attention else 16
    bottom = WIN_HEIGHT - 60

    animation = [y for y in range(int(bird_y), bottom + 1, ((bottom - int(bird_y)) // frames))]

    najz.stop()
    wall.stop()
    diehard.play()

    for i in range(1, frames+1):
        draw_background()

        # pig
        img = pygame.image.load(f'components/dying_{bird}/{i}.png')
        img = pygame.transform.scale(img, (BIRD_WIDTH, BIRD_HEIGHT))
        win.blit(img, (bird_x, animation[i-1]))

        # coins
        for coin in coins:
            coin.update()
            coin.draw(win)

        draw_ui()

        pygame.display.update()
        sleep(0.1)


def hard_mode():
    global run

    die()

    # draw image
    img_name = "rip_shrek" if mode_attention else "rip_pig"
    img = pygame.image.load(f'components/{img_name}.png')
    img = pygame.transform.scale(img, (WIN_HEIGHT * 0.8, WIN_HEIGHT * 0.8))
    win.blit(img, (WIN_WIDTH // 2 - (WIN_HEIGHT * 0.5), WIN_HEIGHT * 0.1))
    pygame.display.update()

    while run:
        if pygame.event.get(pygame.MOUSEBUTTONDOWN):
            run = False


def game_loop():
    global run, bird_y

    clock = pygame.time.Clock()

    thread = threading.Thread(target=set_bird_y)
    thread.start()

    # Game loop
    while run:
        clock.tick(FRAME_RATE)
        if difficulty:
            bird_y = int(((45.0 + 45.0 * np.sin(time() - 4.2))/ 100) * WIN_HEIGHT)

        else:
            if y_desired_until < time():
                bird_y = desired_bird_y
            else:
                bird_y = (desired_bird_y + bird_y) / 2

        if pygame.event.get(pygame.QUIT):
            run = False

        generate_coins()

        draw_window()


def main():
    game_loop()

    requests.post(ENDPOINT + "/addToLeaderboard", data=f"{score}")

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
