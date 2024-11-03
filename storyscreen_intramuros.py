import pygame
import sys
from enum import Enum, auto
from pathlib import Path
import time
import math
import pygame.mixer
from concurrent.futures import ThreadPoolExecutor

class SceneState(Enum):
    FADE_IN = auto()
    DISPLAY = auto()
    FADE_OUT = auto()

class LoadingScreen:
    def __init__(self, screen: pygame.Surface, font_path: str):
        self.screen = screen
        self.progress = 0
        self.loading_complete = False
        
        # Load pixel font
        self.font = pygame.font.Font(font_path, 16)
        self.small_font = pygame.font.Font(font_path, 12)
        
        # Colors
        self.border_color = (76, 63, 47)  # Dark brown
        self.fill_color = (155, 126, 89)  # Light brown
        self.bg_color = (25, 25, 25)  # Dark background
        self.text_color = (219, 202, 169)  # Cream color
        self.highlight_color = (255, 223, 186)  # Lighter cream for highlights
        
        # Loading bar dimensions
        self.bar_width = 300
        self.bar_height = 20
        self.border_thickness = 4
        self.corner_radius = 10  # Radius for rounded corners
        
        # Position loading bar in center screen
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
        
        # Randomly select message version
        import random
        self.selected_message = random.choice(self.loading_messages)
        
        # Text animation properties
        self.tagalog_alpha = 0
        self.tagalog_fade_in = True
        self.fade_speed = 5

    def draw_rounded_rect(self, surface, color, rect, radius):
        """Draw a rounded rectangle"""
        x, y, width, height = rect
        
        # Create temporary surface for anti-aliasing
        temp_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw the main rectangles
        pygame.draw.rect(temp_surface, color, 
                        (radius, 0, width - 2 * radius, height))
        pygame.draw.rect(temp_surface, color,
                        (0, radius, width, height - 2 * radius))
        
        # Draw the four corner circles
        pygame.draw.circle(temp_surface, color, (radius, radius), radius)
        pygame.draw.circle(temp_surface, color, (width - radius, radius), radius)
        pygame.draw.circle(temp_surface, color, (radius, height - radius), radius)
        pygame.draw.circle(temp_surface, color, (width - radius, height - radius), radius)
        
        # Blit the temporary surface onto the main surface
        surface.blit(temp_surface, (x, y))
    
    def update(self, progress: float):
        self.progress = progress
        self.anim_counter += 1
        
        # Update loading dots animation
        if self.anim_counter % self.dot_update_rate == 0:
            if len(self.dots) < 3:
                self.dots += "."
            else:
                self.dots = ""
        
        # Update tagalog text fade animation
        if self.tagalog_fade_in:
            self.tagalog_alpha = min(255, self.tagalog_alpha + self.fade_speed)
            if self.tagalog_alpha >= 255:
                self.tagalog_fade_in = False
        else:
            self.tagalog_alpha = max(180, self.tagalog_alpha - self.fade_speed)
            if self.tagalog_alpha <= 180:
                self.tagalog_fade_in = True
    
    def draw(self):
        # Fill background
        self.screen.fill(self.bg_color)
        
        # Draw main title
        title_text = self.font.render("ISLA", True, self.text_color)
        title_rect = title_text.get_rect(centerx=640, bottom=self.bar_y - 40)
        self.screen.blit(title_text, title_rect)
        
        # Draw main loading message
        loading_text = self.small_font.render(self.selected_message[0], True, self.text_color)
        loading_rect = loading_text.get_rect(centerx=640, top=self.bar_y + 40)
        self.screen.blit(loading_text, loading_rect)
        
        # Draw Tagalog message with fade effect
        tagalog_text = self.small_font.render(self.selected_message[1], True, self.highlight_color)
        tagalog_text.set_alpha(self.tagalog_alpha)
        tagalog_rect = tagalog_text.get_rect(centerx=640, top=self.bar_y + 60)
        self.screen.blit(tagalog_text, tagalog_rect)
        
        # Draw loading bar border (rounded)
        border_rect = (self.bar_x - self.border_thickness,
                      self.bar_y - self.border_thickness,
                      self.bar_width + (self.border_thickness * 2),
                      self.bar_height + (self.border_thickness * 2))
        self.draw_rounded_rect(self.screen, self.border_color, border_rect, self.corner_radius)
        
        # Draw loading bar background (rounded)
        bg_rect = (self.bar_x, self.bar_y, self.bar_width, self.bar_height)
        self.draw_rounded_rect(self.screen, self.bg_color, bg_rect, self.corner_radius - self.border_thickness)
        
        # Draw loading bar progress (rounded)
        progress_width = int(self.bar_width * self.progress)
        if progress_width > 0:
            progress_rect = (self.bar_x, self.bar_y, progress_width, self.bar_height)
            if progress_width < self.bar_width:
                self.draw_rounded_rect(self.screen, self.fill_color, progress_rect, 
                                     min(self.corner_radius - self.border_thickness, progress_width // 2))
            else:
                self.draw_rounded_rect(self.screen, self.fill_color, progress_rect, 
                                     self.corner_radius - self.border_thickness)
                
class AssetLoader:
    @staticmethod
    def load_image(path):
        image = pygame.image.load(path)
        return pygame.transform.scale(image, (1280, 720))
    
    @staticmethod
    def load_sound(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Warning: Could not load sound {path}: {e}")
            return None

class Scene:
    def __init__(self, image_path: str, text: str, font: pygame.font.Font, 
                 sound_path: str = None, is_first_scene: bool = False, 
                 is_final_scene: bool = False):
        # Visual elements
        self.image = image_path  # Store path initially
        self.loaded_image = None  # Will store the loaded image
        self.text = text
        self.font = font
        
        # State management
        self.state = SceneState.FADE_IN
        self.alpha = 255 if is_first_scene else 0
        self.text_alpha = 255 if is_first_scene else 0
        self.fade_speed = 10  # Increased fade speed
        self.textbox_height = 180
        self.transition_complete = True if is_first_scene else False
        self.is_first_scene = is_first_scene
        self.is_final_scene = is_final_scene
        self.space_pressed = False

        # Space prompt properties
        self.space_prompt_alpha = 0
        self.space_prompt_fade_direction = 1
                
        # Text transition properties
        self.next_text = None
        self.final_text_shown = False
        self.time_active = 0
        
        # Typewriter effect properties
        self.current_text = ""
        self.text_counter = 0
        self.typewriter_speed = 2
        self.typewriter_complete = True if is_first_scene else False
        self.char_buffer = []
        self.last_char_time = 0
        self.char_delay = 5
        self.original_char_delay = 5
        
        # Audio properties
        self.sound_path = sound_path
        self.sound = None
        self.current_volume = 0.0
        self.target_volume = 0.7
        self.volume_fade_speed = 0.08
        
        # Typewriter sound
        self.typewriter_sound = None
        try:
            self.typewriter_sound = pygame.mixer.Sound("audio/typewriter.wav")
            self.typewriter_sound.set_volume(0.3)
        except Exception as e:
            print(f"Warning: Could not load typewriter sound: {e}")

    def load_assets(self):
        if not self.loaded_image:
            self.loaded_image = AssetLoader.load_image(self.image)
        if self.sound_path and not self.sound:
            self.sound = AssetLoader.load_sound(self.sound_path)
            if self.sound:
                self.sound.set_volume(0.0)

    def render(self, screen: pygame.Surface) -> None:
        if not self.loaded_image:
            return
            
        image_surface = self.loaded_image.copy()
        if not self.is_final_scene:
            image_surface.set_alpha(self.alpha)
        else:
            image_surface.set_alpha(255)
        screen.blit(image_surface, (0, 0))
        
        if (self.alpha >= 255 and not self.is_first_scene) or self.is_final_scene:
            if self.text:
                textbox_surface = pygame.Surface((1280, self.textbox_height), pygame.SRCALPHA)
                pygame.draw.rect(textbox_surface, (0, 0, 0, 120), (0, 0, 1280, self.textbox_height))
                textbox_surface.set_alpha(self.text_alpha)
                screen.blit(textbox_surface, (0, 720 - self.textbox_height))
                
                display_text = self.current_text if not self.next_text else self.next_text
                wrapped_text = self.wrap_text(display_text, self.font, 1200)
                base_y_offset = 720 - self.textbox_height + 20
                
                for i, line in enumerate(wrapped_text):
                    text_surface = self.font.render(line, True, (255, 255, 255))
                    text_surface.set_alpha(self.text_alpha)
                    text_rect = text_surface.get_rect(midleft=(40, base_y_offset + (i * 22)))
                    screen.blit(text_surface, text_rect)
                
                if self.typewriter_complete and not (self.is_final_scene and self.final_text_shown):
                    space_text = self.font.render("Press SPACE to continue", True, (255, 255, 255))
                    float_offset = math.sin(self.time_active * 0.03) * 1.5
                    space_text.set_alpha(self.space_prompt_alpha)
                    space_rect = space_text.get_rect(center=(640, 695 + float_offset))
                    screen.blit(space_text, space_rect)

    def update(self) -> None:
        self.time_active += 1
        current_time = pygame.time.get_ticks()
        
        self._update_audio()
        self._update_scene_state(current_time)
        
        if self.typewriter_complete and not (self.is_final_scene and self.final_text_shown):
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
                if self.current_volume <= 0 and self.sound.get_num_channels() > 0 and not self.is_final_scene:
                    self.sound.stop()

    def _update_scene_state(self, current_time: int) -> None:
        if self.state == SceneState.FADE_IN:
            self._handle_fade_in(current_time)
        elif self.state == SceneState.FADE_OUT:
            self._handle_fade_out(current_time)

    def _handle_fade_in(self, current_time: int) -> None:
        if not self.is_final_scene and not self.is_first_scene:
            self.alpha = min(255, self.alpha + self.fade_speed)
        if self.alpha >= 255 or self.is_final_scene:
            self.text_alpha = min(255, self.text_alpha + self.fade_speed)
            if self.text_alpha >= 255:
                self._update_typewriter(current_time)

    def _handle_fade_out(self, current_time: int) -> None:
        if self.is_final_scene and not self.final_text_shown:
            self.text_alpha = max(0, self.text_alpha - self.fade_speed)
            if self.text_alpha <= 0:
                self.next_text = "History lives here. And now, so do you."
                self.text = self.next_text
                self.final_text_shown = True
                self.state = SceneState.FADE_IN
                self.current_text = ""
                self.text_counter = 0
                self.typewriter_complete = False
                self.char_delay = 50
                self.last_char_time = current_time
                if self.typewriter_sound:
                    self.typewriter_sound.set_volume(0.15)
        else:
            self.text_alpha = max(0, self.text_alpha - self.fade_speed)
            if self.text_alpha <= 0:
                self.alpha = max(0, self.alpha - self.fade_speed)

    def _update_typewriter(self, current_time: int) -> None:
        if not self.typewriter_complete:
            if self.is_final_scene and self.text == "History lives here. And now, so do you." and not self.space_pressed:
                char_delay = 50
            else:
                char_delay = 3 if self.space_pressed else self.original_char_delay
                
            if current_time - self.last_char_time >= char_delay:
                target_text = self.text if not self.next_text else self.next_text
                if len(self.current_text) < len(target_text):
                    if self.typewriter_sound and self.typewriter_sound.get_num_channels() == 0:
                        self.typewriter_sound.play(-1)
                    characters_to_add = 5 if self.space_pressed else 2
                    end_index = min(len(self.current_text) + characters_to_add, len(target_text))
                    self.current_text += target_text[len(self.current_text):end_index]
                    self.last_char_time = current_time
                else:
                    self.typewriter_complete = True
                    self.transition_complete = True
                    self._fade_out_typewriter()

    def _fade_out_typewriter(self):
        if self.typewriter_sound:
            current_volume = self.typewriter_sound.get_volume()
            while current_volume > 0:
                current_volume = max(0, current_volume - 0.1)
                self.typewriter_sound.set_volume(current_volume)
                if current_volume <= 0:
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
        if self.sound and self.sound.get_num_channels() > 0 and not self.is_final_scene:
            self.sound.stop()
        if self.typewriter_sound and self.typewriter_sound.get_num_channels() > 0:
            self.typewriter_sound.stop()

class OpeningSequence:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("ISLA")
        
        font_path = Path("font/pixel_font.ttf")
        self.font = pygame.font.Font(font_path, 14)
        pygame.display.set_icon(pygame.image.load("assets/first_airport.png"))
        
        self.scenes = self._initialize_scenes()
        self.loading_screen = LoadingScreen(self.screen, str(font_path))
        self.loading_complete = False
        
        self.current_scene = 0
        self.clock = pygame.time.Clock()
        self.transitioning = False
        self.last_space_time = 0
        self.space_cooldown = 10
        
        self.initial_fade_alpha = 255
        self.initial_fade_complete = False

    def _initialize_scenes(self) -> list:
        return [
            Scene("assets/first_airport.png", 
                 "", 
                 self.font, 
                 "audio/first_airplane.wav",
                 is_first_scene=True),
            
            Scene("assets/second_arrival.png", 
                 "You are a Filipino who has spent most of your life abroad. After years away, you have returned to the Philippines to rediscover the land of your ancestors.", 
                 self.font, 
                 "audio/second_terminal.wav"),
            
            Scene("assets/third_outside.png",  
                 "Armed with curiosity and a map, your first stop is a place steeped in history and mystery: Intramuros, the Walled City.",
                 self.font,
                 "audio/third_street.wav"),
            
            Scene("assets/fourth_intramuros.png",
                 "Welcome to Intramuros ('inside the walls'), the heart of old Manila and the crown jewel of Spanish colonial rule in the Philippines. Founded in 1571 by conquistador Miguel López de Legazpi, this fortified city was designed to protect Spain's empire in the East Indies, marked by its imposing walls, towering 6.7 meters high and 2.4 meters thick.",
                 self.font,
                 "audio/fourth_bell.wav"),
            
            Scene("assets/fifth_santiago.png",
                 "At the heart of Intramuros rose Fort Santiago, a symbol of unyielding power where the Pasig River met Manila Bay. Rebuilt in stone after a fierce pirate attack in 1574, the fort became both protector and prison. Under Spanish, British, American, and Japanese rule, its walls held countless souls—including the nation's hero, José Rizal.",
                 self.font,
                 "audio/fifth_war.wav"),
            
            Scene("assets/sixth_trade.png",
                 "Intramuros stood as the stronghold of Spanish authority and the center of the Manila-Acapulco Galleon Trade, where silver from the Americas fueled Asia's demand for silk, spices, and porcelain. Traders from China and sailors from distant lands passed through its gates. Yet beneath its bustling markets and grand walls lurked darker tales of invasions, betrayals, and unending conflict.",
                 self.font,
                 "audio/sixth_footsteps.wav"),
            
            Scene("assets/seventh_prison.png",
                 "For four centuries, the walls of Intramuros have witnessed the rise and fall of regimes, from the decline of Spanish rule to the horrors of World War II. In 1945, the Battle of Manila ravaged the city, leaving only San Agustin Church standing amid the ruins. Beneath Fort Santiago, the remains of 600 prisoners of war lie buried, a chilling reminder of the atrocities that transpired within these walls.",
                 self.font,
                 "audio/seventh_banging.wav"),
            
            Scene("assets/eight_ghost.png",
                 "Some say the souls of these victims still wander its streets and tunnels—spirits trapped between this world and the next.",
                 self.font,
                 "audio/eight_whispers.wav"),
            
            Scene("assets/ninth_guard.png",
                 "They say the ghost of a Spanish guard watches over the gate, unable to leave his post even in death.",
                 self.font,
                 "audio/ninth_lantern.wav"),
            
            Scene("assets/tenth_girl.png",
                 "In a quiet corner of Fort Santiago, whispers tell of a young woman waiting for her lost lover, eternally bound to the walls.",
                 self.font,
                 "audio/tenth_humming.wav",
                 is_final_scene=True)
        ]
    
    def _preload_assets(self):
        total_assets = len(self.scenes)
        assets_loaded = 0
        
        # Preload all assets with progress tracking
        with ThreadPoolExecutor() as executor:
            futures = []
            for scene in self.scenes:
                future = executor.submit(scene.load_assets)
                futures.append(future)
            
            while assets_loaded < total_assets:
                completed = sum(1 for f in futures if f.done())
                progress = completed / total_assets
                
                # Update and draw loading screen
                self.loading_screen.update(progress)
                self.loading_screen.draw()
                pygame.display.flip()
                
                assets_loaded = completed
                self.clock.tick(60)
        
        self.loading_complete = True

    def run(self):
        # Show loading screen and preload assets
        self._preload_assets()
        
        running = True
        self.scenes[0].start_sound()
        fade_surface = pygame.Surface((1280, 720))
        fade_surface.fill((0, 0, 0))
        
        while running:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.fade_out()
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.initial_fade_complete:
                        if current_time - self.last_space_time >= self.space_cooldown:
                            current_scene = self.scenes[self.current_scene]
                            current_scene.space_pressed = True
                            current_scene._fade_out_typewriter()
                            if not self.transitioning:
                                if current_scene.is_final_scene and not current_scene.final_text_shown:
                                    current_scene.state = SceneState.FADE_OUT
                                elif not current_scene.is_final_scene and self.current_scene < len(self.scenes) - 1:
                                    self.transitioning = True
                                    current_scene.state = SceneState.FADE_OUT
                            self.last_space_time = current_time
                    elif event.key == pygame.K_ESCAPE:
                        self.fade_out()
                        running = False
            
            self.screen.fill((0, 0, 0))
            
            # Handle the initial scene
            if not self.initial_fade_complete:
                current_scene = self.scenes[self.current_scene]
                current_scene.render(self.screen)
                
                # Apply fade overlay
                fade_surface.set_alpha(self.initial_fade_alpha)
                self.screen.blit(fade_surface, (0, 0))
                
                # Decrease fade alpha
                self.initial_fade_alpha = max(0, self.initial_fade_alpha - 5)
                
                if self.initial_fade_alpha <= 0:
                    self.initial_fade_complete = True
            else:
                # Normal scene handling
                current_scene = self.scenes[self.current_scene]
                current_scene.update()
                
                if self.transitioning and current_scene.alpha <= 0:
                    if not self.scenes[self.current_scene].is_final_scene:
                        current_scene.stop_sound()
                    self.current_scene += 1
                    if not self.scenes[self.current_scene - 1].is_final_scene:
                        self.scenes[self.current_scene].start_sound()
                    self.transitioning = False
                    
                current_scene.render(self.screen)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        for scene in self.scenes:
            if scene.sound and not scene.is_final_scene:
                scene.stop_sound()
            if scene.typewriter_sound:
                scene.typewriter_sound.stop()
        
        pygame.quit()
        sys.exit()
    
    def fade_out(self):
        alpha = 0
        fade_surface = pygame.Surface((1280, 720))
        fade_surface.fill((0, 0, 0))
        
        while alpha < 255:
            self.screen.fill((0, 0, 0))
            self.scenes[self.current_scene].render(self.screen)
            fade_surface.set_alpha(alpha)
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            alpha += 8
            self.clock.tick(60)

def main():
    # Set higher priority for the game process
    try:
        import os
        if os.name == 'nt':  # Windows
            import psutil
            process = psutil.Process()
            process.nice(psutil.HIGH_PRIORITY_CLASS)
        else:  # Unix-based
            os.nice(-10)
    except:
        pass

    sequence = OpeningSequence()
    sequence.run()

if __name__ == "__main__":
    main()