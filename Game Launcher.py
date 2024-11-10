import pygame
import sys
import time
import math
from pygame import gfxdraw
from pygame import mixer
from storyscreen_intramuros import OpeningSequence  # Import the OpeningSequence class

class GameLauncher:
    def __init__(self):
        pygame.init()
        mixer.init()
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("ISLA")
        self.clock = pygame.time.Clock()
        self.state = 'splash'
        
        self.background = (0, 0, 0)
        
        # Audio setup
        try:
            self.music = mixer.Sound("audio/islamapost.mp3")
            self.click_sound = mixer.Sound("audio/click.wav")
            self.click_sound.set_volume(0.5)
            self.current_volume = 0.0
            self.target_volume = 0.7
            self.music.set_volume(self.current_volume)
            self.music_started = False
        except pygame.error as e:
            print(f"Couldn't load audio: {e}")
            sys.exit(1)
        
        try:
            self.pygame_logo = pygame.image.load("assets/pygame_powered.png").convert_alpha()
            self.dev_logo = pygame.image.load("assets/Logo2.png").convert_alpha()
            self.menu_background = pygame.image.load('assets/menu_screen.png')
            self.menu_background = pygame.transform.scale(
                self.menu_background, 
                (self.screen_width, self.screen_height)
            )
            
            pygame_aspect = self.pygame_logo.get_width() / self.pygame_logo.get_height()
            dev_aspect = self.dev_logo.get_width() / self.dev_logo.get_height()
            
            pygame_base_height = 200
            dev_base_height = 500
            
            self.pygame_logo_orig = self.scale_image(
                self.pygame_logo,
                (int(pygame_base_height * pygame_aspect), pygame_base_height)
            )
            self.dev_logo_orig = self.scale_image(
                self.dev_logo,
                (int(dev_base_height * dev_aspect), dev_base_height)
            )
            
        except pygame.error as e:
            print(f"Couldn't load image: {e}")
            sys.exit(1)
            
        self.marker = pygame.Surface((220, 40))
        self.marker.set_alpha(0)
        self.marker_rect = self.marker.get_rect(center=(self.screen_width // 2, 230))
        self.fade_alpha = 255
        self.transitioning = False
        self.menu_reveal_complete = False
        self.click_played = False

    def scale_image(self, surface, size):
        return pygame.transform.smoothscale(surface, size)  # Using smoothscale for better quality

    def smooth_step(self, x):
        # Enhanced smoothstep function with additional smoothing
        x = max(0, min(1, x))
        return x * x * (3 - 2 * x)

    def update_music_volume(self, target, rate=0.02):
        if abs(self.current_volume - target) > 0.001:  # Increased precision
            self.current_volume += (target - self.current_volume) * rate
            self.music.set_volume(max(0.0, min(1.0, self.current_volume)))
            return False
        self.current_volume = target
        self.music.set_volume(target)
        return True

    def transform_image(self, image, scale, rotation=0):
        target_width = int(image.get_width() * scale)
        target_height = int(image.get_height() * scale)
        
        if target_width <= 1 or target_height <= 1:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
            
        # Use smoothscale for better quality scaling
        scaled = pygame.transform.smoothscale(image, (target_width, target_height))
        
        if rotation != 0:
            # Smoother rotation with rotozoom
            scaled = pygame.transform.rotozoom(scaled, rotation, 1.0)
            
        return scaled

    def display_logo(self, logo, is_final=False):
        start_time = time.time()
        zoom_in_duration = 2.5
        hold_duration = 3.0 if is_final else 1.8
        fade_out_duration = 1.2
        total_duration = zoom_in_duration + hold_duration + fade_out_duration
        
        last_scale = 0.01
        last_rotation = 0
        
        while True:
            current_time = time.time() - start_time
            
            if current_time >= total_duration:
                break
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return True

            if self.music_started:
                if current_time < zoom_in_duration:
                    target_volume = self.target_volume * (current_time / zoom_in_duration)
                elif current_time < (zoom_in_duration + hold_duration):
                    target_volume = self.target_volume
                else:
                    fade_progress = (current_time - (zoom_in_duration + hold_duration)) / fade_out_duration
                    target_volume = self.target_volume * (1 - self.smooth_step(fade_progress))
                
                self.update_music_volume(target_volume, rate=0.025)
            
            self.screen.fill(self.background)
            
            if current_time < zoom_in_duration:
                progress = current_time / zoom_in_duration
                ease_progress = self.smooth_step(progress)
                target_scale = 0.01 + (0.99 * ease_progress)
                scale = last_scale + (target_scale - last_scale) * 0.25  # Smoother scale interpolation
                last_scale = scale
                
                target_rotation = 5 * (1 - ease_progress)
                rotation = last_rotation + (target_rotation - last_rotation) * 0.25  # Smoother rotation
                last_rotation = rotation
                
                alpha = int(255 * min(1, progress * 2))
            elif current_time < (zoom_in_duration + hold_duration):
                scale = 1.0
                rotation = 0
                alpha = 255
            else:
                fade_progress = (current_time - (zoom_in_duration + hold_duration)) / fade_out_duration
                scale = 1.0 + (0.05 * self.smooth_step(fade_progress))
                rotation = 0
                alpha = int(255 * (1 - self.smooth_step(fade_progress)))
            
            current_logo = self.transform_image(logo, scale, rotation)
            x = (self.screen_width - current_logo.get_width()) // 2
            y = (self.screen_height - current_logo.get_height()) // 2
            
            # Enhanced shadow
            shadow_surf = pygame.Surface(current_logo.get_size(), pygame.SRCALPHA)
            shadow_alpha = int(alpha * 0.3)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha),
                              (0, 0, current_logo.get_width(), current_logo.get_height()))
            shadow_surf = pygame.transform.smoothscale(
                shadow_surf,
                (int(current_logo.get_width() * 1.1),
                 int(current_logo.get_height() * 1.1))
            )
            shadow_x = x - (shadow_surf.get_width() - current_logo.get_width()) // 2
            shadow_y = y - (shadow_surf.get_height() - current_logo.get_height()) // 2
            self.screen.blit(shadow_surf, (shadow_x, shadow_y))
            
            temp_surface = current_logo.copy()
            temp_surface.set_alpha(alpha)
            self.screen.blit(temp_surface, (x, y))
            
            pygame.display.flip()
            self.clock.tick(144)
        
        return True

    def reveal_menu(self):
        if not self.music_started:
            self.music.play(-1)
            self.music_started = True
            
        start_time = time.time()
        fade_duration = 2.5
        
        self.screen.blit(self.menu_background, (0, 0))
        
        while True:
            current_time = time.time() - start_time
            progress = min(current_time / fade_duration, 1.0)
            
            if progress >= 1.0:
                self.menu_reveal_complete = True
                break
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
            
            target_volume = self.target_volume * self.smooth_step(progress)
            self.update_music_volume(target_volume, rate=0.025)
            
            fade_surface = pygame.Surface((self.screen_width, self.screen_height))
            fade_surface.fill((0, 0, 0))
            
            ease_progress = self.smooth_step(progress)
            fade_surface.set_alpha(int(255 * (1 - ease_progress)))
            
            self.screen.blit(self.menu_background, (0, 0))
            self.screen.blit(fade_surface, (0, 0))
            
            pygame.display.flip()
            self.clock.tick(144)
        
        return True

    def cross_fade(self, duration=0.8):
        start_time = time.time()
        temp = pygame.Surface((self.screen_width, self.screen_height))
        temp.fill(self.background)
        
        while time.time() - start_time < duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
            
            progress = (time.time() - start_time) / duration
            alpha = int(255 * self.smooth_step(progress))
            temp.set_alpha(alpha)
            self.screen.blit(temp, (0, 0))
            pygame.display.flip()
            self.clock.tick(144)
        
        return True

    def splash_sequence(self):
        if not self.cross_fade(0.8):
            return False
        if not self.display_logo(self.pygame_logo_orig):
            return False
        if not self.cross_fade(0.8):
            return False
        if not self.display_logo(self.dev_logo_orig, True):
            return False
        if not self.cross_fade(0.8):
            return False
        if not self.reveal_menu():
            return False
        self.state = 'menu'
        return True

    def menu_state(self):
        if not self.menu_reveal_complete:
            return self.reveal_menu()
            
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.marker_rect.collidepoint(mouse_pos) and not self.transitioning:
                    self.click_sound.play()  # Play click sound when marker area is clicked
                    self.transitioning = True
                    self.click_played = True

        if self.transitioning:
            # Only start fading music after click sound has had a chance to play
            if self.click_played and not mixer.get_busy():  # Check if click sound finished playing
                self.update_music_volume(0.0, rate=0.05)
                if self.current_volume <= 0.01:
                    self.music.stop()
                    self.music_started = False

        self.screen.blit(self.menu_background, (0, 0))
        self.screen.blit(self.marker, self.marker_rect)
        
        if self.transitioning:
            self.fade_alpha = min(self.fade_alpha + 3, 255)
            fade_surface = pygame.Surface((self.screen_width, self.screen_height))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(fade_surface, (0, 0))
            
            if self.fade_alpha >= 255:
                self.state = 'game'

        if self.marker_rect.collidepoint(mouse_pos):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.flip()
        return True

    def game_state(self):
        # Stop the menu music completely
        if self.music_started:
            self.music.stop()
            self.music_started = False
        
        # Initialize and run the opening sequence
        sequence = OpeningSequence()
        sequence.run()
        
        # The game will exit after the sequence ends
        return False

    def run(self):
        running = True
        while running:
            self.clock.tick(144)
            
            if self.state == 'splash':
                running = self.splash_sequence()
            elif self.state == 'menu':
                running = self.menu_state()
            elif self.state == 'game':
                running = self.game_state()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":  
    game = GameLauncher()
    game.run()