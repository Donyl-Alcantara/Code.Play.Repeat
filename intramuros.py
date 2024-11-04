import pygame
from random import randint
from sprites import *
from PIL import Image, ImageSequence
import os
import subprocess
import sys

# Game Class
class Game:
    def __init__(self):
        # Setup
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Intramuros")
        self.clock = pygame.time.Clock()
        self.running = True
        self.score = 0
        self.game_over = False
        self.player_won = False
        self.start_delay = 3
        self.start_timer = 0
        self.game_started = False
        self.restart_prompt_visible = False
        self.restart_prompt_timer = 0
        self.restart_prompt_interval = 1.0  # Blink interval in seconds
        self.transitioning_to_map = False

        # Sprite groups
        self.all_sprites = AllSprites(self)
        self.collision_sprites = pygame.sprite.Group()
        self.collectible_sprites = pygame.sprite.Group()
        self.ghost_sprites = pygame.sprite.Group()
        self.win_zone_sprites = pygame.sprite.Group()

        # Game initialization
        self.initialize_game()

        # Load fonts
        try:
            self.font = pygame.font.Font('font/pixel_font.ttf', 16)
            self.popup_font = pygame.font.Font('font/pixel_font.ttf', 20)
        except:
            self.main_font = pygame.font.SysFont('helvetica', 36)
            self.popup_font = pygame.font.SysFont('helvetica', 48)

        # Load sounds
        pygame.mixer.init()
        self.catch_sound = pygame.mixer.Sound("audio//jumpscare.wav")
        self.win_sound = pygame.mixer.Sound("audio//win.wav")
        self.win_sound.set_volume(0.5)
        self.collectall_sound = pygame.mixer.Sound("audio//collectall.wav")
        self.collectall_sound.set_volume(0.3)
        self.pickup_sound = pygame.mixer.Sound("audio//pickup.wav")
        self.pickup_sound.set_volume(0.1)
        self.background_music = "audio//bg.mp3"
        self.game_over_music = "audio//game over.mp3"
        self.victory_music = "audio//purity.mp3"
        pygame.mixer.music.load(self.background_music)
        pygame.mixer.music.set_volume(0.1)

        # Load images
        self.win_img_load = pygame.image.load('img//env//agimat.png')
        self.win_img = pygame.transform.scale(self.win_img_load, (69, 69))
        self.background = pygame.image.load('img//env//bgdark.png').convert()
        self.background_win = pygame.image.load('img//env//bglight.png').convert()
        self.background_current = self.background

        # Load gif frames for jumpscare
        self.caught_frames = self.load_gif_frames("img//misc//jumpscare.gif", scale=1)
        self.caught_animation = AnimatedSprite(self.caught_frames, 0, 0, scale=1)

        # Jumpscare timming
        self.jumpscare_duration = 1  # Duration in seconds
        self.jumpscare_timer = 0
        self.jumpscare_active = False
        self.game_over_screen_active = False

    def initialize_game(self):
        # Clear existing sprites
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.collectible_sprites.empty()
        self.ghost_sprites.empty()
        self.win_zone_sprites.empty()

        # Reset background music
        self.background_music = "audio//bg.mp3"
        pygame.mixer.music.stop()
        pygame.mixer.music.load(self.background_music)
        pygame.mixer.music.set_volume(0.1)

        # Reset jumpscare state
        self.jumpscare_active = False
        self.jumpscare_timer = 0
        self.game_over_screen_active = False
        self.caught_frames = self.load_gif_frames("img//misc//jumpscare.gif", scale=1)
        self.caught_animation = AnimatedSprite(self.caught_frames, 0, 0, scale=1)

        # Reset game state
        self.background = pygame.image.load('img//env//bgdark.png').convert()
        self.background_current = self.background
        self.score = 0
        self.game_over = False
        self.player_won = False
        self.start_timer = 0
        self.game_started = False
        self.restart_prompt_visible = False
        self.restart_prompt_timer = 0
        self.bg_music_playing = False

        # Define and create game boundary
        self.game_area = {
            'left': 0,
            'right': int(WIDTH * 1.5),  # Make play area wider than screen
            'top': 0,
            'bottom': int(HEIGHT * 1.5)  # Make play area taller than screen
        }
        self.create_bounds()
        self.all_sprites.set_boundaries(self.game_area) # For camera

        # Spawn Player
        player_start_x = self.game_area['right'] // 2
        player_start_y = self.game_area['bottom'] // 2
        self.player = Player((player_start_x, player_start_y),
                             self.all_sprites,
                             self.collision_sprites,
                             self.collectible_sprites)
        self.player.can_move = False

        # Spawn game elements
        self.total_artifacts = 15
        self.spawn_blocks()
        self.spawn_collectibles()
        self.collectall_sound_played = False

        # Create win zone
        self.win_zone = WinZone((self.game_area['right'] // 2, self.game_area['bottom'] // 2),
                                (200, 200), (self.all_sprites, self.win_zone_sprites))

        # Spawn ghost
        self.min_ghost_spawn_distance = 300
        self.spawn_ghosts(num_ghosts=5)

        # Win zone state
        self.in_win_zone = False
        self.showing_win_hint = False

    def create_bounds(self):
        wall_thickness = 64  # Thickness of boundary walls

        # Create the boundary walls
        boundaries = [
            # Left wall
            (self.game_area['left'] - wall_thickness, self.game_area['top'],
             wall_thickness, self.game_area['bottom'] - self.game_area['top']),
            # Right wall
            (self.game_area['right'], self.game_area['top'],
             wall_thickness, self.game_area['bottom'] - self.game_area['top']),
            # Top wall
            (self.game_area['left'] - wall_thickness, self.game_area['top'] - wall_thickness,
             self.game_area['right'] - self.game_area['left'] + wall_thickness * 2, wall_thickness),
            # Bottom wall
            (self.game_area['left'] - wall_thickness, self.game_area['bottom'],
             self.game_area['right'] - self.game_area['left'] + wall_thickness * 2, wall_thickness)
        ]

        # Create each boundary wall
        for boundary in boundaries:
            Boundary((boundary[0], boundary[1]),
                     (boundary[2], boundary[3]),
                     (self.all_sprites, self.collision_sprites))

    def get_safe_ghost_spawn(self):
        """Generate a spawn position that's far enough from the player and within bounds"""
        while True:
            # Generate random position
            spawn_x = randint(self.game_area['left'], self.game_area['right'])
            spawn_y = randint(self.game_area['top'], self.game_area['bottom'])

            # Calculate distance to player
            player_pos = pygame.math.Vector2(self.player.rect.center)
            spawn_pos = pygame.math.Vector2(spawn_x, spawn_y)
            distance = (spawn_pos - player_pos).length()

            # Check if position is far enough from player
            if distance >= self.min_ghost_spawn_distance:
                # Optional: Check if spawn point is not inside a wall
                test_rect = pygame.Rect(spawn_x - 15, spawn_y - 15, 30, 30)
                collision = any(sprite.rect.colliderect(test_rect)
                                for sprite in self.collision_sprites)

                if not collision:
                    return spawn_x, spawn_y

    def spawn_ghosts(self, num_ghosts=1):
        """Spawn multiple ghosts in safe locations"""
        for _ in range(num_ghosts):
            spawn_x, spawn_y = self.get_safe_ghost_spawn()
            ghost = Ghost((spawn_x, spawn_y),
                          (self.all_sprites, self.ghost_sprites),
                          self.player,
                          self.collision_sprites)
            ghost.set_win_zone(self.win_zone)

    def spawn_collectibles(self):
        """Spawn collectibles within game boundaries and not on top of blocks"""
        attempts_per_collectible = 5  # Maximum attempts to find a valid spot

        for _ in range(self.total_artifacts):
            placed = False
            attempts = 0

            while not placed and attempts < attempts_per_collectible:
                # Generate random position
                x = randint(self.game_area['left'] + 32, self.game_area['right'] - 32)
                y = randint(self.game_area['top'] + 32, self.game_area['bottom'] - 32)

                # Create a test rect for collision checking
                test_rect = pygame.Rect(x - 10, y - 10, 20, 20)  # Size matches collectible

                # Check if this position collides with any blocks
                collision = any(sprite.rect.colliderect(test_rect)
                                for sprite in self.collision_sprites)
                if not collision:
                    # If no collision, place the collectible
                    Collectibles((x, y), (self.all_sprites, self.collectible_sprites))
                    placed = True
                attempts += 1
            if not placed:
                print(f"Warning: Could not place collectible after {attempts_per_collectible} attempts")

    def spawn_blocks(self):
        """Spawn blocks within game boundaries"""
        for _ in range(40):
            x = randint(self.game_area['left'] + 64, self.game_area['right'] - 64)
            y = randint(self.game_area['top'] + 64, self.game_area['bottom'] - 64)
            w, h = randint(32, 80), randint(32, 80)
            Blocks((x, y), (w, h),
                  (self.all_sprites, self.collision_sprites))

    def load_gif_frames(self, gif_path, scale=1):
        frames = []
        with Image.open(gif_path) as gif:
            for frame in ImageSequence.Iterator(gif):
                frame_rgba = frame.convert("RGBA")
                size = frame_rgba.size
                new_size = (int(size[0] * scale), int(size[1] * scale))
                frame_rgba = frame_rgba.resize(new_size, Image.LANCZOS)
                pygame_image = pygame.image.fromstring(
                    frame_rgba.tobytes(), frame_rgba.size, "RGBA"
                ).convert_alpha()
                frames.append(pygame_image)
        return frames

    def run(self):
        while self.running:
            # Delta time
            dt = self.clock.tick() / 1000

            # Event Handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.player_won:
                        self.transition_to_map()

            if not self.bg_music_playing:
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(0.1)
                self.bg_music_playing = True

            if self.game_over:
                self.all_sprites.draw(self.player.rect.center)
                self.handle_game_over(dt)
                self.restart_key()
            elif self.player_won:
                # Draw purified bg
                victory_pos = self.all_sprites.offset
                self.screen.blit(self.background_current, victory_pos)

                # Keep assets updating
                self.all_sprites.update(dt)
                self.all_sprites.draw(self.player.rect.center)

                self.handle_win_transition()
                self.win_text = self.font.render("You have purified the museum!", True, WHITE)
                self.screen.blit(self.win_text, (WIDTH // 4 + 100, HEIGHT // 2 - 150))
                self.screen.blit(self.win_img, (WIDTH // 4 + 300, HEIGHT // 4 - 100))
                
                # Update the prompt blink timer
                self.restart_prompt_timer += dt
                if self.restart_prompt_timer >= self.restart_prompt_interval:
                    self.restart_prompt_timer = 0
                    self.restart_prompt_visible = not self.restart_prompt_visible

                # Draw blinking map transition prompt
                if self.restart_prompt_visible:
                    transition_text = self.font.render("Press SPACE to Access the Map", True, WHITE)
                    transition_rect = transition_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
                    self.screen.blit(transition_text, transition_rect)

            else:
                # Game completion loop
                if not self.game_started:
                    self.start_timer += dt
                    if self.start_timer >= self.start_delay:
                        self.game_started = True
                        self.player.can_move = True
                        for ghost in self.ghost_sprites:
                            ghost.start_moving()

                # Update game
                self.all_sprites.update(dt)
                self.all_sprites.draw(self.player.rect.center)
                self.player.update(dt)
                collected = self.player.collectible()
                self.score += collected
                if collected > 0:
                    self.pickup_sound.play()

                # Check for player progress
                self.check_win_zone()
                self.win_input()
                self.check_game_over()

                # Draw UI elements
                self.score_text = self.font.render(f"Artifacts Obtained: {self.score}/{self.total_artifacts}", True, WHITE)
                self.screen.blit(self.score_text, (10, 10))
                self.player.draw_stamina_bar(self.screen)
                self.draw_win_hint()

                if self.score == self.total_artifacts and not self.collectall_sound_played:
                    self.collectall_sound.play()
                    self.collectall_sound_played = True

                # Draw countdown timer
                if not self.game_started:
                    time_left = max(0, self.start_delay - self.start_timer)
                    countdown_text = self.font.render(f"Starts in {time_left:.1f}", True, WHITE)
                    text_rect = countdown_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
                    self.screen.blit(countdown_text, text_rect)

            pygame.display.flip()

        pygame.quit()

    def transition_to_map(self):
        pygame.quit()
        map_path = os.path.join('map.py')
        if os.path.exists(map_path):
            try:
                # Start the map.py script
                if sys.platform == 'win32':
                    python_executable = 'python'
                else:
                    python_executable = 'python3'
                subprocess.Popen([python_executable, map_path])
                self.running = False
            except Exception as e:
                print(f"Error launching map: {e}")
        else:
            print(f"Map file not found at: {map_path}")

    def check_win_zone(self):
        # Check if player is in win zone
        if self.game_started:
            if pygame.sprite.spritecollide(self.player, self.win_zone_sprites, False):
                if not self.in_win_zone:  # Just entered the zone
                    self.in_win_zone = True
                    self.showing_win_hint = True
            else:
                self.in_win_zone = False
                self.showing_win_hint = False

    def draw_win_hint(self):
        if self.showing_win_hint:
            # Create semi-transparent background for popup
            popup_surface = pygame.Surface((900, 80))
            popup_surface.fill((0, 0, 0))
            popup_surface.set_alpha(64)

            # Position popup in center of screen
            popup_rect = popup_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150))
            self.screen.blit(popup_surface, popup_rect)

            # Draw prompt text
            if self.score >= self.total_artifacts:
                prompt_text = "Press F to craft the Agimat"
            else:
                prompt_text = f"Collect all Agimat shards first! ({self.score}/{self.total_artifacts})"

            text_surface = self.popup_font.render(prompt_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150))
            self.screen.blit(text_surface, text_rect)

    def win_input(self):
        keys = pygame.key.get_pressed()
        if self.in_win_zone and keys[pygame.K_f] and self.score >= self.total_artifacts:
            self.trigger_win()
            self.showing_win_hint = False

    def trigger_win(self):
        self.win_sound.play()
        pygame.mixer.music.stop()
        self.bg_music_playing = False
        pygame.mixer.music.load(self.victory_music)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(1)
        self.player_won = True
        self.background_current = self.background_win
        for ghost in self.ghost_sprites:
            ghost.kill()
        self.ghost_sprites.empty()

    def check_game_over(self):
        if not self.in_win_zone:
            if pygame.sprite.spritecollide(self.player, self.ghost_sprites, True):
                self.game_over = True
                pygame.mixer.music.stop()
                self.bg_music_playing = False
                self.catch_sound.play()
                self.caught_animation.start_animation()
                self.player.can_move = False
                self.jumpscare_active = True
                self.game_over_screen_active = False

    def handle_game_over(self, dt):
        if self.jumpscare_active:
            # Update jumpscare animation
            self.caught_animation.update()
            self.screen.blit(self.caught_animation.image, (0, -100))

            # Update timer
            self.jumpscare_timer += dt

            # Check if jumpscare duration is complete
            if self.jumpscare_timer >= self.jumpscare_duration:
                self.jumpscare_active = False
                self.game_over_screen_active = True
                # Start game over music
                pygame.mixer.music.load(self.game_over_music)
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(0.1)

        elif self.game_over_screen_active:
            self.screen.fill(BLACK)
            self.draw_game_over_screen(dt)

    def draw_game_over_screen(self, dt):
        # Update the restart prompt blink timer
        self.restart_prompt_timer += dt
        if self.restart_prompt_timer >= self.restart_prompt_interval:
            self.restart_prompt_timer = 0
            self.restart_prompt_visible = not self.restart_prompt_visible

        # Draw game over text
        game_over_font = pygame.font.Font('font/pixel_font.ttf', 64)
        game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        self.screen.blit(game_over_text, game_over_rect)

        # Draw score
        score_text = self.font.render(f"Final Score: {self.score}/{self.total_artifacts}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        self.screen.blit(score_text, score_rect)

        # Draw blinking restart prompt
        if self.restart_prompt_visible:
            restart_text = self.font.render("Press ENTER to Restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
            self.screen.blit(restart_text, restart_rect)

    def restart_key(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            # Reset game state and restart
            self.initialize_game()

    def handle_win_transition(self):
        pass  # You can add any additional transition effects here if desired

if __name__ == '__main__':
    game = Game()
    game.run()