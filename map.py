import pygame
import sys
from pygame.math import Vector2
import random
import math
import pygame.gfxdraw
import json

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()

# Set up the display
screen_width, screen_height = 1280, 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Philippine Map")

# Colors
SEA_COLOR = (53, 180, 186, 255)
LAND_COLOR = (124, 252, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
SHADOW_COLOR = (100, 100, 100, 128)
BUBBLE_COLOR = (255, 255, 255, 200)

# Load and scale images
original_map = pygame.image.load("assets/pixel_philippines_map.png").convert_alpha()
star_img = pygame.image.load("assets/star.png").convert_alpha()

# Load sounds
click_sound = pygame.mixer.Sound("audio/click.wav")
ambient_sound = pygame.mixer.Sound("audio/islamapost.mp3")
ambient_sound.play(-1)  # Loop ambient sound

# Load location data
try:
    with open("philippines_data.json", "r") as f:
        locations = json.load(f)
    print("Loaded locations:", locations)
    if not locations:
        raise ValueError("Empty JSON data")
except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
    print(f"Error loading locations: {e}")
    sys.exit(1)

# Fonts
try:
    main_font = pygame.font.Font("font/pixel_font.ttf", 18)
    small_font = pygame.font.Font("font/pixel_font.ttf", 14)
    title_font = pygame.font.Font("font/pixel_font.ttf", 24)
    instruction_font = pygame.font.Font("font/pixel_font.ttf", 8)
except:
    print("Custom font not found. Using default font.")
    main_font = pygame.font.Font(None, 18)
    small_font = pygame.font.Font(None, 14)
    title_font = pygame.font.Font(None, 24)
    instruction_font = pygame.font.Font(None, 14)

class Particle:
    def __init__(self, pos, color):
        self.pos = Vector2(pos)
        self.vel = Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        self.color = color
        self.life = 255

    def update(self):
        self.pos += self.vel
        self.life -= 5

    def draw(self, surface):
        if self.life > 0:
            pygame.gfxdraw.pixel(surface, int(self.pos.x), int(self.pos.y), 
                               (*self.color, self.life))

class Star:
    def __init__(self, pos):
        self.pos = Vector2(pos)
        self.brightness = random.uniform(0.5, 1)
        self.twinkle_speed = random.uniform(1, 3)
        self.time = random.uniform(0, 2 * math.pi)

    def update(self, dt):
        self.time += self.twinkle_speed * dt
        self.brightness = 0.5 + 0.5 * math.sin(self.time)

    def draw(self, surface):
        alpha = int(self.brightness * 255)
        star_surface = star_img.copy()
        star_surface.set_alpha(alpha)
        surface.blit(star_surface, self.pos)

class MiniGame:
    def __init__(self, location, data):
        self.location = location
        self.data = data
        self.question = f"What is the population of {location}?"
        if 'population' not in data:
            print(f"Warning: Population data missing for {location}. Using default values.")
            self.options = [str(random.randint(100000, 1000000)) for _ in range(4)]
            self.correct_answer = self.options[0]
        else:
            self.options = [str(int(data['population']) + random.randint(-100000, 100000)) 
                          for _ in range(3)]
            self.options.append(str(data['population']))
            self.correct_answer = str(data['population'])
        random.shuffle(self.options)
        self.selected_answer = None
        self.game_over = False

    def draw(self, screen):
        screen.fill((200, 200, 200))
        title = title_font.render(f"Mini-Game: {self.location}", True, BLACK)
        screen.blit(title, (screen_width // 2 - title.get_width() // 2, 50))

        question_surf = main_font.render(self.question, True, BLACK)
        screen.blit(question_surf, (screen_width // 2 - question_surf.get_width() // 2, 150))

        for i, option in enumerate(self.options):
            button_rect = pygame.Rect(screen_width // 4, 250 + i * 60, screen_width // 2, 50)
            color = GREEN if self.game_over and option == self.correct_answer else \
                   (RED if self.game_over and option == self.selected_answer else WHITE)
            pygame.draw.rect(screen, color, button_rect, border_radius=5)
            pygame.draw.rect(screen, BLACK, button_rect, 2, border_radius=5)
            option_text = main_font.render(option, True, BLACK)
            screen.blit(option_text, (button_rect.centerx - option_text.get_width() // 2,
                                    button_rect.centery - option_text.get_height() // 2))

        if self.game_over:
            result_text = "Correct!" if self.selected_answer == self.correct_answer else "Incorrect!"
            result_surf = title_font.render(result_text, True,
                                          GREEN if self.selected_answer == self.correct_answer else RED)
            screen.blit(result_surf, (screen_width // 2 - result_surf.get_width() // 2, 500))

            back_button = pygame.Rect(screen_width // 2 - 100, 600, 200, 50)
            pygame.draw.rect(screen, BLUE, back_button, border_radius=5)
            pygame.draw.rect(screen, BLACK, back_button, 2, border_radius=5)
            back_text = main_font.render("Back to Map", True, WHITE)
            screen.blit(back_text, (back_button.centerx - back_text.get_width() // 2,
                                  back_button.centery - back_text.get_height() // 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.game_over:
                for i, option in enumerate(self.options):
                    button_rect = pygame.Rect(screen_width // 4, 250 + i * 60, 
                                           screen_width // 2, 50)
                    if button_rect.collidepoint(event.pos):
                        self.selected_answer = option
                        self.game_over = True
                        break
            else:
                back_button = pygame.Rect(screen_width // 2 - 100, 600, 200, 50)
                if back_button.collidepoint(event.pos):
                    return True
        return False

class MapClass:
    def __init__(self, image, locations):
        self.original_image = image
        self.locations = locations
        self.offset = Vector2(0, 0)
        self.zoom = 1.0
        self.min_zoom = 1.0
        self.max_zoom = 3.0
        self.dragging = False
        self.drag_start = Vector2(0, 0)
        self.selected_location = None
        self.hover_location = None
        self.show_all_names = False
        self.stars = [Star((random.randint(0, screen_width), random.randint(0, screen_height // 2))) 
                     for _ in range(100)]
        self.time = 12
        self.particles = []
        self.mini_game = None
        self.show_instructions = False
        self.instruction_button = pygame.Rect(10, 10, 30, 30)
        self.fade_alpha = 255
        self.fading_in = True
        self.fading_out = False
        self.fade_speed = 5
        self.button_hover = False
        self.button_rect = None
        self.restart_sound = False

    def get_darkness(self):
        if 6 <= self.time < 18:
            return 0
        elif self.time < 6:
            return int(255 * (1 - self.time / 6))
        else:
            return int(255 * (self.time - 18) / 6)

    def update(self, dt):
        for star in self.stars:
            star.update(dt)
        self.time = (self.time + dt / 60) % 24
        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update()
            
        if self.fading_in:
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed)
            if self.fade_alpha <= 0:
                self.fading_in = False
        elif self.fading_out:
            self.fade_alpha = min(255, self.fade_alpha + self.fade_speed)
            if self.fade_alpha >= 255:
                self.start_mini_game(self.selected_location)
        
        if self.restart_sound:
            ambient_sound.play(-1)
            self.restart_sound = False

    def draw(self, screen):
        screen_size = Vector2(screen.get_size())
        aspect_ratio = self.original_image.get_width() / self.original_image.get_height()
        
        if screen_size.x / screen_size.y > aspect_ratio:
            base_size = Vector2(screen_size.y * aspect_ratio, screen_size.y)
        else:
            base_size = Vector2(screen_size.x, screen_size.x / aspect_ratio)
        
        map_size = base_size * self.zoom
        map_pos = (screen_size - map_size) / 2 + self.offset
        
        scaled_map = pygame.transform.smoothscale(self.original_image, 
                                                (int(map_size.x), int(map_size.y)))
        
        darkness = self.get_darkness()
        dark_surface = pygame.Surface(scaled_map.get_size()).convert_alpha()
        dark_surface.fill((0, 0, 0, darkness))
        scaled_map.blit(dark_surface, (0, 0))
        
        screen.blit(scaled_map, map_pos)

        if darkness > 100:
            for star in self.stars:
                star.draw(screen)

        for name, data in self.locations.items():
            if 'x' not in data or 'y' not in data:
                continue
            pixel_pos = map_pos + Vector2(data['x'] * map_size.x, data['y'] * map_size.y)
            self.draw_marker(screen, pixel_pos, name)
            if self.show_all_names or name == self.hover_location:
                self.draw_name_label(screen, name, pixel_pos)

        if self.selected_location:
            self.draw_info_bubble(screen, self.selected_location)

        for particle in self.particles:
            particle.draw(screen)

        time_text = main_font.render(f"{int(self.time):02d}:00", True, WHITE)
        screen.blit(time_text, (screen_size.x - time_text.get_width() - 20,
                               screen_size.y - time_text.get_height() - 20))

        pygame.draw.rect(screen, (200, 200, 200), self.instruction_button, border_radius=5)
        pygame.draw.rect(screen, BLACK, self.instruction_button, 2, border_radius=5)
        question_mark = main_font.render("?", True, BLACK)
        screen.blit(question_mark, (self.instruction_button.centerx - question_mark.get_width() // 2,
                                  self.instruction_button.centery - question_mark.get_height() // 2))

        if self.show_instructions:
            self.draw_instructions(screen)

        if self.fading_in or self.fading_out:
            fade_surface = pygame.Surface((screen_width, screen_height))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(self.fade_alpha)
            screen.blit(fade_surface, (0, 0))

        return map_pos, map_size

    def start_mini_game(self, location):
        ambient_sound.stop()
        
        if location.lower() == 'manila':
            from storyscreen_intramuros import OpeningSequence
            sequence = OpeningSequence()
            sequence.run()
            self.restart_sound = True
        elif location.lower() == 'ifugao':
            import BANAUE
            BANAUE.main()
            self.restart_sound = True
        else:
            self.mini_game = MiniGame(location, self.locations[location])
        
        self.current_state = 'MAP'
        self.fading_out = False

    def draw_marker(self, screen, pos, name):
        shadow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(shadow_surf, 10, 10, 10, SHADOW_COLOR)
        screen.blit(shadow_surf, (pos.x - 10, pos.y - 3))

        color = BLUE if name == self.selected_location else \
                (GREEN if name == self.hover_location else RED)
        pygame.gfxdraw.filled_trigon(screen, 
            int(pos.x), int(pos.y - 15),
            int(pos.x - 7), int(pos.y),
            int(pos.x + 7), int(pos.y),
            color)
        pygame.gfxdraw.aacircle(screen, int(pos.x), int(pos.y - 15), 7, color)
        pygame.gfxdraw.filled_circle(screen, int(pos.x), int(pos.y - 15), 7, color)
        pygame.gfxdraw.aacircle(screen, int(pos.x), int(pos.y - 15), 3, WHITE)
        pygame.gfxdraw.filled_circle(screen, int(pos.x), int(pos.y - 15), 3, WHITE)

    def draw_name_label(self, screen, name, pos):
        label = small_font.render(name, True, BLACK, WHITE)
        label_rect = label.get_rect(center=(pos.x, pos.y + 20))
        screen.blit(label, label_rect)

    def draw_info_bubble(self, screen, location):
        if location not in self.locations:
            return
        data = self.locations[location]
        screen_size = Vector2(screen.get_size())
        bubble_width, bubble_height = 300, 200
        
        bubble_pos = Vector2(screen_size.x - bubble_width - 20, 20)
        
        pygame.draw.rect(screen, BUBBLE_COLOR, (*bubble_pos, bubble_width, bubble_height), 
                        border_radius=10)
        pygame.draw.rect(screen, BLACK, (*bubble_pos, bubble_width, bubble_height), 2, 
                        border_radius=10)
        
        name_surf = main_font.render(location, True, BLACK)
        screen.blit(name_surf, (bubble_pos.x + 10, bubble_pos.y + 10))
        
        y_offset = 40
        for key, value in data.items():
            if key not in ['x', 'y']:
                text = f"{key.capitalize()}: {str(value)}"
                wrapped_text = self.wrap_text(text, small_font, bubble_width - 20)
                for line in wrapped_text:
                    text_surf = small_font.render(line, True, BLACK)
                    screen.blit(text_surf, (bubble_pos.x + 10, bubble_pos.y + y_offset))
                    y_offset += 20

        button_rect = pygame.Rect(bubble_pos.x + 10, bubble_pos.y + bubble_height - 40, 
                                bubble_width - 20, 30)
        self.button_rect = button_rect
        
        button_color = (34, 197, 94) if self.button_hover else GREEN
        pygame.draw.rect(screen, button_color, button_rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, button_rect, 2, border_radius=5)
        
        button_text = small_font.render("Play Mini-Game", True, WHITE if self.button_hover else BLACK)
        screen.blit(button_text, (button_rect.centerx - button_text.get_width() // 2,
                                button_rect.centery - button_text.get_height() // 2))

    def draw_instructions(self, screen):
        instructions = [
            "LMB: Select/Drag",
            "Scroll: Zoom",
            "Hover: Show names",
            "SPACE: Show all names",
            "H: Hide/Show help",
            "ESC: Exit"
        ]
        
        line_height = instruction_font.get_linesize()
        padding = 10
        panel_width = 200
        panel_height = len(instructions) * line_height + 2 * padding
        
        instruction_surface = pygame.Surface((panel_width, panel_height))
        instruction_surface.set_alpha(230)
        instruction_surface.fill((30, 30, 30))
        
        for i, instruction in enumerate(instructions):
            text = instruction_font.render(instruction, True, WHITE)
            instruction_surface.blit(text, (padding, padding + i * line_height))
        
        screen.blit(instruction_surface, (50, 50))
        pygame.draw.rect(screen, WHITE, (50, 50, panel_width, panel_height), 2)

    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def handle_event(self, event, map_pos, map_size):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.instruction_button.collidepoint(event.pos):
                    self.show_instructions = not self.show_instructions
                    click_sound.play()
                    return
                    
                if self.button_rect and self.button_rect.collidepoint(event.pos):
                    click_sound.play()
                    self.fading_out = True
                    return
                    
                self.dragging = True
                self.drag_start = Vector2(event.pos)
                clicked_location = self.check_click(event.pos, map_pos, map_size)
                if clicked_location:
                    click_sound.play()
                    self.selected_location = clicked_location
                    for _ in range(20):
                        self.particles.append(Particle(event.pos, RED))
            elif event.button == 4:
                self.zoom = min(self.max_zoom, self.zoom * 1.1)
            elif event.button == 5:
                self.zoom = max(self.min_zoom, self.zoom / 1.1)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.button_rect:
                self.button_hover = self.button_rect.collidepoint(event.pos)
                
            if self.dragging:
                self.offset += Vector2(event.pos) - self.drag_start
                self.drag_start = Vector2(event.pos)
            self.hover_location = self.check_click(event.pos, map_pos, map_size)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:
                self.show_instructions = not self.show_instructions
            elif event.key == pygame.K_SPACE:
                self.show_all_names = not self.show_all_names

    def check_click(self, pos, map_pos, map_size):
        for name, data in self.locations.items():
            pixel_pos = map_pos + Vector2(data['x'] * map_size.x, data['y'] * map_size.y)
            if (Vector2(pos) - pixel_pos).length_squared() < 225:
                return name
        return None

def main():
    if not locations:
        print("No valid location data. Exiting.")
        return

    clock = pygame.time.Clock()
    map_instance = MapClass(original_map, locations)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        screen.fill(SEA_COLOR)
        
        if map_instance.mini_game:
            map_instance.mini_game.draw(screen)
        else:
            map_instance.update(dt)
            map_pos, map_size = map_instance.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ambient_sound.stop()
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                ambient_sound.stop()
                running = False
            elif map_instance.mini_game:
                if map_instance.mini_game.handle_event(event):
                    map_instance.mini_game = None
                    ambient_sound.play(-1)  # Restart ambient sound when returning to map
            else:
                map_instance.handle_event(event, map_pos, map_size)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()