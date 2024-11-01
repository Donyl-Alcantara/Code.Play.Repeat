import pygame
import sys
import time
import math
import random
from pygame import gfxdraw  # For anti-aliased rendering

class SmoothParticle:
    def __init__(self, x, y, color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.orig_x = x
        self.orig_y = y
        self.color = color
        self.size = random.uniform(1.5, 4.0)
        self.life = 1.0
        self.fade_speed = random.uniform(0.002, 0.008)
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.2, 0.8)
        self.sin_offset = random.uniform(0, 2 * math.pi)
        self.sin_speed = random.uniform(0.02, 0.05)

    def update(self):
        self.life -= self.fade_speed
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        # Add subtle floating motion
        self.y += math.sin(self.sin_offset + time.time() * self.sin_speed) * 0.5
        return self.life > 0

    def draw(self, screen):
        if self.life > 0:
            alpha = int(self.life * 255)
            radius = self.size * (0.8 + 0.2 * math.sin(time.time() * 2 + self.sin_offset))
            gfxdraw.filled_circle(screen, int(self.x), int(self.y), int(radius),
                                (*self.color, alpha))
            gfxdraw.aacircle(screen, int(self.x), int(self.y), int(radius),
                            (*self.color, alpha))

class PremiumSplashScreen:
    def __init__(self):
        pygame.init()
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("ISLA")
        self.clock = pygame.time.Clock()
        
        self.background = (0, 0, 0)
        self.particles = []
        
        try:
            # Load and prepare images with smooth scaling
            self.pygame_logo = pygame.image.load("pygame_powered.png").convert_alpha()
            self.dev_logo = pygame.image.load("Logo.png").convert_alpha()
            
            # Calculate optimal sizes while maintaining aspect ratios
            pygame_aspect = self.pygame_logo.get_width() / self.pygame_logo.get_height()
            dev_aspect = self.dev_logo.get_width() / self.dev_logo.get_height()
            
            base_height = 200
            
            # Create high-quality scaled versions
            self.pygame_logo_orig = self.smooth_scale(
                self.pygame_logo,
                (int(base_height * pygame_aspect), base_height)
            )
            self.dev_logo_orig = self.smooth_scale(
                self.dev_logo,
                (int(base_height * dev_aspect), base_height)
            )
            
        except pygame.error as e:
            print(f"Couldn't load image: {e}")
            sys.exit(1)

    def smooth_scale(self, surface, size):
        """Multi-step scaling for smoother results"""
        current = surface
        target_w, target_h = size
        current_w, current_h = surface.get_width(), surface.get_height()
        
        # Gradually scale down in steps for better quality
        while current_w > target_w * 2 or current_h > target_h * 2:
            current_w = max(target_w, current_w // 2)
            current_h = max(target_h, current_h // 2)
            current = pygame.transform.smoothscale(current, (current_w, current_h))
        
        return pygame.transform.smoothscale(current, size)

    def create_particles(self, x, y, amount=3):
        for _ in range(amount):
            self.particles.append(SmoothParticle(x, y))

    def update_particles(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw_particles(self):
        for particle in self.particles:
            particle.draw(self.screen)

    def smooth_step(self, x):
        """Smoother step function for ultra-smooth transitions"""
        x = max(0, min(1, x))
        return x * x * x * (x * (x * 6 - 15) + 10)

    def transform_image(self, image, scale, rotation=0):
        """Transform image with smooth scaling and rotation"""
        width = int(image.get_width() * scale)
        height = int(image.get_height() * scale)
        
        if width == 0 or height == 0:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
            
        scaled = pygame.transform.smoothscale(image, (width, height))
        
        if rotation != 0:
            scaled = pygame.transform.rotozoom(scaled, rotation, 1)
            
        return scaled

    def display_logo(self, logo, is_final=False):
        start_time = time.time()
        
        # Refined animation timings
        zoom_in_duration = 2.5  # Slower, more elegant zoom
        hold_duration = 1.8
        fade_out_duration = 1.2
        total_duration = zoom_in_duration + hold_duration + fade_out_duration
        
        last_scale = 0.01  # For smooth interpolation
        last_rotation = 0
        
        while True:
            current_time = time.time() - start_time
            
            if current_time >= total_duration and not is_final:
                break
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            self.screen.fill(self.background)
            
            # Update and draw particles
            self.update_particles()
            self.draw_particles()
            
            if current_time < zoom_in_duration:
                # Ultra-smooth zoom in
                progress = current_time / zoom_in_duration
                ease_progress = self.smooth_step(progress)
                target_scale = 0.01 + (0.99 * ease_progress)
                
                # Interpolate between last and target scale for extra smoothness
                scale = last_scale + (target_scale - last_scale) * 0.2
                last_scale = scale
                
                # Subtle rotation during zoom
                target_rotation = 5 * (1 - ease_progress)
                rotation = last_rotation + (target_rotation - last_rotation) * 0.2
                last_rotation = rotation
                
                alpha = int(255 * min(1, progress * 2))
                
                # Create particles during zoom
                if random.random() < 0.4:
                    x = self.screen_width // 2 + random.randint(-100, 100)
                    y = self.screen_height // 2 + random.randint(-100, 100)
                    self.create_particles(x, y, 1)
                    
            elif current_time < (zoom_in_duration + hold_duration):
                scale = 1.0
                rotation = 0
                alpha = 255
                
                # Subtle particles during hold
                if random.random() < 0.2:
                    x = self.screen_width // 2 + random.randint(-150, 150)
                    y = self.screen_height // 2 + random.randint(-150, 150)
                    self.create_particles(x, y, 1)
                    
            else:
                fade_progress = (current_time - (zoom_in_duration + hold_duration)) / fade_out_duration
                ease_fade = self.smooth_step(fade_progress)
                scale = 1.0 + (0.05 * ease_fade)  # Subtle zoom during fade
                rotation = 0
                alpha = int(255 * (1 - ease_fade))
            
            # Transform and display logo
            current_logo = self.transform_image(logo, scale, rotation)
            
            # Center the image
            x = (self.screen_width - current_logo.get_width()) // 2
            y = (self.screen_height - current_logo.get_height()) // 2
            
            # Draw subtle glow/shadow
            shadow_surf = pygame.Surface(current_logo.get_size(), pygame.SRCALPHA)
            shadow_alpha = int(alpha * 0.3)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha),
                              (0, 0, current_logo.get_width(), current_logo.get_height()))
            shadow_surf = pygame.transform.smoothscale(shadow_surf,
                                                     (int(current_logo.get_width() * 1.1),
                                                      int(current_logo.get_height() * 1.1)))
            shadow_x = x - (shadow_surf.get_width() - current_logo.get_width()) // 2
            shadow_y = y - (shadow_surf.get_height() - current_logo.get_height()) // 2
            self.screen.blit(shadow_surf, (shadow_x, shadow_y))
            
            # Apply alpha and draw logo
            temp_surface = current_logo.copy()
            temp_surface.set_alpha(alpha)
            self.screen.blit(temp_surface, (x, y))
            
            pygame.display.flip()
            self.clock.tick(144)  # Higher frame rate for smoother animation

    def cross_fade(self, duration=1.0):
        """Smooth cross-fade transition between scenes"""
        start_time = time.time()
        temp = pygame.Surface((self.screen_width, self.screen_height))
        temp.fill(self.background)
        
        while time.time() - start_time < duration:
            progress = (time.time() - start_time) / duration
            alpha = int(255 * self.smooth_step(progress))
            temp.set_alpha(alpha)
            self.screen.blit(temp, (0, 0))
            pygame.display.flip()
            self.clock.tick(144)

    def run_sequence(self):
        # Initial fade in
        self.cross_fade(0.8)
        
        # First logo
        self.display_logo(self.pygame_logo_orig)
        self.cross_fade(0.8)  # Smooth transition
        
        # Second logo
        self.display_logo(self.dev_logo_orig, True)
        self.cross_fade(0.8)  # Final fade out

if __name__ == "__main__":
    splash = PremiumSplashScreen()
    splash.run_sequence()
    pygame.quit()
