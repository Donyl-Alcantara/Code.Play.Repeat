import pygame
import sys
import os
from enum import Enum, auto
from pathlib import Path
import time
import math
import pygame.mixer

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
        
        # Render text box and text when image has faded in
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
                
                # Render space prompt with pulsing effect
                if self.typewriter_complete:
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
        
        # Update space prompt
        if self.typewriter_complete and not self.ready_for_next:
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
            else:
                self.alpha = max(0, self.alpha - self.fade_speed)
                if self.alpha <= 0:
                    self.transition_complete = True

    def _update_typewriter(self, current_time: int) -> None:
        if not self.typewriter_complete:
            char_delay = 5 if self.space_pressed else self.original_char_delay
            
            if current_time - self.last_char_time >= char_delay:
                target_text = self.text if not self.next_text else self.next_text
                if len(self.current_text) < len(target_text):
                    if self.typewriter_sound and self.typewriter_sound.get_num_channels() == 0:
                        self.typewriter_sound.play(-1)
                    characters_to_add = 3 if self.space_pressed else 1
                    end_index = min(len(self.current_text) + characters_to_add, len(target_text))
                    self.current_text += target_text[len(self.current_text):end_index]
                    self.last_char_time = current_time
                else:
                    self.typewriter_complete = True
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
        if self.sound and self.sound.get_num_channels() > 0:
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
        pygame.display.set_icon(pygame.image.load("assets/first_farm.png"))
        
        self.scenes = self._initialize_scenes()
        self.current_scene = 0
        self.clock = pygame.time.Clock()
        self.transitioning = False
        self.last_space_time = 0
        self.space_cooldown = 250

    def _initialize_scenes(self) -> list:
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
        # Fade out all current sounds
        for scene in self.scenes:
            scene.stop_sound()
            
        # Fade out visual
        fade_surface = pygame.Surface((1280, 720))
        fade_surface.fill((0, 0, 0))
        
        # Fade to black
        for alpha in range(0, 255, 5):
            self.screen.fill((0, 0, 0))
            self.scenes[self.current_scene].render(self.screen)
            fade_surface.set_alpha(alpha)
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            self.clock.tick(60)
        
        # Import and start game
        from BANAUE import Game
        game = Game()
        game.run()

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
                        
                        # Only process space if enough time has passed since last press
                        if current_time - self.last_space_time >= self.space_cooldown:
                            self.last_space_time = current_time
                            
                            # Handle final scene differently
                            if current_scene.is_final_scene and current_scene.final_text_shown and current_scene.typewriter_complete:
                                self.transition_to_game()
                                return
                            
                            # Handle other scenes
                            elif current_scene.typewriter_complete and not self.transitioning:
                                current_scene.space_pressed = True
                                current_scene.ready_for_next = True
                                current_scene.state = SceneState.FADE_OUT
                                self.transitioning = True
                            # Speed up typewriter if still typing
                            elif not current_scene.typewriter_complete:
                                current_scene.space_pressed = True
                                
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            self.screen.fill((0, 0, 0))
            current_scene = self.scenes[self.current_scene]
            current_scene.update()
            
            # Handle scene transition
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

def main():
    sequence = OpeningSequence()
    sequence.run()

if __name__ == "__main__":
    main()