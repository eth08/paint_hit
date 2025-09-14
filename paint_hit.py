# file: paint_hit.py

import sys
import random
import math
import json
import os
import webbrowser

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame


# --- Constants & Initialization ---
__version__ = "0.8.2"
__author__= "eth08"

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (196,32,92)
GREEN = (56,228,36)
BLUE = (4,164,236)
YELLOW = (252,220,4)
GREY = (100, 100, 100)
LIGHT_GREY = (170, 170, 170)
HIGHSCORE_FILE = 'highscores.json'
CONFIG_FILE = 'config.json'

# Stylish UI palette
BACKGROUND_COLOR = (24, 26, 29)
BUTTON_COLOR = (44, 47, 51)
HOVER_COLOR = (70, 75, 80)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (88, 101, 242)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Paint (H)it")

# --- Fonts ---
font = pygame.font.Font(None, 36)
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 50)
font_small = pygame.font.Font(None, 24)

# --- Asset Loading & Config Management ---
custom_faces_paths = [None] * 4
custom_background_path = None
loaded_custom_faces = [None] * 4
game_settings = {}

# --- Helper: File validation ---
def is_valid_image(path):
    return path.lower().endswith((".png", ".jpg", ".jpeg"))

def load_default_background():
    global background_img
    try:
        background_img = pygame.image.load('background.jpg').convert()
    except pygame.error as e:
        print(f"Warning: Default background.jpg not found. Using a solid color. Error: {e}")
        background_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background_img.fill(BACKGROUND_COLOR)
    background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

