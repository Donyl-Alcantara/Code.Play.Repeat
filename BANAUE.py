import pygame
import sys
import os
from enum import Enum, auto
from pathlib import Path
import time
import math
import random
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor

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
MAIN_DIR = os.path.dirname(os.path.abspath(__file__))  # Code.Play-Repeat directory
ASSETS_DIR = os.path.join(MAIN_DIR, "assets")
AUDIO_DIR = os.path.join(MAIN_DIR, "audio")
CARDS_DIR = os.path.join(ASSETS_DIR, "front_cards")  # front_cards is now inside assets
FONT_DIR = os.path.join(MAIN_DIR, "font")

# Image paths
BACKGROUND_PATH = os.path.join(ASSETS_DIR, "background_ifugao.png")
CARD_BACK_PATH = os.path.join(ASSETS_DIR, "card_back.png")
FIRST_FARM_PATH = os.path.join(ASSETS_DIR, "first_farm.png")
SECOND_RITUAL_PATH = os.path.join(ASSETS_DIR, "second_ritual.png")
THIRD_PANIC_PATH = os.path.join(ASSETS_DIR, "third_panic.png")
FOURTH_CLICK_PATH = os.path.join(ASSETS_DIR, "fourth_click.png")

# Audio paths
BACKGROUND_MUSIC_PATH = os.path.join(AUDIO_DIR, "background_music.wav")
CLICK_SOUND_PATH = os.path.join(AUDIO_DIR, "click.wav")
MATCH_SOUND_PATH = os.path.join(AUDIO_DIR, "bamboo_clap.wav")
WRONG_SOUND_PATH = os.path.join(AUDIO_DIR, "wrong_bamboo_clap.wav")
FIRST_NATURE_SOUND_PATH = os.path.join(AUDIO_DIR, "first_naturesound.wav")
SECOND_RITUAL_SOUND_PATH = os.path.join(AUDIO_DIR, "second_ritualsong.wav")
THIRD_PANIC_SOUND_PATH = os.path.join(AUDIO_DIR, "third_panicsong.wav")
FOURTH_CLICK_SOUND_PATH = os.path.join(AUDIO_DIR, "fourth_clicksound.wav")
TYPEWRITER_SOUND_PATH = os.path.join(AUDIO_DIR, "typewriter.wav")
VICTORY_SOUND_PATH = os.path.join(AUDIO_DIR, "gong.wav")

# Font path
FONT_PATH = os.path.join(FONT_DIR, "pixel_font.ttf")

class AssetLoader:
    @staticmethod
    def load_image(path):
        """Load and scale an image"""
        try:
            image = pygame.image.load(path)
            return pygame.transform.scale(image, (1280, 720))
        except Exception as e:
            print(f"Warning: Could not load image {path}: {e}")
            surface = pygame.Surface((1280, 720))
            surface.fill((128, 128, 128))
            return surface
    
    @staticmethod
    def load_sound(path):
        """Load a sound file"""
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Warning: Could not load sound {path}: {e}")
            return None

class LoadingScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.progress = 0
        self.loading_complete = False
        
        # Font setup
        try:
            self.font = pygame.font.Font(FONT_PATH, 16)
            self.small_font = pygame.font.Font(FONT_PATH, 12)
        except:
            self.font = pygame.font.SysFont(None, 16)
            self.small_font = pygame.font.SysFont(None, 12)
        
        # Color scheme
        self.border_color = (76, 63, 47)    # Dark brown
        self.fill_color = (155, 126, 89)    # Light brown
        self.bg_color = (25, 25, 25)        # Dark background
        self.text_color = (219, 202, 169)   # Cream color
        self.highlight_color = (255, 223, 186)  # Lighter cream
        
        # Loading bar configuration
        self.bar_width = 300
        self.bar_height = 20
        self.border_thickness = 4
        self.corner_radius = 10
        self.bar_x = (1280 - self.bar_width) // 2
        self.bar_y = 360
        
        # Animation properties
        self.dots = ""
        self.dot_timer = 0
        self.dot_update_rate = 20
        self.anim_counter = 0
        
        # Loading messages
        self.loading_messages = [
            ("Loading... Hold tight, kapatid!", "Parang tricycle ride—matagtag pero siguradong sulit!"),
            ("Loading... Pack your balikbayan box!", "We're collecting memories along the way!"),
            ("Loading... Ready your baon and tsinelas!", "This journey will take you places!"),
            ("Loading... Parang jeep na puno!", "Pero may sasakay pa!"),
            ("Loading... Don't forget to say para!", "Baka lumagpas ka!")
        ]
        
        # Randomly select a message
        self.selected_message = random.choice(self.loading_messages)
        
        # Text animation properties
        self.tagalog_alpha = 0
        self.tagalog_fade_in = True
        self.fade_speed = 5

    def draw_rounded_rect(self, surface, color, rect, radius):
        x, y, width, height = rect
        temp_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw main rectangle body
        pygame.draw.rect(temp_surface, color, 
                        (radius, 0, width - 2 * radius, height))
        pygame.draw.rect(temp_surface, color,
                        (0, radius, width, height - 2 * radius))
        
        # Draw rounded corners
        pygame.draw.circle(temp_surface, color, (radius, radius), radius)
        pygame.draw.circle(temp_surface, color, (width - radius, radius), radius)
        pygame.draw.circle(temp_surface, color, (radius, height - radius), radius)
        pygame.draw.circle(temp_surface, color, (width - radius, height - radius), radius)
        
        surface.blit(temp_surface, (x, y))
    
    def update(self, progress: float):
        """Update loading screen state"""
        self.progress = progress
        self.anim_counter += 1
        
        # Update loading dots animation
        if self.anim_counter % self.dot_update_rate == 0:
            if len(self.dots) < 3:
                self.dots += "."
            else:
                self.dots = ""
        
        # Update Tagalog text fade animation
        if self.tagalog_fade_in:
            self.tagalog_alpha = min(255, self.tagalog_alpha + self.fade_speed)
            if self.tagalog_alpha >= 255:
                self.tagalog_fade_in = False
        else:
            self.tagalog_alpha = max(180, self.tagalog_alpha - self.fade_speed)
            if self.tagalog_alpha <= 180:
                self.tagalog_fade_in = True
    
    def draw(self):
        """Draw the loading screen"""
        # Fill background
        self.screen.fill(self.bg_color)
        
        # Draw title
        title_text = self.font.render("ISLA", True, self.text_color)
        title_rect = title_text.get_rect(centerx=640, bottom=self.bar_y - 40)
        self.screen.blit(title_text, title_rect)
        
        # Draw loading message
        loading_text = self.small_font.render(self.selected_message[0], True, self.text_color)
        loading_rect = loading_text.get_rect(centerx=640, top=self.bar_y + 40)
        self.screen.blit(loading_text, loading_rect)
        
        # Draw Tagalog message with fade effect
        tagalog_text = self.small_font.render(self.selected_message[1], True, self.highlight_color)
        tagalog_text.set_alpha(self.tagalog_alpha)
        tagalog_rect = tagalog_text.get_rect(centerx=640, top=self.bar_y + 60)
        self.screen.blit(tagalog_text, tagalog_rect)
        
        # Draw loading bar border
        border_rect = (self.bar_x - self.border_thickness,
                      self.bar_y - self.border_thickness,
                      self.bar_width + (self.border_thickness * 2),
                      self.bar_height + (self.border_thickness * 2))
        self.draw_rounded_rect(self.screen, self.border_color, border_rect, self.corner_radius)
        
        # Draw loading bar background
        bg_rect = (self.bar_x, self.bar_y, self.bar_width, self.bar_height)
        self.draw_rounded_rect(self.screen, self.bg_color, bg_rect, self.corner_radius - self.border_thickness)
        
        # Draw progress bar
        progress_width = int(self.bar_width * self.progress)
        if progress_width > 0:
            progress_rect = (self.bar_x, self.bar_y, progress_width, self.bar_height)
            if progress_width < self.bar_width:
                self.draw_rounded_rect(self.screen, self.fill_color, progress_rect, 
                                     min(self.corner_radius - self.border_thickness, progress_width // 2))
            else:
                self.draw_rounded_rect(self.screen, self.fill_color, progress_rect, 
                                     self.corner_radius - self.border_thickness)

class SceneState(Enum):
    FADE_IN = auto()
    DISPLAY = auto()
    FADE_OUT = auto()

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
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        
        self.screen = pygame.display.get_surface()
        if not self.screen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            
        pygame.display.set_caption("BANAUE")
            
        # Fade-in effect variables
        self.fade_alpha = 255
        self.fading_in = True
        self.fade_speed = 5
        
        # Load sound effects
        try:
            self.click_sound = pygame.mixer.Sound(CLICK_SOUND_PATH)
            self.match_sound = pygame.mixer.Sound(MATCH_SOUND_PATH)
            self.wrong_sound = pygame.mixer.Sound(WRONG_SOUND_PATH)
            self.victory_sound = pygame.mixer.Sound(VICTORY_SOUND_PATH) 
            
            self.click_sound.set_volume(0.4)
            self.match_sound.set_volume(0.6)
            self.wrong_sound.set_volume(0.6)
            self.victory_sound.set_volume(1.0)  # Add this line
        except pygame.error as e:
            print(f"Error loading sound effects: {e}")
            class DummySound:
                def play(self): pass
                def set_volume(self, vol): pass
            self.click_sound = self.match_sound = self.wrong_sound = self.victory_sound = DummySound()  # Update this line
        
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
            self.font = pygame.font.Font(FONT_PATH, 24)
            self.font_large = pygame.font.Font(FONT_PATH, 32)
            self.font_small = pygame.font.Font(FONT_PATH, 20)
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

        #Victory sound flag
        self.victory_sound_played = False
        
        # Initialize game
        self.initialize_cards()
        
        # Timer variables
        self.flip_timer = 0
        self.waiting_to_flip_back = False
        
        # Start background music with fade-in
        try:
            pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
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

    def transition_to_map(self):
        # Create fade out effect
        fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fade_surface.fill((0, 0, 0))
        fade_alpha = 0
        fade_speed = 5

        # Fade out loop
        while fade_alpha < 255:
            # Handle any quit events during transition
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Draw current game state
            self.screen.blit(self.background, (0, 0))
            for card in self.cards:
                card.draw(self.screen)
            if self.player_won:
                self.draw_victory_screen()

            # Draw fade overlay
            fade_surface.set_alpha(fade_alpha)
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            
            fade_alpha += fade_speed
            pygame.time.Clock().tick(60)

        # Stop all sounds
        pygame.mixer.music.stop()
        pygame.mixer.stop()

        # Import and start map
        import map
        try:
            self.running = False
            map.main()
        except Exception as e:
            print(f"Error transitioning to map: {e}")
            self.running = False

    def update(self):
        if self.player_won:
            # Play victory sound once when victory is first achieved
            if not self.victory_sound_played:
                self.victory_sound.play()
                self.victory_sound_played = True
            
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
                        return  # Exit run loop after transition starts
            
            self.update()
            self.draw()
            clock.tick(60)

        pygame.quit()

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
            self.typewriter_sound = pygame.mixer.Sound(TYPEWRITER_SOUND_PATH)
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
                if self.typewriter_sound:
                    self.typewriter_sound.stop()
                    self.typewriter_sound.set_volume(0)
            else:
                self.alpha = max(0, self.alpha - self.fade_speed)
                if self.alpha <= 0:
                    self.transition_complete = True
                    if self.is_final_scene:
                        self.typewriter_complete = True
                        self.ready_for_next = True

    def _update_typewriter(self, current_time: int) -> None:
        if not self.typewriter_complete:
            if current_time - self.last_char_time >= self.char_delay:
                target_text = self.text if not self.next_text else self.next_text
                if len(self.current_text) < len(target_text):
                    if not (self.is_final_scene and self.final_text_shown):
                        if self.typewriter_sound and self.typewriter_sound.get_num_channels() == 0:
                            self.typewriter_sound.play(-1)
                    self.current_text += target_text[len(self.current_text)]
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

class OpeningSequence:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        
        self.screen = pygame.display.get_surface()
        if not self.screen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                
        pygame.display.set_caption("BANAUE")

        # Add clock initialization here
        self.clock = pygame.time.Clock()

        # Fade-in effect variables
        self.fade_alpha = 255
        self.fading_in = True
        self.fade_speed = 5
        
        try:
            self.font = pygame.font.Font(FONT_PATH, 14)
            pygame.display.set_icon(pygame.image.load(FIRST_FARM_PATH))
        except pygame.error as e:
            print(f"Error loading font or icon: {e}")
            self.font = pygame.font.SysFont(None, 14)
        
        self.scenes = self._initialize_scenes()
        self.current_scene = 0
        self.last_space_time = 0
        self.space_cooldown = 250
        self.transitioning = False

    def _initialize_scenes(self) -> list:
        return [
            Scene(FIRST_FARM_PATH, 
                'Welcome to Ifugao, a stunning province in the mountains of the Philippines, home to the rice terraces, one of the "Eighth Wonders of the World." Carved over 2,000 years ago by the Ifugao ancestors, these terraces are not just for farming; they represent a deep connection to the land and their culture. The Ifugao people have developed smart irrigation systems that help grow rice, which is essential to their way of life.', 
                self.font, 
                FIRST_NATURE_SOUND_PATH,
                is_first_scene=True),
            
            Scene(SECOND_RITUAL_PATH, 
                "These terraces embody the Ifugao's respect for nature, each level steeped in mythology and tradition. A UNESCO World Heritage Site since 1995, they symbolize enduring cultural pride. As you explore this breathtaking landscape, immerse yourself in the vibrant heritage shaped by generations.", 
                self.font, 
                SECOND_RITUAL_SOUND_PATH),
            
            Scene(THIRD_PANIC_PATH,
                "Context and Rules: In Ifugao, the rice terraces are not just a source of sustenance but also a symbol of cultural heritage. One day, as the villagers prepare for the planting season, they discover that the precious seeds have been misplaced!",
                self.font,
                THIRD_PANIC_SOUND_PATH),
            
            Scene(FOURTH_CLICK_PATH,
                "The community is in a panic, for without these seeds, the upcoming harvest is at risk. To retrieve the scattered seeds, you will need to use your memory and skill in a card-flip matching game.",
                self.font,
                FOURTH_CLICK_SOUND_PATH,
                is_final_scene=True)
        ]

    def transition_to_game(self):
        """Smooth transition from story to game"""
        # Create fade out effect
        fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fade_surface.fill((0, 0, 0))
        fade_alpha = 0
        fade_speed = 5

        # Fade out loop
        while fade_alpha < 255:
            # Handle any quit events during transition
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Draw current scene state
            self.screen.fill((0, 0, 0))
            self.scenes[self.current_scene].render(self.screen)

            # Draw fade overlay
            fade_surface.set_alpha(fade_alpha)
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            
            fade_alpha += fade_speed
            self.clock.tick(60)

        # Stop all sounds from story sequence
        for scene in self.scenes:
            scene.stop_sound()

        try:
            # Start game with fade in
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
                        
                        if current_scene.is_final_scene and current_scene.final_text_shown:
                            self.transition_to_game()
                            return
                        
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

def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("BANAUE")
    clock = pygame.time.Clock()
    
    # Initialize loading screen
    loading_screen = LoadingScreen(screen)
    
    # Asset loading configuration
    assets_to_load = [
        (AssetLoader.load_image, BACKGROUND_PATH),
        (AssetLoader.load_image, CARD_BACK_PATH),
        (AssetLoader.load_image, FIRST_FARM_PATH),
        (AssetLoader.load_image, SECOND_RITUAL_PATH),
        (AssetLoader.load_image, THIRD_PANIC_PATH),
        (AssetLoader.load_image, FOURTH_CLICK_PATH),
        (AssetLoader.load_sound, BACKGROUND_MUSIC_PATH),
        (AssetLoader.load_sound, CLICK_SOUND_PATH),
        (AssetLoader.load_sound, MATCH_SOUND_PATH),
        (AssetLoader.load_sound, WRONG_SOUND_PATH),
        (AssetLoader.load_sound, FIRST_NATURE_SOUND_PATH),
        (AssetLoader.load_sound, SECOND_RITUAL_SOUND_PATH),
        (AssetLoader.load_sound, THIRD_PANIC_SOUND_PATH),
        (AssetLoader.load_sound, FOURTH_CLICK_SOUND_PATH),
        (AssetLoader.load_sound, TYPEWRITER_SOUND_PATH),
    ]
    
    # Add card images to assets
    card_pairs_path = Path(CARDS_DIR)
    for i in range(1, 9):
        assets_to_load.append((AssetLoader.load_image, str(card_pairs_path / f"pair{i}_card1.png")))
        assets_to_load.append((AssetLoader.load_image, str(card_pairs_path / f"pair{i}_card2.png")))
    
    total_assets = len(assets_to_load)
    loaded_assets = 0
    chunk_size = 4  # Load assets in smaller chunks to prevent thread overload
    
    # Load assets with progress tracking
    with ThreadPoolExecutor(max_workers=4) as executor:
        for i in range(0, total_assets, chunk_size):
            chunk = assets_to_load[i:i + chunk_size]
            futures = []
            
            for loader_func, asset_path in chunk:
                future = executor.submit(loader_func, asset_path)
                futures.append(future)
            
            running = True
            while running and not all(f.done() for f in futures):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                
                completed = sum(1 for f in futures if f.done())
                current_progress = (loaded_assets + completed) / total_assets
                
                loading_screen.update(current_progress)
                loading_screen.draw()
                pygame.display.flip()
                
                pygame.time.wait(10)  # Small delay to prevent CPU overload
                clock.tick(60)
            
            if not running:
                break
                
            loaded_assets += len(chunk)
            pygame.time.wait(20)  # Brief pause between chunks
    
    if running:
        # Brief pause to ensure all resources are properly loaded
        pygame.time.wait(100)
        # Start the opening sequence
        sequence = OpeningSequence()
        sequence.run()
    else:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()