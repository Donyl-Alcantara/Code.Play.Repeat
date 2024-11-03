import pygame
import sys
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
        self.alpha = 0  # Always start at 0 for fade in
        self.text_alpha = 0  # Always start at 0 for fade in
        self.fade_speed = 7
        self.textbox_height = 180
        self.transition_complete = False  # Always start false
        self.is_first_scene = is_first_scene
        self.is_final_scene = is_final_scene
        self.space_pressed = False # Flag to track if space is pressed - controls text speed acceleration

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
        self.typewriter_speed = 1
        self.typewriter_complete = False  # Start false for all scenes
        self.char_buffer = []
        self.last_char_time = 0
        self.char_delay = 10
        self.original_char_delay = 10 
        
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

        #Typewriter properties/sound
        self.typewriter_sound = None
        try:
            self.typewriter_sound = pygame.mixer.Sound("typewriter.wav")
            self.typewriter_sound.set_volume(0.5)  # Lower volume for typing sound
        except Exception as e:
            print(f"Warning: Could not load typewriter sound: {e}")

    def render(self, screen: pygame.Surface) -> None:
        image_surface = self.image.copy()
        if not self.is_final_scene:
            image_surface.set_alpha(self.alpha)
        else:
            image_surface.set_alpha(255)
        screen.blit(image_surface, (0, 0))
        
        if (self.alpha >= 255) or self.is_final_scene:  # Modified condition for first scene
            if self.text:
                textbox_surface = pygame.Surface((1280, self.textbox_height), pygame.SRCALPHA)
                for i in range(self.textbox_height):
                    alpha = int(120 * (1 - (i / self.textbox_height) * 0.3))
                    pygame.draw.rect(textbox_surface, (0, 0, 0, alpha), (0, i, 1280, 1))
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
        if not self.is_final_scene:
            self.alpha = min(255, self.alpha + self.fade_speed)
        if self.alpha >= 255 or self.is_final_scene:
            self.text_alpha = min(255, self.text_alpha + self.fade_speed)
            if self.text_alpha >= 255:
                self._update_typewriter(current_time)

    def _handle_fade_out(self, current_time: int) -> None:
        if self.is_final_scene and not self.final_text_shown:
            self.text_alpha = max(0, self.text_alpha - self.fade_speed)
            if self.text_alpha <= 0:
                self.next_text = "Today, Cebu's story of resistance and resilience lives on, embedded into its colorful practices and spirit."
                self.text = self.next_text
                self.final_text_shown = True
                self.state = SceneState.FADE_IN
                self.current_text = ""  # Reset for typing effect
                self.text_counter = 0
                self.typewriter_complete = False
                self.char_delay = 50  # Slower typing for dramatic effect
                self.last_char_time = current_time
                if self.typewriter_sound:
                    self.typewriter_sound.set_volume(0.15)  # Slightly louder for final text
        else:
            self.text_alpha = max(0, self.text_alpha - self.fade_speed)
            if self.text_alpha <= 0:
                self.alpha = max(0, self.alpha - self.fade_speed)

    def _update_typewriter(self, current_time: int) -> None:
        if not self.typewriter_complete:
            if self.is_final_scene and self.text == "Today, Cebu's story of resistance and resilience lives on, embedded into its colorful practices and spirit." and not self.space_pressed:
                char_delay = 50  # Dramatic slow typing
            else:
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
       
       font_path = Path("pixel_font.ttf")
       self.font = pygame.font.Font(font_path, 14)
       pygame.display.set_icon(pygame.image.load("first_cebu.png"))
       
       self.scenes = self._initialize_scenes()
       
       self.current_scene = 0
       self.clock = pygame.time.Clock()
       self.transitioning = False
       self.last_space_time = 0
       self.space_cooldown = 15

   def _initialize_scenes(self) -> list:
        return [
            Scene("first_cebu.png", 
                'Welcome to Cebu, one of the oldest cities in the Philippines. Before the Spanish arrived, Cebu already thrived as a hub for merchants from China, Japan, and beyond. Here, communities known as "barangays" flourished under the rule of "datus," chieftains who rose through strength, wisdom, and wealth, keeping everyone safe in their close-knit communities.', 
                self.font, 
                "first_esong.wav",
                is_first_scene=True),
            
            Scene("second_limasawa.png", 
                'But in 1521, the peace was shattered by the arrival of Ferdinand Magellan, sent by Spain to spread the "Three Gs": God, Gold, and Glory. Rajah Humabon, Cebu\'s ruler then, welcomed him and even converted to Christianity.', 
                self.font, 
                "second_folksong.wav"),
            
            Scene("third_mactan.png",
                "But not everyone was so willing to submit. On nearby Mactan Island, Datu Lapulapu refused to bow to foreign powers. In a battle that would make history, Lapulapu and his warriors defeated Magellan, holding onto Cebu's freedom—at least for a while.",
                self.font,
                "third_sagayan.wav"),
            
            Scene("fourth_american.png",
                "Spanish forces eventually returned, building churches, forts, and watchtowers as they tightened their hold on the city. For years, Cebu fought against colonial rule, and when the Philippine Revolution ignited in 1898, Cebuanos took up arms. Just as independence seemed within reach, American ships appeared, marking the start of yet another chapter of struggle.",
                self.font,
                "fourth_bayanko_1stver.wav",
                is_final_scene=True)
        ]

   def run(self):
       running = True
       self.scenes[0].start_sound()
       
       while running:
           current_time = pygame.time.get_ticks()
           
           for event in pygame.event.get():
               if event.type == pygame.QUIT:
                   self.fade_out()
                   running = False
               elif event.type == pygame.KEYDOWN:
                   if event.key == pygame.K_SPACE:
                       if current_time - self.last_space_time >= self.space_cooldown:
                           current_scene = self.scenes[self.current_scene]
                           current_scene.space_pressed = True
                           current_scene._fade_out_typewriter()  # Fade out typewriter sound immediately
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
           alpha += 5
           self.clock.tick(60)

def main():
  sequence = OpeningSequence()
  sequence.run()

if __name__ == "__main__":
  main()