def load_config():
    global custom_background_path, custom_faces_paths, loaded_custom_faces, game_settings
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            custom_background_path = config.get('background_path')
            saved_paths = config.get('faces_paths', [])
            game_settings = config.get('game_settings', {})
    except (FileNotFoundError, json.JSONDecodeError):
        custom_background_path = None
        saved_paths = []
        game_settings = {}

    # Attempt to load assets from the paths
    if custom_background_path and os.path.exists(custom_background_path):
        try:
            new_bg = pygame.image.load(custom_background_path).convert()
            global background_img
            background_img = pygame.transform.scale(new_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error as e:
            print(f"Error loading saved background: {e}")
            load_default_background()
    else:
        load_default_background()

    loaded_custom_faces = [None] * 4
    custom_faces_paths = [None] * 4
    for i, path in enumerate(saved_paths):
        if i < 4 and path and os.path.exists(path):
            try:
                face = pygame.image.load(path).convert_alpha()
                loaded_custom_faces[i] = face
                custom_faces_paths[i] = path
            except pygame.error as e:
                print(f"Error loading saved face from {path}: {e}")

def save_config():
    config = {
        'background_path': custom_background_path,
        'faces_paths': [path for path in custom_faces_paths if path is not None],
        'game_settings': game_settings
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

load_config()

try:
    gun_img = pygame.image.load('gun.png').convert_alpha()
    gun_img = pygame.transform.scale(gun_img, (200, 200))
    silhouette_img = pygame.image.load('silhouette.png').convert_alpha()
    target_img = pygame.image.load('target.jpg').convert_alpha()
    question_mark_img = pygame.image.load('question_mark.png').convert_alpha()
    splat_base_images = {
        RED: pygame.image.load('splat_red.png').convert_alpha(),
        GREEN: pygame.image.load('splat_green.png').convert_alpha(),
        BLUE: pygame.image.load('splat_blue.png').convert_alpha(),
        YELLOW: pygame.image.load('splat_yellow.png').convert_alpha(),
    }
except pygame.error as e:
    print(f"Fatal Error: Could not load image asset: {e}")
    sys.exit()


# --- Utility Functions ---
def load_high_scores():
    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_high_scores(scores):
    with open(HIGHSCORE_FILE, 'w') as f:
        json.dump(scores, f, indent=4)

def check_for_high_score(score, scores):
    return len(scores) < 10 or score > min(s['score'] for s in scores)

def add_high_score(name, score, scores):
    scores.append({'name': name, 'score': score})
    scores.sort(key=lambda s: s['score'], reverse=True)
    return scores[:10]

# --- Game Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(centerx=SCREEN_WIDTH / 2, bottom=SCREEN_HEIGHT)

    def update(self):
        self.rect.centerx = pygame.mouse.get_pos()[0]
        self.rect.clamp_ip(screen.get_rect())

class Splat:
    def __init__(self, norm_pos, color):
        self.norm_pos = norm_pos
        self.base_image = splat_base_images[color]
        self.rotation = random.randint(0, 360)

class Target(pygame.sprite.Sprite):
    LANES = [200, 400, 600, 800]

    def __init__(self, base_silhouette_img, base_target_img, face_img, speed_multiplier):
        super().__init__()
        self.base_silhouette_img = base_silhouette_img
        self.base_target_img = base_target_img
        self.face_img = face_img
        self.splats = []
        self.y = 60
        self.x = random.choice(self.LANES)
        self.target_lane_x = self.x
        self.scale = 0.10
        self.speed = random.uniform(0.5, 1.2) * speed_multiplier
        self.falling, self.fall_speed = False, 0
        self.lane_change_timer = random.randint(120, 240)
        self.face_box = (0.35, 0.05, 0.30, 0.20)
        self.update_image()
        self.target_center_rect_on_image = None
        
    def is_face_hit(self, pos):
        return self.face_abs_rect.collidepoint(pos)

    def score_body(self, pos):
        distance = math.hypot(pos[0] - self.target_center_abs[0], pos[1] - self.target_center_abs[1])
        if distance <= self.target_radius * 0.2:
            return 10
        if distance <= self.target_radius:
            return 5
        elif self.rect.collidepoint(pos):
            return 1
        return 0

    def add_splat(self, hit_pos, color):
        norm_x = (hit_pos[0] - self.rect.left) / self.scale
        norm_y = (hit_pos[1] - self.rect.top) / self.scale
        self.splats.append(Splat((norm_x, norm_y), color))

    def update_image(self):
        width = int(self.base_silhouette_img.get_width() * self.scale)
        height = int(self.base_silhouette_img.get_height() * self.scale)
        if width < 1 or height < 1: return
        self.image = pygame.transform.scale(self.base_silhouette_img, (width, height))
        tgt_size = int(width * 0.5)
        scaled_target = pygame.transform.scale(self.base_target_img, (tgt_size, tgt_size))
        self.target_pos_on_image = (int(width * 0.25), int(height * 0.3))
        self.image.blit(scaled_target, self.target_pos_on_image)
        if self.face_img:
            fx, fy, fw, fh = self.face_box
            face_w, face_h = int(width * fw), int(height * fh)
            if face_w > 0 and face_h > 0:
                scaled_face = pygame.transform.scale(self.face_img, (face_w, face_h))
                self.image.blit(scaled_face, (int(width * fx), int(height * fy)))

        for splat in self.splats:
            base_w = int(self.base_silhouette_img.get_width() * 0.2)
            cur_w = int(base_w * self.scale)
            if cur_w < 1: continue
            scaled_splat = pygame.transform.scale(splat.base_image, (cur_w, cur_w))
            rotated_splat = pygame.transform.rotate(scaled_splat, splat.rotation)
            cx = splat.norm_pos[0] * self.scale
            cy = splat.norm_pos[1] * self.scale
            srect = rotated_splat.get_rect(center=(cx, cy))
            self.image.blit(rotated_splat, srect)

        self.rect = self.image.get_rect(center=(self.x, self.y))
        fx, fy, fw, fh = self.face_box
        face_rect_on_image = pygame.Rect(int(width * fx), int(height * fy), int(width * fw), int(height * fh))
        if self.rect.top + face_rect_on_image.top < 0:
            self.y -= (self.rect.top + face_rect_on_image.top)
            self.rect = self.image.get_rect(center=(self.x, self.y))
        self.face_abs_rect = pygame.Rect(self.rect.left + face_rect_on_image.left, self.rect.top + face_rect_on_image.top, face_rect_on_image.width, face_rect_on_image.height)
        self.target_center_abs = (self.rect.left + self.target_pos_on_image[0] + tgt_size / 2, self.rect.top + self.target_pos_on_image[1] + tgt_size / 2)
        self.target_radius = tgt_size / 2
        self.red_circle_abs_rect = pygame.Rect(
            self.target_center_abs[0] - self.target_radius * 0.2,
            self.target_center_abs[1] - self.target_radius * 0.2,
            self.target_radius * 0.4,
            self.target_radius * 0.4
        )
        
    def update(self):
        if not self.falling:
            self.lane_change_timer -= 1
            if self.lane_change_timer <= 0:
                possible_lanes = [l for l in self.LANES if l != self.target_lane_x]
                if possible_lanes:
                    self.target_lane_x = random.choice(possible_lanes)
                self.lane_change_timer = random.randint(180, 300)
            self.x += (self.target_lane_x - self.x) * 0.02
            self.y += self.speed
            self.scale += self.speed * 0.003
            if self.y > 650:
                if game.state == 'PLAYING':
                    game.lose_life()
                self.kill()
            else:
                self.update_image()
        else:
            self.y += self.fall_speed
            self.fall_speed += 0.5
            if self.y > SCREEN_HEIGHT: self.kill()
            else: self.update_image()

    def fall(self):
        self.falling, self.fall_speed = True, 5

class Game:
    def __init__(self):
        self.author_url = "https://github.com/eth08"
        self.state = 'MENU'
        self.clock = pygame.time.Clock()
        self.high_scores = load_high_scores()
        self.player = Player(gun_img)
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.targets = pygame.sprite.Group()
        self.speed_setting = game_settings.get('speed_setting', 'Normal')
        self.speed_multipliers = {'Easy': 0.7, 'Normal': 1.0, 'Hard': 1.5}
        self.challenge_duration_str = game_settings.get('challenge_duration', "60")
        try:
            self.challenge_duration = int(self.challenge_duration_str)
        except ValueError:
            self.challenge_duration = 60
        self.input_box_active = None
        self.player_name = ""
        self.last_path = game_settings.get('last_path', os.path.expanduser('~'))
        self.confirmation_active = None
        self.last_game_mode = 'PLAYING'
        self.running = True

        self.flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.flash_surface.fill((255, 0, 0, 128))
        self.flash_timer = 0
        
        self.face_slot_to_edit = None
        self.error_message = None
        self.error_timer = 0

        self.buttons = {
            'classic': pygame.Rect(SCREEN_WIDTH/2 - 150, 250, 300, 60),
            'timed': pygame.Rect(SCREEN_WIDTH/2 - 150, 320, 300, 60),
            'scores': pygame.Rect(SCREEN_WIDTH/2 - 150, 390, 300, 60),
            'settings': pygame.Rect(SCREEN_WIDTH/2 - 150, 460, 300, 60),
            'about': pygame.Rect(SCREEN_WIDTH/2 - 150, 530, 300, 60),
            'quit': pygame.Rect(SCREEN_WIDTH/2 - 150, 600, 300, 60),
            'easy': pygame.Rect(200, 280, 150, 60),
            'normal': pygame.Rect(425, 280, 150, 60),
            'hard': pygame.Rect(650, 280, 150, 60),
            'faces': pygame.Rect(SCREEN_WIDTH/2 - 150, 420, 300, 60),
            'background': pygame.Rect(SCREEN_WIDTH/2 - 150, 490, 300, 60),
            'back_settings': pygame.Rect(SCREEN_WIDTH/2 - 150, 650, 300, 60),
            'back_faces': pygame.Rect(SCREEN_WIDTH/2 - 150, 650, 300, 60),
            'back_scores': pygame.Rect(SCREEN_WIDTH/2 - 150, 700, 300, 60),
            'back_about': pygame.Rect(SCREEN_WIDTH/2 - 150, 650, 300, 60),
            'back_file_explorer': pygame.Rect(50, SCREEN_HEIGHT - 80, 200, 60),
            'back_timed_setup': pygame.Rect(SCREEN_WIDTH/2 - 150, 580, 300, 60),
            'skip_score': pygame.Rect(SCREEN_WIDTH - 250, 700, 200, 60)
        }
        self.face_upload_rects = [pygame.Rect(100 + i * 225, 300, 200, 250) for i in range(4)]
        self.file_explorer_path = self.last_path
        self.file_explorer_mode = None
        self.scroll_offset = 0
        self.reset()

    def lose_life(self):
        if self.state != 'PLAYING' or self.game_over:
            return
            
        if self.lives > 0:
            self.lives -= 1
            self.flash_timer = 30
        
        if self.lives <= 0:
            self.last_game_mode = self.state
            self.game_over = True
            self.state = 'GAME_OVER'
            self.last_state = 'classic'

    def reset(self):
        self.lives = 5
        self.score = 0
        self.paused = False
        
        self.confirmation_active = None
        self.current_color = RED
        self.targets.empty()
        self.game_over = False
        self.start_time = pygame.time.get_ticks()
        pygame.time.set_timer(SPAWN_TARGET_EVENT, 0)
        self.combo_counter = 0
        self.combo_timer = 0
        self.last_game_mode = 'PLAYING'
        self.max_combo_time = 180

    def start_game(self, mode):
        self.reset()
        self.state = mode
        self.start_time = pygame.time.get_ticks()
        pygame.time.set_timer(SPAWN_TARGET_EVENT, 2000, loops=1)
        pygame.mouse.set_visible(False)

    def spawn_target(self):
        valid_faces = [face for face in loaded_custom_faces if face is not None]
        face = random.choice(valid_faces) if valid_faces else None
        speed_mult = self.speed_multipliers[self.speed_setting]
        self.targets.add(Target(silhouette_img, target_img, face, speed_mult))
        delay = random.randint(1500, 3000)
        pygame.time.set_timer(SPAWN_TARGET_EVENT, delay, loops=1)

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    save_config()
                    self.running = False
                if event.type == SPAWN_TARGET_EVENT and not self.paused and not self.game_over:
                    self.spawn_target()

            if self.state in ['PLAYING', 'TIMED_CHALLENGE']:
                self.handle_gameplay(events)
                self.update_gameplay()
                self.draw_gameplay()
            elif self.state == 'MENU':
                self.handle_menu(events); self.draw_menu()
            elif self.state == 'SETTINGS':
                self.handle_settings(events); self.draw_settings()
            elif self.state == 'TIMED_CHALLENGE_SETUP':
                self.handle_timed_challenge_setup(events); self.draw_timed_challenge_setup()
            elif self.state == 'CUSTOM_FACES':
                self.handle_custom_faces(events); self.draw_custom_faces()
            elif self.state == 'HIGH_SCORES':
                self.handle_high_scores(events); self.draw_high_scores()
            elif self.state == 'ABOUT':
                self.handle_about(events); self.draw_about()
            elif self.state == 'FILE_EXPLORER':
                self.handle_file_explorer(events); self.draw_file_explorer()
            elif self.state == 'GAME_OVER' or self.state == 'SAVE_AND_QUIT':
                self.handle_game_over(events); self.draw_game_over()
            
            if self.error_timer > 0:
                self.error_timer -= 1
                if self.error_timer == 0:
                    self.error_message = None

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def handle_menu(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.buttons['classic'].collidepoint(event.pos): self.start_game('PLAYING')
                if self.buttons['timed'].collidepoint(event.pos): self.state = 'TIMED_CHALLENGE_SETUP'; self.input_box_active = 'timer'
                if self.buttons['scores'].collidepoint(event.pos): self.state = 'HIGH_SCORES'
                if self.buttons['settings'].collidepoint(event.pos): self.state = 'SETTINGS'
                if self.buttons['about'].collidepoint(event.pos): self.state = 'ABOUT'
                if self.buttons['quit'].collidepoint(event.pos): save_config(); self.running = False

    def draw_menu(self):
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((20, 20, 20))
        screen.blit(overlay, (0, 0))
        title = font_large.render("Paint (H)it", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH/2, 150))
        screen.blit(title, title_rect)
        draw_button("Classic Mode", self.buttons['classic'])
        draw_button("Timed Challenge", self.buttons['timed'])
        draw_button("High Scores", self.buttons['scores'])
        draw_button("Settings", self.buttons['settings'])
        draw_button("About", self.buttons['about'])
        draw_button("Quit", self.buttons['quit'])
        self.draw_error_overlay()

    def handle_gameplay(self, events):
        for event in events:
            # --- Handle Mouse Clicks (Shooting) ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.paused and not self.game_over:
                pos = pygame.mouse.get_pos()
                shot_hit = False
                for target in sorted(self.targets.sprites(), key=lambda t: t.y, reverse=True):
                    body_score = target.score_body(pos)
                    if body_score == 10:
                        shot_hit = True
                        self.combo_counter += 1
                        self.combo_timer = self.max_combo_time
                        combo_bonus = self.combo_counter * 10
                        self.score += body_score + combo_bonus
                        target.add_splat(pos, self.current_color)
                        target.fall()
                        break
                    elif body_score > 0:
                        shot_hit = True
                        self.combo_counter = 0
                        self.score += body_score
                        target.add_splat(pos, self.current_color)
                        if body_score >= 8:
                            target.fall()
                        break
                    elif target.is_face_hit(pos):
                        shot_hit = True
                        self.combo_counter = 0
                        self.score += 5
                        target.add_splat(pos, self.current_color)
                        target.fall()
                        break
                if not shot_hit:
                    self.combo_counter = 0

            # --- Handle Keyboard Presses ---
            if event.type == pygame.KEYDOWN:
                # If a confirmation dialog is active, only listen for Y/N
                if self.confirmation_active is not None:
                    if event.key == pygame.K_y:
                        if self.confirmation_active == 'restart':
                            self.start_game(self.state) # Restart current mode
                        elif self.confirmation_active == 'quit':
                            self.game_over = True
                            self.state = 'GAME_OVER'
                            self.last_state = 'quit' # Go to score screen
                    elif event.key == pygame.K_n or event.key == pygame.K_p:
                        # Cancel confirmation and unpause
                        self.paused = False
                        self.confirmation_active = None
                        # Restart the spawn timer when unpausing from a confirmation.
                        pygame.time.set_timer(SPAWN_TARGET_EVENT, 2000, loops=1)
                    continue # Skip other key checks

                # If no confirmation is active, handle normal game keys
                if not self.game_over:
                    # The Pause key toggles the paused state
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                        # If we just unpaused, restart the spawn timer.
                        if not self.paused:
                            pygame.time.set_timer(SPAWN_TARGET_EVENT, 2000, loops=1)

                    # Other actions only work if the game is not paused
                    if not self.paused:
                        if event.key == pygame.K_r:
                            self.paused = True
                            self.confirmation_active = 'restart'
                        elif event.key == pygame.K_q:
                            self.paused = True
                            self.confirmation_active = 'quit'
                        elif event.key == pygame.K_1: self.current_color = RED
                        elif event.key == pygame.K_2: self.current_color = GREEN
                        elif event.key == pygame.K_3: self.current_color = BLUE
                        elif event.key == pygame.K_4: self.current_color = YELLOW


    def handle_game_over(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.buttons['skip_score'].collidepoint(event.pos):
                    self.state = 'MENU'
                    self.reset()
                    return
            
            if event.type == pygame.KEYDOWN:
                if self.input_box_active == 'name_input':
                    if event.key == pygame.K_RETURN:
                        if self.player_name.strip():
                            self.high_scores = add_high_score(self.player_name, self.score, self.high_scores)
                            save_high_scores(self.high_scores)
                            self.input_box_active = None
                            self.state = 'HIGH_SCORES'
                    elif event.key == pygame.K_BACKSPACE: 
                        self.player_name = self.player_name[:-1]
                    elif len(self.player_name) < 15 and (event.unicode.isalnum() or event.unicode == ' '):
                        self.player_name += event.unicode
                
                else:
                    if event.key == pygame.K_r: self.start_game(self.last_game_mode)
                    if event.key == pygame.K_m: self.state = 'MENU'

    def update_gameplay(self):
        if self.paused or self.game_over: return
        
        if self.flash_timer > 0:
            self.flash_timer -= 1
        
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo_counter = 0
        
        self.player_group.update()
        self.targets.update()

        if self.state == 'TIMED_CHALLENGE':
            elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
            if elapsed >= self.challenge_duration:
                self.last_game_mode = self.state
                self.game_over = True
                self.state = 'GAME_OVER'
                self.last_state = 'timed'

    def draw_gameplay(self):
        screen.blit(background_img, (0, 0))
        for target in sorted(self.targets.sprites(), key=lambda t: t.y):
            screen.blit(target.image, target.rect)
            
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(topleft=(10, 10))
        bg_rect = score_rect.inflate(20, 10)
        pygame.draw.rect(screen, (20, 20, 20, 200), bg_rect, border_radius=8)
        screen.blit(score_text, score_rect)

        if self.combo_counter > 1:
            scale = 1 + 0.1 * (self.combo_timer / self.max_combo_time)
            scaled_font_size = int(50 * scale)
            if scaled_font_size > 0:
                combo_font = pygame.font.Font(None, scaled_font_size)
                combo_text = combo_font.render(f"x{self.combo_counter} Combo!", True, YELLOW)
                combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
                bg_rect = combo_rect.inflate(20, 10)
                pygame.draw.rect(screen, (20, 20, 20, 200), bg_rect, border_radius=8)
                screen.blit(combo_text, combo_rect)     
                
        if self.state == 'PLAYING':
            lives_text = font.render(f"Lives: {self.lives}", True, WHITE)
            lives_rect = lives_text.get_rect(topright=(SCREEN_WIDTH - 20, 10))
            bg_rect = lives_rect.inflate(20, 10)
            pygame.draw.rect(screen, (20, 20, 20, 200), bg_rect, border_radius=8)
            screen.blit(lives_text, lives_rect)
        elif self.state == 'TIMED_CHALLENGE':
            elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
            time_left = max(0, self.challenge_duration - elapsed)
            timer_text = font.render(f"Time: {int(time_left)}s", True, WHITE)
            timer_rect = timer_text.get_rect(topright=(SCREEN_WIDTH - 20, 10))
            bg_rect = timer_rect.inflate(20, 10)
            pygame.draw.rect(screen, (20, 20, 20, 200), bg_rect, border_radius=8)
            screen.blit(timer_text, timer_rect)

        for i, color in enumerate([RED, GREEN, BLUE, YELLOW]):
            rect = pygame.Rect(10 + i * 50, 60, 40, 40)
            pygame.draw.rect(screen, (20, 20, 20, 200), rect.inflate(10, 10), border_radius=6)
            pygame.draw.rect(screen, color, rect)
            if color == self.current_color:
                pygame.draw.rect(screen, WHITE, rect, 2)

        if not self.game_over: self.player_group.draw(screen)
        
        if self.paused and not self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            if self.confirmation_active is not None:
                if self.confirmation_active == 'restart':
                    title = font_large.render("Restart Game?", True, YELLOW)
                    prompt = font_medium.render("Y / N", True, TEXT_COLOR)
                else:
                    title = font_large.render("Quit Game?", True, YELLOW)
                    prompt = font_medium.render("Y (Save & Quit) / N (Continue)", True, TEXT_COLOR)
                
                screen.blit(title, (SCREEN_WIDTH/2 - title.get_width()/2, 300))
                screen.blit(prompt, (SCREEN_WIDTH/2 - prompt.get_width()/2, 400))
            else:
                pause_text = font_large.render("PAUSED", True, YELLOW)
                screen.blit(pause_text, (SCREEN_WIDTH/2 - pause_text.get_width()/2, SCREEN_HEIGHT/2 - 50))
        
        if self.flash_timer > 0:
            screen.blit(self.flash_surface, (0, 0))
            
        if not self.paused and not self.game_over:
            pygame.mouse.set_visible(False)
            mouse_pos = pygame.mouse.get_pos()
            pygame.draw.line(screen, WHITE, (mouse_pos[0]-10, mouse_pos[1]), (mouse_pos[0]+10, mouse_pos[1]), 2)
            pygame.draw.line(screen, WHITE, (mouse_pos[0], mouse_pos[1]-10), (mouse_pos[0], mouse_pos[1]+10), 2)
        elif self.paused and not self.game_over:
             pygame.mouse.set_visible(True)

    def handle_timed_challenge_setup(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    try: 
                        self.challenge_duration = int(self.challenge_duration_str)
                        game_settings['challenge_duration'] = self.challenge_duration_str
                        save_config()
                    except ValueError: 
                        self.challenge_duration = 60
                    self.start_game('TIMED_CHALLENGE')
                elif event.key == pygame.K_BACKSPACE: self.challenge_duration_str = self.challenge_duration_str[:-1]
                elif event.unicode.isdigit(): self.challenge_duration_str += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.buttons['back_timed_setup'].collidepoint(event.pos): self.state = 'MENU'

    def draw_timed_challenge_setup(self):
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((20, 20, 20))
        screen.blit(overlay, (0, 0))
        title = font_large.render("Timed Challenge Setup", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH/2 - title.get_width()/2, 180))
        timer_title = font_medium.render("Enter Time (seconds)", True, TEXT_COLOR)
        screen.blit(timer_title, (SCREEN_WIDTH/2 - timer_title.get_width()/2, 260))
        draw_input_box(self.challenge_duration_str, SCREEN_WIDTH/2 - 150, 320, 300, 50)
        start_prompt = font.render("Press ENTER to start", True, GREEN)
        screen.blit(start_prompt, (SCREEN_WIDTH/2 - start_prompt.get_width()/2, 400))
        draw_button("Back to Menu", self.buttons['back_timed_setup'])

    def handle_settings(self, events):
        global game_settings
        pygame.mouse.set_visible(True)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.buttons['easy'].collidepoint(event.pos): self.speed_setting = 'Easy'; game_settings['speed_setting'] = 'Easy'; save_config()
                if self.buttons['normal'].collidepoint(event.pos): self.speed_setting = 'Normal'; game_settings['speed_setting'] = 'Normal'; save_config()
                if self.buttons['hard'].collidepoint(event.pos): self.speed_setting = 'Hard'; game_settings['speed_setting'] = 'Hard'; save_config()
                if self.buttons['faces'].collidepoint(event.pos):
                    self.state = 'CUSTOM_FACES'
                if self.buttons['background'].collidepoint(event.pos):
                    self.state = 'FILE_EXPLORER'
                    self.file_explorer_mode = 'background'
                    self.file_explorer_path = self.last_path
                if self.buttons['back_settings'].collidepoint(event.pos): self.state = 'MENU'

    def draw_settings(self):
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((20, 20, 20))
        screen.blit(overlay, (0, 0))
        title = font_large.render("Settings", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH/2 - title.get_width()/2, 120))
        speed_title = font_medium.render("Target Speed", True, GREEN)
        screen.blit(speed_title, (SCREEN_WIDTH/2 - speed_title.get_width()/2, 220))
        draw_button("Easy", self.buttons['easy'], highlight=self.speed_setting == 'Easy')
        draw_button("Normal", self.buttons['normal'], highlight=self.speed_setting == 'Normal')
        draw_button("Hard", self.buttons['hard'], highlight=self.speed_setting == 'Hard')
        draw_button("Faces", self.buttons['faces'])
        draw_button("Background", self.buttons['background'])
        draw_button("Back to Menu", self.buttons['back_settings'])
        self.draw_error_overlay()

    def handle_custom_faces(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.buttons['back_faces'].collidepoint(event.pos):
                    self.state = 'SETTINGS'
                for i, rect in enumerate(self.face_upload_rects):
                    if rect.collidepoint(event.pos):
                        self.state = 'FILE_EXPLORER'
                        self.file_explorer_mode = 'faces'
                        self.file_explorer_path = self.last_path
                        self.face_slot_to_edit = i
                        self.scroll_offset = 0
                        break

    def draw_custom_faces(self):
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((20, 20, 20))
        screen.blit(overlay, (0, 0))
        title = font_large.render("Custom Faces", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH/2 - title.get_width()/2, 100))
        info_text = font.render("Click any slot to upload or change an image.", True, TEXT_COLOR)
        screen.blit(info_text, (SCREEN_WIDTH/2 - info_text.get_width()/2, 180))
        for i, frame_rect in enumerate(self.face_upload_rects):
            pygame.draw.rect(screen, BUTTON_COLOR, frame_rect, border_radius=15)
            pygame.draw.rect(screen, HIGHLIGHT_COLOR, frame_rect, border_radius=15, width=3)
            face_img = loaded_custom_faces[i]
            if face_img:
                face_img_scaled = pygame.transform.scale(face_img, (150, 150))
                screen.blit(face_img_scaled, face_img_scaled.get_rect(center=frame_rect.center))
            else:
                qm_img = pygame.transform.scale(question_mark_img, (100, 100))
                screen.blit(qm_img, qm_img.get_rect(center=frame_rect.center))
        draw_button("Back to Settings", self.buttons['back_faces'])

    def draw_error_overlay(self):
        if self.error_message:
            error_font = pygame.font.Font(None, 60)
            text_surface = error_font.render(self.error_message, True, WHITE)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 60))
            bg_rect = text_rect.inflate(40, 20)
            pygame.draw.rect(screen, (200, 0, 0), bg_rect, border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), bg_rect, 3, border_radius=10)
            screen.blit(text_surface, text_rect)

    def handle_file_explorer(self, events):
        global custom_faces_paths, loaded_custom_faces, custom_background_path, background_img, game_settings
        pygame.mouse.set_visible(True)
        file_list_rect = pygame.Rect(50, 180, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 320)
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.buttons['back_file_explorer'].collidepoint(event.pos):
                    if self.file_explorer_mode == 'faces':
                        self.state = 'CUSTOM_FACES'
                    elif self.file_explorer_mode == 'background':
                        self.state = 'SETTINGS'
                    self.face_slot_to_edit = None
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and file_list_rect.collidepoint(event.pos):
                try:
                    items = sorted(os.listdir(self.file_explorer_path), 
                                   key=lambda s: os.path.isdir(os.path.join(self.file_explorer_path, s)), 
                                   reverse=True)
                    if self.file_explorer_path != os.path.abspath(os.sep):
                        items.insert(0, ".. (Back)")
                except OSError as e:
                    self.error_message = f"Cannot access directory: {e.strerror}"
                    self.error_timer = 180
                    items = []

                clicked_index = int((event.pos[1] - file_list_rect.y + self.scroll_offset) / 50)

                if 0 <= clicked_index < len(items):
                    item_name = items[clicked_index]
                    
                    if item_name == ".. (Back)":
                        self.file_explorer_path = os.path.abspath(os.path.join(self.file_explorer_path, os.pardir))
                        self.scroll_offset = 0
                        game_settings['last_path'] = self.file_explorer_path
                        save_config()
                        break

                    full_path = os.path.join(self.file_explorer_path, item_name)

                    if os.path.isdir(full_path):
                        self.file_explorer_path = full_path
                        self.scroll_offset = 0
                        game_settings['last_path'] = self.file_explorer_path
                        save_config()
                    
                    elif os.path.isfile(full_path):
                        if not is_valid_image(full_path):
                            self.error_message = "Invalid file! Use .png, .jpg, .jpeg"
                            self.error_timer = 180
                            break

                        try:
                            if self.file_explorer_mode == 'background':
                                new_bg = pygame.image.load(full_path).convert()
                                background_img = pygame.transform.scale(new_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
                                custom_background_path = full_path
                                self.state = 'SETTINGS'
                            
                            elif self.file_explorer_mode == 'faces' and self.face_slot_to_edit is not None:
                                new_face = pygame.image.load(full_path).convert_alpha()
                                slot_index = self.face_slot_to_edit
                                loaded_custom_faces[slot_index] = new_face
                                custom_faces_paths[slot_index] = full_path
                                self.state = 'CUSTOM_FACES'
                                self.face_slot_to_edit = None
                            
                            self.last_path = os.path.dirname(full_path)
                            game_settings['last_path'] = self.last_path
                            save_config()

                        except pygame.error as e:
                            self.error_message = "Could not load image!"
                            self.error_timer = 180
                            print(f"Error loading image '{full_path}': {e}")
                        break
            
            if event.type == pygame.MOUSEWHEEL:
                self.scroll_offset -= event.y * 20
                try:
                    num_items = len(os.listdir(self.file_explorer_path))
                    if self.file_explorer_path != os.path.abspath(os.sep):
                        num_items += 1
                except OSError:
                    num_items = 0
                
                max_scroll = max(0, num_items * 50 - file_list_rect.height)
                self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def draw_file_explorer(self):
        screen.blit(background_img, (0, 0))
        active_tooltip_info = None
        header_box = pygame.Surface((SCREEN_WIDTH - 100, 140), pygame.SRCALPHA)
        header_box.fill((0, 0, 0, 180))
        screen.blit(header_box, (50, 30))
        title = font_large.render("File Explorer", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 60))
        screen.blit(title, title_rect)

        def truncate_text(text, max_width, font):
            if font.size(text)[0] <= max_width:
                return text
            while font.size(text + "...")[0] > max_width and len(text) > 0:
                text = text[:-1]
            return text + "..."

        max_text_width = SCREEN_WIDTH - 120
        full_current_path = f"Current Path: {self.file_explorer_path}"
        truncated_current_path = truncate_text(full_current_path, max_text_width, font)
        path_text = font.render(truncated_current_path, True, TEXT_COLOR)
        path_rect = path_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(path_text, path_rect)
        if truncated_current_path.endswith("...") and path_rect.collidepoint(pygame.mouse.get_pos()):
            tooltip_rect = font_small.render(full_current_path, True, GREY).get_rect(center=(SCREEN_WIDTH // 2, path_rect.bottom + 20))
            active_tooltip_info = (full_current_path, tooltip_rect)

        if custom_background_path:
            full_bg_path = f"Background: {custom_background_path}"
            truncated_bg_path = truncate_text(full_bg_path, max_text_width, font_small)
            bg_path_text = font_small.render(truncated_bg_path, True, GREEN)
            bg_path_rect = bg_path_text.get_rect(center=(SCREEN_WIDTH // 2, 130))
            screen.blit(bg_path_text, bg_path_rect)
            if truncated_bg_path.endswith("...") and bg_path_rect.collidepoint(pygame.mouse.get_pos()):
                tooltip_rect = font_small.render(full_bg_path, True, GREY).get_rect(center=(SCREEN_WIDTH // 2, bg_path_rect.bottom + 20))
                active_tooltip_info = (full_bg_path, tooltip_rect)

        file_list_rect = pygame.Rect(50, 180, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 320)
        pygame.draw.rect(screen, BUTTON_COLOR, file_list_rect, border_radius=10)

        try:
            items = sorted(os.listdir(self.file_explorer_path), key=lambda s: os.path.isdir(os.path.join(self.file_explorer_path, s)), reverse=True)
            if self.file_explorer_path != os.path.abspath(os.sep):
                items.insert(0, ".. (Back)")
        except OSError:
            items = []

        content_height = len(items) * 50
        max_scroll = max(0, content_height - file_list_rect.height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
        file_list_surface = pygame.Surface((file_list_rect.width, file_list_rect.height), pygame.SRCALPHA)
        file_list_surface.fill(BUTTON_COLOR)

        for i, item in enumerate(items):
            item_y_pos = i * 50 - self.scroll_offset
            if -50 < item_y_pos < file_list_rect.height:
                is_dir = os.path.isdir(os.path.join(self.file_explorer_path, item.replace(".. (Back)", os.pardir)))
                color = HIGHLIGHT_COLOR if is_dir or item.startswith("..") else TEXT_COLOR
                truncated_item = truncate_text(item, file_list_rect.width - 20, font)
                item_text = font.render(truncated_item, True, color)
                item_rect_on_surface = item_text.get_rect(topleft=(5, item_y_pos + 5))
                mouse_pos_rel = (pygame.mouse.get_pos()[0] - file_list_rect.x, pygame.mouse.get_pos()[1] - file_list_rect.y)
                if item_rect_on_surface.inflate(10,10).collidepoint(mouse_pos_rel):
                    pygame.draw.rect(file_list_surface, HOVER_COLOR, (0, item_y_pos, file_list_rect.width, 50), border_radius=5)
                    if truncated_item.endswith("..."):
                        tooltip_rect = font_small.render(item, True, GREY).get_rect(midleft=(pygame.mouse.get_pos()[0] + 15, pygame.mouse.get_pos()[1]))
                        active_tooltip_info = (item, tooltip_rect)
                file_list_surface.blit(item_text, item_rect_on_surface)

        screen.blit(file_list_surface, file_list_rect.topleft)
        draw_button("Back", self.buttons['back_file_explorer'])
        
        if active_tooltip_info:
            text, rect = active_tooltip_info
            tooltip_surf = font_small.render(text, True, WHITE)
            bg_rect = rect.inflate(20, 10)
            pygame.draw.rect(screen, (0, 0, 0, 220), bg_rect, border_radius=8)
            screen.blit(tooltip_surf, rect)

    def handle_high_scores(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.state = 'MENU'
            if event.type == pygame.MOUSEBUTTONDOWN and self.buttons['back_scores'].collidepoint(event.pos): self.state = 'MENU'

    def draw_high_scores(self):
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((20, 20, 20))
        screen.blit(overlay, (0, 0))
        title = font_large.render("Top 10 High Scores", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH/2 - title.get_width()/2, 50))
        if not self.high_scores:
            no_scores = font_medium.render("No scores yet!", True, TEXT_COLOR)
            no_scores_rect = no_scores.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(no_scores, no_scores_rect)
        else:
            row_height = 50
            table_height = (len(self.high_scores) + 1) * row_height
            start_y = (SCREEN_HEIGHT - table_height) // 2
            col_spacing_name = 80
            col_spacing_score = 150
            rank_width = max(font_medium.size(f"{i+1}.")[0] for i in range(len(self.high_scores)))
            name_width = max(font_medium.size(entry['name'])[0] for entry in self.high_scores)
            score_width = max(font_medium.size(str(entry['score']))[0] for entry in self.high_scores)
            total_width = rank_width + col_spacing_name + name_width + col_spacing_score + score_width
            start_x = (SCREEN_WIDTH - total_width) // 2
            header_rank = font_medium.render("Rank", True, GREEN)
            header_name = font_medium.render("Name", True, GREEN)
            header_score = font_medium.render("Score", True, GREEN)
            screen.blit(header_rank, (start_x + (rank_width - header_rank.get_width()), start_y))
            screen.blit(header_name, (start_x + rank_width + col_spacing_name, start_y))
            screen.blit(header_score, (start_x + rank_width + col_spacing_name + name_width + col_spacing_score + (score_width - header_score.get_width()), start_y))
            for i, entry in enumerate(self.high_scores):
                rank_text = f"{i+1}."
                name_text, score_text = entry['name'], str(entry['score'])
                rank = font_medium.render(rank_text, True, HIGHLIGHT_COLOR)
                name = font_medium.render(name_text, True, TEXT_COLOR)
                score = font_medium.render(score_text, True, TEXT_COLOR)
                y = start_y + (i+1) * row_height
                screen.blit(rank, (start_x + (rank_width - rank.get_width()), y))
                screen.blit(name, (start_x + rank_width + col_spacing_name, y))
                screen.blit(score, (start_x + rank_width + col_spacing_name + name_width + col_spacing_score + (score_width - score.get_width()), y))
        draw_button("Back to Menu", self.buttons['back_scores'])
        self.draw_error_overlay()

    def handle_about(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if hasattr(self, "author_rect") and self.author_rect.collidepoint(event.pos):
                    webbrowser.open(self.author_url)
                if self.buttons['back_about'].collidepoint(event.pos):
                    self.state = 'MENU'

    def draw_about(self):
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((20, 20, 20))
        screen.blit(overlay, (0, 0))
        title = font_large.render("Paint (H)it", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH/2 - title.get_width()/2, 100))
        info_lines = [
            f"Version: v{__version__}",
            "",
            "A fun and simple target shooting game.",
            "Hit the bullseye for a combo streak!",
            "Customize faces and backgrounds to your liking."
        ]
        y_offset = 180
        author_text = font.render(f"Author: {__author__}", True, HIGHLIGHT_COLOR)
        author_rect = author_text.get_rect(centerx=SCREEN_WIDTH//2, top=y_offset)
        screen.blit(author_text, author_rect)
        self.author_rect = author_rect
        y_offset += 40

        for line in info_lines:
            text_surf = font.render(line, True, GREEN)
            text_rect = text_surf.get_rect(centerx=SCREEN_WIDTH/2, top=y_offset)
            screen.blit(text_surf, text_rect)
            y_offset += 40

        draw_button("Back to Menu", self.buttons['back_about'])

    def draw_game_over(self):
        screen.blit(background_img, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((20, 20, 20))
        screen.blit(overlay, (0, 0))
        
        is_high_score = check_for_high_score(self.score, self.high_scores)
        
        if self.last_state == 'quit':
             title = font_large.render("Save Your Score?", True, YELLOW)
        else:
             title = font_large.render("GAME OVER", True, RED)

        screen.blit(title, (SCREEN_WIDTH/2 - title.get_width()/2, 200))
        
        if is_high_score:
            self.input_box_active = 'name_input'
            hs_text = font_medium.render("New High Score!", True, YELLOW)
            screen.blit(hs_text, (SCREEN_WIDTH/2 - hs_text.get_width()/2, 300))
            draw_input_box(self.player_name, 300, 380, 400, 50, "Enter Name...")
            prompt = font.render("Press ENTER to save", True, TEXT_COLOR)
            screen.blit(prompt, (SCREEN_WIDTH/2 - prompt.get_width()/2, 450))
            draw_button("Skip", self.buttons['skip_score'])
        else:
            final_score = font_medium.render(f"Final Score: {self.score}", True, TEXT_COLOR)
            screen.blit(final_score, (SCREEN_WIDTH/2 - final_score.get_width()/2, 350))
            
            if self.last_state == 'quit':
                prompt = font.render("Your score wasn't a high score.", True, TEXT_COLOR)
                screen.blit(prompt, (SCREEN_WIDTH/2 - prompt.get_width()/2, 400))
                back_to_menu = font.render("Press 'M' to go to menu", True, GREEN)
                screen.blit(back_to_menu, (SCREEN_WIDTH/2 - back_to_menu.get_width()/2, 450))
            else:
                prompt = font.render("Press 'R' to Restart or 'M' for Menu", True, TEXT_COLOR)
                screen.blit(prompt, (SCREEN_WIDTH/2 - prompt.get_width()/2, 450))

# --- UI Drawing Helper Functions ---
def draw_button(text, rect, highlight=False):
    mouse_pos = pygame.mouse.get_pos()
    color = HOVER_COLOR if rect.collidepoint(mouse_pos) else BUTTON_COLOR
    if highlight: color = HIGHLIGHT_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=10)
    shadow_rect = rect.copy(); shadow_rect.move_ip(5, 5)
    pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=10)
    text_surf = font_medium.render(text, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)

def draw_input_box(text, x, y, w, h, placeholder=""):
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, BUTTON_COLOR, rect, border_radius=10)
    pygame.draw.rect(screen, HIGHLIGHT_COLOR, rect, 2, border_radius=10)
    if text:
        text_surf = font_medium.render(text, True, TEXT_COLOR)
        screen.blit(text_surf, (rect.x + 10, rect.y + 5))
    elif placeholder:
        place_surf = font_medium.render(placeholder, True, GREY)
        screen.blit(place_surf, (rect.x + 10, rect.y + 5))

# --- Main Execution ---
if __name__ == '__main__':
    SPAWN_TARGET_EVENT = pygame.USEREVENT + 1
    game = Game()
    game.run()