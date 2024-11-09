import pygame
import sys
import os
from enum import Enum, auto
from pathlib import Path
import time
import math
import random
from typing import List, Tuple

# Game Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CARD_WIDTH = 120
CARD_HEIGHT = 160
CARD_MARGIN = 20
FONT_SIZE = 32

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 100, 0)

# Asset paths configuration
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(GAME_DIR, "assets")
CARDS_DIR = os.path.join(GAME_DIR, "front_cards")
BACKGROUND_PATH = os.path.join(GAME_DIR, "background_ifugao.png")
MUSIC_PATH = os.path.join(GAME_DIR, "background_music.wav")
CARD_BACK_PATH = os.path.join(GAME_DIR, "card_back.png")

# Sound effects paths
CLICK_SOUND_PATH = os.path.join(GAME_DIR, "click.wav")
MATCH_SOUND_PATH = os.path.join(GAME_DIR, "bamboo_clap.wav")
WRONG_SOUND_PATH = os.path.join(GAME_DIR, "wrong_bamboo_clap.wav")

class SceneState(Enum):
    FADE_IN = auto()
    DISPLAY = auto()
    FADE_OUT = auto()

class Scene:
    def __init__(self, image_path: str, text: str, font: pygame.font.Font, 
                 sound_path: str = None, is_first_scene: bool = False, 
                 is_final_scene: bool = False):
        # Visual elements
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (1280, 720))
        self.text = text
        self.font = font
        
        # State management
        self.state = SceneState.FADE_IN
        self.alpha = 0
        self.text_alpha = 0
        self.fade_speed = 7
        self.textbox_height = 180
        self.is_first_scene = is_first_scene
        self.is_final_scene = is_final_scene
        self.space_pressed = False
        
        # Important flags for state tracking
        self.transition_complete = False
        self.typewriter_complete = False
        self.ready_for_next = False
        
        # Text transition properties
        self.next_text = None
        self.final_text_shown = False
        self.time_active = 0
        
        # Typewriter effect properties
        self.current_text = ""
        self.text_counter = 0
        self.char_delay = 10
        self.original_char_delay = 10
        self.last_char_time = 0
        
        # Space prompt properties
        self.space_prompt_alpha = 0
        self.space_prompt_visible = True
        
        # Audio properties
        self.sound = None
        if sound_path:
            try:
                self.sound = pygame.mixer.Sound(sound_path)
                self.sound.set_volume(0.0)
            except Exception as e:
                print(f"Warning: Could not load sound {sound_path}: {e}")
        self.current_volume = 0.0
        self.target_volume = 0.7
        self.volume_fade_speed = 0.06
        
        # Typewriter sound
        self.typewriter_sound = None
        try:
            self.typewriter_sound = pygame.mixer.Sound("audio/typewriter.wav")
            self.typewriter_sound.set_volume(0.5)
        except Exception as e:
            print(f"Warning: Could not load typewriter sound: {e}")

    # Game Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CARD_WIDTH = 120
CARD_HEIGHT = 160
CARD_MARGIN = 20
FONT_SIZE = 32

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 100, 0)

# Asset paths configuration
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(GAME_DIR, "assets")
CARDS_DIR = os.path.join(GAME_DIR, "front_cards")
BACKGROUND_PATH = os.path.join(GAME_DIR, "background_ifugao.png")
MUSIC_PATH = os.path.join(GAME_DIR, "background_music.wav")
CARD_BACK_PATH = os.path.join(GAME_DIR, "card_back.png")

# Sound effects paths
CLICK_SOUND_PATH = os.path.join(GAME_DIR, "click.wav")
MATCH_SOUND_PATH = os.path.join(GAME_DIR, "bamboo_clap.wav")
WRONG_SOUND_PATH = os.path.join(GAME_DIR, "wrong_bamboo_clap.wav")

class SceneState(Enum):
    FADE_IN = auto()
    DISPLAY = auto()
    FADE_OUT = auto()

