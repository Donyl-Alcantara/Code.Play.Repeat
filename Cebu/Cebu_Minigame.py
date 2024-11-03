import pygame
import sys
import random
from sprites1 import Player, Guard, Direction, GuardState, AlertIndicator

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRID_COLOR = (150, 150, 150)
BG_COLOR = (30, 30, 45)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Patintero")
        self.clock = pygame.time.Clock()
        
        # Calculate grid dimensions with narrower width
        self.grid_margin_x = int(SCREEN_WIDTH * 0.3)  # Increased margin for narrower field
        self.grid_margin_y = 100
        self.grid_width = SCREEN_WIDTH - (2 * self.grid_margin_x)
        
        # Adjust grid height to remove empty spaces
        self.num_lines = 4
        self.line_spacing = (SCREEN_HEIGHT - (2 * self.grid_margin_y)) // (self.num_lines - 1)
        self.grid_height = self.line_spacing * (self.num_lines - 1)
        
        # Create grid boundary rect
        self.grid_bounds = pygame.Rect(
            self.grid_margin_x,
            self.grid_margin_y,
            self.grid_width,
            self.grid_height
        )
        
        self.reset_game()

    def reset_game(self):
        self.running = True
        self.won = False
        self.lost = False
        
        self.all_sprites = pygame.sprite.Group()
        self.guards = pygame.sprite.Group()
        
        # Adjusted player spawn position to be lower and safer
        spawn_x = SCREEN_WIDTH // 2
        spawn_y = self.grid_margin_y + self.grid_height + 80  # Increased from +40 to +80
        self.player = Player(spawn_x, spawn_y)
        self.all_sprites.add(self.player)
        
        self.create_guards()

    def create_guards(self):
        # Create horizontal guards with more varied and challenging patterns
        for i in range(self.num_lines):
            y_pos = self.grid_margin_y + (self.line_spacing * i)
            # More varied phase offsets for less predictable movement
            phase_offset = random.uniform(0, 3)
            # Alternate initial directions for more challenge
            initial_direction = 1 if i % 2 == 0 else -1
            
            guard = Guard(
                self.grid_margin_x + (20 if initial_direction == 1 else self.grid_width - 20),
                y_pos,
                Direction.HORIZONTAL,
                self.grid_width - 40,
                line_y=y_pos,
                phase_offset=phase_offset
            )
            guard.patrol_direction.x = initial_direction  # Set initial direction
            self.all_sprites.add(guard)
            self.guards.add(guard)
        
        # Adjusted vertical guard for better challenge
        mid_row = 2
        y_pos = self.grid_margin_y + (self.line_spacing * mid_row)
        x_pos = SCREEN_WIDTH // 2
        bottom_line_y = y_pos + self.line_spacing
        
        vertical_guard = Guard(
            x_pos,
            y_pos,
            Direction.VERTICAL,
            self.line_spacing,
            line_y=bottom_line_y,
            phase_offset=random.uniform(0, 2)
        )
        self.all_sprites.add(vertical_guard)
        self.guards.add(vertical_guard)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r and (self.won or self.lost):
                    self.reset_game()

    def update(self):
        if not (self.won or self.lost):
            keys = pygame.key.get_pressed()
            self.player.move(keys, SCREEN_WIDTH, SCREEN_HEIGHT, self.grid_bounds)
            self.guards.update(self.player, self.grid_bounds)
            
            # Check both direct collisions and tag range
            player_pos = pygame.math.Vector2(self.player.rect.center)
            for guard in self.guards:
                if guard.can_tag_player(player_pos):
                    self.lost = True
                    break
            
            # Win condition: reach the top of the grid
            if (self.player.rect.centery <= self.grid_margin_y + 20 and  # Player is near top
                self.grid_margin_x <= self.player.rect.centerx <= self.grid_margin_x + self.grid_width):  # Within grid bounds
                self.won = True

    def draw_grid(self):
        # Draw horizontal lines
        for i in range(self.num_lines):
            y_pos = self.grid_margin_y + (self.line_spacing * i)
            pygame.draw.line(
                self.screen,
                GRID_COLOR,
                (self.grid_margin_x, y_pos),
                (self.grid_margin_x + self.grid_width, y_pos),
                2
            )
        
        # Draw vertical boundaries
        pygame.draw.line(
            self.screen,
            GRID_COLOR,
            (self.grid_margin_x, self.grid_margin_y),
            (self.grid_margin_x, self.grid_margin_y + self.grid_height),
            2
        )
        pygame.draw.line(
            self.screen,
            GRID_COLOR,
            (self.grid_margin_x + self.grid_width, self.grid_margin_y),
            (self.grid_margin_x + self.grid_width, self.grid_margin_y + self.grid_height),
            2
        )
        
        # Draw center vertical line
        mid_x = SCREEN_WIDTH // 2
        pygame.draw.line(
            self.screen,
            GRID_COLOR,
            (mid_x, self.grid_margin_y),
            (mid_x, self.grid_margin_y + self.grid_height),
            2
        )

    def draw(self):
        self.screen.fill(BG_COLOR)
        self.draw_grid()
        
        # Draw guard ranges first (under sprites)
        for sprite in self.guards:
            sprite.draw(self.screen) 
            
        self.all_sprites.draw(self.screen)
        
        if self.won:
            self.draw_game_over("Panalo! Press R to restart", WHITE)
        elif self.lost:
            self.draw_game_over("Talo! Press R to restart", RED)
        else:
            # Draw simple instructions
            font = pygame.font.Font(None, 26)
            instructions = font.render("Use WASD to move | Reach the top to win | Avoid guards and their reach", True, WHITE)
            self.screen.blit(instructions, (20, SCREEN_HEIGHT - 30))
        
        pygame.display.flip()

    def draw_game_over(self, message, color):
        # Add semi-transparent overlay
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 128))
        self.screen.blit(surface, (0, 0))
        
        # Draw message
        font = pygame.font.Font(None, 74)
        text = font.render(message, True, color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

if __name__ == '__main__':
    game = Game()
    game.run()