class Scene:
    def __init__(self, image_path: str, text: str, font: pygame.font.Font, 
                 sound_path: str = None, is_first_scene: bool = False, 
                 is_final_scene: bool = False):
        # Visual elements
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (1280, 720))
        self.text = text
        self.font = font
        
        # State management
        self.state = SceneState.FADE_IN
        self.alpha = 0
        self.text_alpha = 0
        self.fade_speed = 7
        self.textbox_height = 180
        self.is_first_scene = is_first_scene
        self.is_final_scene = is_final_scene
        self.space_pressed = False
        
        # Important flags for state tracking
        self.transition_complete = False
        self.typewriter_complete = False
        self.ready_for_next = False
        
        # Text transition properties
        self.next_text = None
        self.final_text_shown = False
        self.time_active = 0
        
        # Typewriter effect properties
        self.current_text = ""
        self.text_counter = 0
        self.char_delay = 10
        self.original_char_delay = 10
        self.last_char_time = 0
        
        # Space prompt properties
        self.space_prompt_alpha = 0
        self.space_prompt_visible = True
        
        # Audio properties
        self.sound = None
        if sound_path:
            try:
                self.sound = pygame.mixer.Sound(sound_path)
                self.sound.set_volume(0.0)
            except Exception as e:
                print(f"Warning: Could not load sound {sound_path}: {e}")
        self.current_volume = 0.0
        self.target_volume = 0.7
        self.volume_fade_speed = 0.06
        
        # Typewriter sound
        self.typewriter_sound = None
        try:
            self.typewriter_sound = pygame.mixer.Sound("audio/typewriter.wav")
            self.typewriter_sound.set_volume(0.5)
        except Exception as e:
            print(f"Warning: Could not load typewriter sound: {e}")

    def render(self, screen: pygame.Surface) -> None:
        # Render image
        image_surface = self.image.copy()
        if not self.is_final_scene:
            image_surface.set_alpha(self.alpha)
        else:
            image_surface.set_alpha(255)
        screen.blit(image_surface, (0, 0))
        
        if (self.alpha >= 255) or self.is_final_scene:
            if self.text:
                # Create textbox background
                textbox_surface = pygame.Surface((1280, self.textbox_height), pygame.SRCALPHA)
                for i in range(self.textbox_height):
                    alpha = int(120 * (1 - (i / self.textbox_height) * 0.3))
                    pygame.draw.rect(textbox_surface, (0, 0, 0, alpha), (0, i, 1280, 1))
                textbox_surface.set_alpha(self.text_alpha)
                screen.blit(textbox_surface, (0, 720 - self.textbox_height))
                
                # Render text
                display_text = self.current_text if not self.next_text else self.next_text
                wrapped_text = self.wrap_text(display_text, self.font, 1200)
                base_y_offset = 720 - self.textbox_height + 20
                
                for i, line in enumerate(wrapped_text):
                    text_surface = self.font.render(line, True, (255, 255, 255))
                    text_surface.set_alpha(self.text_alpha)
                    text_rect = text_surface.get_rect(midleft=(40, base_y_offset + (i * 22)))
                    screen.blit(text_surface, text_rect)
                
                # Render space prompt
                if self.text_alpha >= 200:  # Show prompt when text is mostly visible
                    if self.is_final_scene and self.final_text_shown:
                        prompt_text = "Press SPACE to Start Game"
                    else:
                        prompt_text = "Press SPACE to continue"
                    
                    space_text = self.font.render(prompt_text, True, (255, 255, 255))
                    float_offset = math.sin(self.time_active * 0.03) * 1.5
                    space_text.set_alpha(self.space_prompt_alpha)
                    space_rect = space_text.get_rect(center=(640, 695 + float_offset))
                    screen.blit(space_text, space_rect)

    def update(self) -> None:
        self.time_active += 1
        current_time = pygame.time.get_ticks()
        
        self._update_audio()
        self._update_scene_state(current_time)
        
        # Update space prompt alpha
        if self.text_alpha >= 200:  # Show prompt when text is mostly visible
            pulse = (math.sin(self.time_active * 0.05) + 1) * 0.5
            self.space_prompt_alpha = int(100 + (155 * pulse))

    def _update_audio(self) -> None:
        if self.sound:
            if self.state == SceneState.FADE_IN:
                if self.current_volume < self.target_volume:
                    self.current_volume = min(self.target_volume, 
                                           self.current_volume + self.volume_fade_speed)
                    self.sound.set_volume(self.current_volume)
            elif self.state == SceneState.FADE_OUT and not self.is_final_scene:
                if self.current_volume > 0:
                    self.current_volume = max(0, self.current_volume - self.volume_fade_speed)
                    self.sound.set_volume(self.current_volume)
                if self.current_volume <= 0 and self.sound.get_num_channels() > 0:
                    self.sound.stop()

    def _update_scene_state(self, current_time: int) -> None:
        if self.state == SceneState.FADE_IN:
            self._handle_fade_in(current_time)
        elif self.state == SceneState.FADE_OUT:
            self._handle_fade_out(current_time)

    def _handle_fade_in(self, current_time: int) -> None:
        if not self.is_final_scene:
            self.alpha = min(255, self.alpha + self.fade_speed)
        if self.alpha >= 255 or self.is_final_scene:
            self.text_alpha = min(255, self.text_alpha + self.fade_speed)
            if self.text_alpha >= 255:
                self._update_typewriter(current_time)
                # Make final scene more responsive
                if self.is_final_scene and self.final_text_shown:
                    self.typewriter_complete = True
                    self.ready_for_next = True

    def _handle_fade_out(self, current_time: int) -> None:
        self.text_alpha = max(0, self.text_alpha - self.fade_speed)
        if self.text_alpha <= 0:
            if self.is_final_scene and not self.final_text_shown:
                self.next_text = "On-Screen Controls: Tap or click a face-down card to flip it over. You can only flip two cards at a time. The goal is to match all the cards."
                self.text = self.next_text
                self.final_text_shown = True
                self.state = SceneState.FADE_IN
                self.current_text = ""
                self.text_counter = 0
                self.typewriter_complete = False
                self.ready_for_next = False
                self.char_delay = 50
                self.last_char_time = current_time
                # Ensure typewriter sound is off for controls text
                if self.typewriter_sound:
                    self.typewriter_sound.stop()
                    self.typewriter_sound.set_volume(0)
            else:
                self.alpha = max(0, self.alpha - self.fade_speed)
                if self.alpha <= 0:
                    self.transition_complete = True
                    # Ensure final scene is ready for transition
                    if self.is_final_scene:
                        self.typewriter_complete = True
                        self.ready_for_next = True

    def _update_typewriter(self, current_time: int) -> None:
        if not self.typewriter_complete:
            if current_time - self.last_char_time >= self.char_delay:
                target_text = self.text if not self.next_text else self.next_text
                if len(self.current_text) < len(target_text):
                    # Don't play typewriter sound for controls text
                    if not (self.is_final_scene and target_text.startswith("On-Screen Controls")):
                        if self.typewriter_sound and self.typewriter_sound.get_num_channels() == 0:
                            self.typewriter_sound.play(-1)
                    self.current_text += target_text[len(self.current_text):len(self.current_text) + 1]
                    self.last_char_time = current_time
                else:
                    self.typewriter_complete = True
                    self.ready_for_next = True
                    if self.typewriter_sound and self.typewriter_sound.get_num_channels() > 0:
                        self.typewriter_sound.stop()

    def wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list:
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            text_surface = font.render(' '.join(current_line), True, (255, 255, 255))
            
            if text_surface.get_width() > max_width:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        
        lines.append(' '.join(current_line))
        return lines

    def start_sound(self) -> None:
        if self.sound and self.sound.get_num_channels() == 0:
            self.sound.play(-1)

    def stop_sound(self) -> None:
        if self.sound and self.sound.get_num_channels() > 0:
            self.sound.stop()
        if self.typewriter_sound and self.typewriter_sound.get_num_channels() > 0:
            self.typewriter_sound.stop()

class Card:
    def __init__(self, x: int, y: int, pair_id: int, image_path: str):
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self.pair_id = pair_id
        self.is_flipped = False
        self.is_matched = False
        
        try:
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.scale(self.image, (CARD_WIDTH, CARD_HEIGHT))
        except pygame.error as e:
            print(f"Error loading card image {image_path}: {e}")
            self.image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.image.fill(WHITE)
            
        try:
            self.back = pygame.image.load(CARD_BACK_PATH)
            self.back = pygame.transform.scale(self.back, (CARD_WIDTH, CARD_HEIGHT))
        except pygame.error as e:
            print(f"Error loading card back image: {e}")
            self.back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.back.fill(GRAY)
            pygame.draw.rect(self.back, BLACK, pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT), 2)
       
    def draw(self, screen):
        if self.is_matched or self.is_flipped:
            screen.blit(self.image, self.rect)
        else:
            screen.blit(self.back, self.rect)

class Game:
    def __init__(self):
        # Use existing pygame display if available
        self.screen = pygame.display.get_surface()
        if not self.screen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Fade-in effect variables
        self.fade_alpha = 255
        self.fading_in = True
        self.fade_speed = 5
        
        # Load sound effects
        try:
            self.click_sound = pygame.mixer.Sound(CLICK_SOUND_PATH)
            self.match_sound = pygame.mixer.Sound(MATCH_SOUND_PATH)
            self.wrong_sound = pygame.mixer.Sound(WRONG_SOUND_PATH)
            
            self.click_sound.set_volume(0.4)
            self.match_sound.set_volume(0.6)
            self.wrong_sound.set_volume(0.6)
        except pygame.error as e:
            print(f"Error loading sound effects: {e}")
            class DummySound:
                def play(self): pass
                def set_volume(self, vol): pass
            self.click_sound = self.match_sound = self.wrong_sound = DummySound()
        
        # Load background
        try:
            self.background = pygame.image.load(BACKGROUND_PATH)
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error as e:
            print(f"Error loading background: {e}")
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background.fill(WHITE)
        
        # Initialize fonts
        try:
            self.font = pygame.font.Font('font/pixel_font.ttf', 24)
            self.font_large = pygame.font.Font('font/pixel_font.ttf', 32)
            self.font_small = pygame.font.Font('font/pixel_font.ttf', 20)
        except pygame.error as e:
            print(f"Error loading font: {e}")
            self.font = pygame.font.SysFont(None, 24)
            self.font_large = pygame.font.SysFont(None, 32)
            self.font_small = pygame.font.SysFont(None, 20)
        
        # Game state
        self.cards: List[Card] = []
        self.flipped_cards: List[Card] = []
        self.matches_found = 0
        self.player_won = False
        
        # Victory screen variables
        self.victory_prompt_timer = 0
        self.victory_prompt_visible = True
        self.victory_prompt_interval = 1.0
        
        # Initialize game
        self.initialize_cards()
        
        # Timer variables
        self.flip_timer = 0
        self.waiting_to_flip_back = False
        
        # Start background music with fade-in
        try:
            pygame.mixer.music.load(MUSIC_PATH)
            pygame.mixer.music.set_volume(0.0)
            pygame.mixer.music.play(-1)
            
            # Fade in music
            for vol in range(0, 31):
                pygame.mixer.music.set_volume(vol/100)
                pygame.time.delay(30)
        except pygame.error as e:
            print(f"Error loading background music: {e}")

    def find_card_files(self) -> List[Tuple[str, str]]:
        card_pairs = []
        directory = CARDS_DIR
        
        for i in range(1, 9):  # For 8 pairs
            card1 = os.path.join(directory, f"pair{i}_card1.png")
            card2 = os.path.join(directory, f"pair{i}_card2.png")
            if os.path.exists(card1) and os.path.exists(card2):
                card_pairs.append((card1, card2))
        
        if len(card_pairs) < 8:
            raise Exception(f"Not enough card images found. Found {len(card_pairs)}, need 8.")
        
        return card_pairs[:8]

    def initialize_cards(self):
        try:
            card_pairs = self.find_card_files()
            
            total_cards = 16  # 8 pairs
            cards_per_row = 4
            rows = total_cards // cards_per_row
            
            start_x = (SCREEN_WIDTH - (cards_per_row * (CARD_WIDTH + CARD_MARGIN))) // 2
            start_y = (SCREEN_HEIGHT - (rows * (CARD_HEIGHT + CARD_MARGIN))) // 2
            
            cards_to_place = []
            for pair_id, (card1_path, card2_path) in enumerate(card_pairs):
                cards_to_place.append((card1_path, pair_id))
                cards_to_place.append((card2_path, pair_id))
            
            random.shuffle(cards_to_place)
            
            self.cards = []
            for i in range(total_cards):
                row = i // cards_per_row
                col = i % cards_per_row
                x = start_x + col * (CARD_WIDTH + CARD_MARGIN)
                y = start_y + row * (CARD_HEIGHT + CARD_MARGIN)
                image_path, pair_id = cards_to_place[i]
                self.cards.append(Card(x, y, pair_id, image_path))
                
        except Exception as e:
            print(f"Error initializing cards: {e}")
            pygame.quit()
            sys.exit(1)

    def handle_click(self, pos):
        if self.waiting_to_flip_back:
            return
            
        for card in self.cards:
            if card.rect.collidepoint(pos) and not card.is_flipped and not card.is_matched:
                self.click_sound.play()
                
                if len(self.flipped_cards) < 2:
                    card.is_flipped = True
                    self.flipped_cards.append(card)
                    
                    if len(self.flipped_cards) == 2:
                        if self.flipped_cards[0].pair_id == self.flipped_cards[1].pair_id:
                            self.match_sound.play()
                            self.flipped_cards[0].is_matched = True
                            self.flipped_cards[1].is_matched = True
                            self.matches_found += 1
                            self.flipped_cards = []
                        else:
                            self.wrong_sound.play()
                            self.waiting_to_flip_back = True
                            self.flip_timer = pygame.time.get_ticks()
                break

    def update(self):
        if self.player_won:
            self.victory_prompt_timer += 1/60
            if self.victory_prompt_timer >= self.victory_prompt_interval:
                self.victory_prompt_timer = 0
                self.victory_prompt_visible = not self.victory_prompt_visible
        else:
            if self.waiting_to_flip_back and pygame.time.get_ticks() - self.flip_timer > 1000:
                for card in self.flipped_cards:
                    card.is_flipped = False
                self.flipped_cards = []
                self.waiting_to_flip_back = False
            
            # Check for victory
            if self.matches_found == 8 and not self.player_won:
                self.player_won = True

    def draw_victory_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(WHITE)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))
        
        center_y = SCREEN_HEIGHT // 2
        title_offset = 35
        
        victory_text = self.font_large.render("Congratulations!", True, DARK_GREEN)
        victory_rect = victory_text.get_rect(
            center=(SCREEN_WIDTH // 2, center_y - title_offset)
        )
        self.screen.blit(victory_text, victory_rect)
        
        subtext = self.font_small.render("You've collected all the scattered seeds!", True, DARK_GREEN)
        subtext_rect = subtext.get_rect(
            center=(SCREEN_WIDTH // 2, center_y)
        )
        self.screen.blit(subtext, subtext_rect)
        
        if self.victory_prompt_visible:
            prompt_text = self.font_small.render("Press SPACE to Access Map", True, BLACK)
            prompt_rect = prompt_text.get_rect(
                center=(SCREEN_WIDTH // 2, center_y + title_offset)
            )
            
            t = pygame.time.get_ticks()
            alpha = int(180 + 75 * math.sin(t * 0.003))
            
            prompt_surface = prompt_text.copy()
            prompt_surface.set_alpha(alpha)
            self.screen.blit(prompt_surface, prompt_rect)

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        
        for card in self.cards:
            card.draw(self.screen)
            
        if self.player_won:
            self.draw_victory_screen()
        
        if self.fading_in:
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(fade_surface, (0, 0))
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed)
            if self.fade_alpha <= 0:
                self.fading_in = False
                pygame.mixer.music.set_volume(0.3)
        
        pygame.display.flip()

    def transition_to_map(self):
        current_volume = pygame.mixer.music.get_volume()
        for vol in range(int(current_volume * 100), -1, -1):
            pygame.mixer.music.set_volume(vol/100)
            pygame.time.delay(20)
        
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        pygame.quit()
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(current_dir, 'map.py')
        
        if os.path.exists(map_path):
            python_executable = sys.executable
            try:
                os.execv(python_executable, [python_executable, map_path])
            except Exception as e:
                print(f"Error launching map: {e}")
                sys.exit(1)
        else:
            print(f"Map file not found at: {map_path}")
            sys.exit(1)

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.player_won:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.player_won:
                        self.transition_to_map()
            
            self.update()
            self.draw()
            clock.tick(60)

class OpeningSequence:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("ISLA")
        
        font_path = Path("font/pixel_font.ttf")
        self.font = pygame.font.Font(font_path, 14)
        pygame.display.set_icon(pygame.image.load("assets/first_farm.png"))
        
        self.scenes = self._initialize_scenes()
        self.current_scene = 0
        self.clock = pygame.time.Clock()
        self.transitioning = False
        self.last_space_time = 0
        self.space_cooldown = 250

    def _initialize_scenes(self) -> list:
        # [Scene initialization remains unchanged...]
        return [
            Scene("assets/first_farm.png", 
                'Welcome to Ifugao, a stunning province in the mountains of the Philippines, home to the rice terraces, one of the "Eighth Wonders of the World." Carved over 2,000 years ago by the Ifugao ancestors, these terraces are not just for farming; they represent a deep connection to the land and their culture. The Ifugao people have developed smart irrigation systems that help grow rice, which is essential to their way of life.', 
                self.font, 
                "audio/first_naturesound.wav",
                is_first_scene=True),
            
            Scene("assets/second_ritual.png", 
                "These terraces embody the Ifugao's respect for nature, each level steeped in mythology and tradition. A UNESCO World Heritage Site since 1995, they symbolize enduring cultural pride. As you explore this breathtaking landscape, immerse yourself in the vibrant heritage shaped by generations.", 
                self.font, 
                "audio/second_ritualsong.wav"),
            
            Scene("assets/third_panic.png",
                "Context and Rules: In Ifugao, the rice terraces are not just a source of sustenance but also a symbol of cultural heritage. One day, as the villagers prepare for the planting season, they discover that the precious seeds have been misplaced!",
                self.font,
                "audio/third_panicsong.wav"),
            
            Scene("assets/fourth_click.png",
                "The community is in a panic, for without these seeds, the upcoming harvest is at risk. To retrieve the scattered seeds, you will need to use your memory and skill in a card-flip matching game.",
                self.font,
                "audio/fourth_clicksound.wav",
                is_final_scene=True)
        ]

    def transition_to_game(self):
        # Fade out all sounds
        for scene in self.scenes:
            scene.stop_sound()
        
        # Fade out visual
        fade_surface = pygame.Surface((1280, 720))
        fade_surface.fill((0, 0, 0))
        
        # Smooth fade to black
        for alpha in range(0, 255, 5):
            self.screen.fill((0, 0, 0))
            self.scenes[self.current_scene].render(self.screen)
            fade_surface.set_alpha(alpha)
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            pygame.time.delay(20)
        
        # Clear events before transition
        pygame.event.clear()
        
        try:
            game = Game()
            game.run()
        except Exception as e:
            print(f"Error starting game: {e}")
            self.cleanup()
            sys.exit(1)

    def cleanup(self):
        for scene in self.scenes:
            scene.stop_sound()
        pygame.quit()
        sys.exit()

    def run(self):
        running = True
        self.scenes[0].start_sound()
        
        while running:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        current_scene = self.scenes[self.current_scene]
                        
                        # Make final scene transition more responsive
                        if current_scene.is_final_scene and current_scene.final_text_shown:
                            self.transition_to_game()
                            return
                        
                        # For other scenes, keep existing behavior
                        if current_time - self.last_space_time >= self.space_cooldown:
                            self.last_space_time = current_time
                            if not self.transitioning:
                                if current_scene.typewriter_sound and current_scene.typewriter_sound.get_num_channels() > 0:
                                    current_scene.typewriter_sound.stop()
                                current_scene.ready_for_next = True
                                current_scene.state = SceneState.FADE_OUT
                                self.transitioning = True
                                
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            self.screen.fill((0, 0, 0))
            current_scene = self.scenes[self.current_scene]
            current_scene.update()
            
            if self.transitioning and current_scene.transition_complete:
                if self.current_scene < len(self.scenes) - 1:
                    current_scene.stop_sound()
                    self.current_scene += 1
                    self.scenes[self.current_scene].start_sound()
                    self.transitioning = False
                    current_scene.transition_complete = False
            
            current_scene.render(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

        self.cleanup()

    def cleanup(self):
        for scene in self.scenes:
            scene.stop_sound()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    sequence = OpeningSequence()
    sequence.run()