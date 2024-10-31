import pygame
from random import randint
from sprites import *
from PIL import Image, ImageSequence

# Game Class
class Game:
    def __init__(self):
        # Setup
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Intramuros Demo 2")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 36)
        self.score = 0
        self.game_over = False
        self.player_won = False
        self.start_delay = 3
        self.start_timer = 0
        self.game_started = False

        # Sprite groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.collectible_sprites = pygame.sprite.Group()
        self.ghost_sprites = pygame.sprite.Group()
        self.win_zone_sprites = pygame.sprite.Group()

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

        # Create win zone
        self.win_zone = WinZone((self.game_area['right'] // 2, self.game_area['bottom'] // 2 + 100), (100, 100), (self.all_sprites, self.win_zone_sprites))

        # Spawn ghost
        self.min_ghost_spawn_distance = 300
        self.spawn_ghosts(num_ghosts=5)

        # Win zone state
        self.in_win_zone = False
        self.showing_win_prompt = False
        self.popup_font = pygame.font.Font(None, 48)

        # Load sounds
        pygame.mixer.init()
        self.catch_sound = pygame.mixer.Sound("audio//jumpscare.wav")
        self.win_sound = pygame.mixer.Sound("audio//i win.mp3")
        pygame.mixer.music.load("audio//bg.mp3")
        pygame.mixer.music.set_volume(0.1)
        self.bg_music_playing = False

        # Load images
        self.win_img = pygame.image.load('img//misc//win.png')

        # Load gif frames for jumpscare
        self.caught_frames = self.load_gif_frames("img//misc//jumpscare.gif", scale=2.5)
        self.caught_animation = AnimatedSprite(self.caught_frames, 0, 0, scale=2.5)

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

            # Draw spawn radius while loading
            """
            pygame.draw.circle(self.screen, 
                             (255, 0, 0), 
                             self.player.rect.center,
                             self.min_ghost_spawn_distance,
                             1)
            pygame.display.flip()
            """

    def spawn_collectibles(self):
        """Spawn collectibles within game boundaries"""
        for _ in range(self.total_artifacts):
            x = randint(self.game_area['left'] + 32, self.game_area['right'] - 32)
            y = randint(self.game_area['top'] + 32, self.game_area['bottom'] - 32)
            Collectibles((x, y), (20, 20),
                        (self.all_sprites, self.collectible_sprites))

    def spawn_blocks(self):
        """Spawn blocks within game boundaries"""
        for _ in range(20):
            x = randint(self.game_area['left'] + 64, self.game_area['right'] - 64)
            y = randint(self.game_area['top'] + 64, self.game_area['bottom'] - 64)
            w, h = randint(32, 64), randint(32, 64)
            Blocks((x, y), (w, h),
                  (self.all_sprites, self.collision_sprites))

    # GIF loader
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
        # Start background music when game starts
        if not self.bg_music_playing:
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(0.1)
            self.bg_music_playing = True

        while self.running:
            # Delta time
            dt = self.clock.tick() / 1000

            # Event Handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # Game completion loop
            if not self.game_over and not self.player_won:
                # Update start timer
                if not self.game_started:
                    self.start_timer += dt
                    if self.start_timer >= self.start_delay:
                        self.game_started = True
                        self.player.can_move = True  # Enable player movement
                        for ghost in self.ghost_sprites:
                            ghost.start_moving()
                # Update game
                self.all_sprites.update(dt)
                collected = self.player.collectible()  # Get the number of collected items
                self.score += collected  # Update the score

                # Check for player progress
                self.check_win_zone()
                self.win_input()
                self.check_game_over()

            # Update sprites
            self.all_sprites.update(dt)
            self.player.update(dt)

            # Draw sprites
            self.screen.fill(BLACK)
            self.all_sprites.draw(self.player.rect.center)

            self.score_text = self.font.render(f"Artifacts Obtained: {self.score}/{self.total_artifacts}", True, WHITE)
            self.screen.blit(self.score_text, (10, 10))

            self.draw_win_prompt()

            # Draw countdown timer
            if not self.game_started:
                time_left = max(0, self.start_delay - self.start_timer)
                countdown_text = self.font.render(f"Starts in {time_left:.1f}", True, WHITE)
                text_rect = countdown_text.get_rect(center=(WIDTH//2, HEIGHT//4))
                self.screen.blit(countdown_text, text_rect)

            """
            # Draw player hitbox
            hitbox_draw_pos = self.player.hitbox_rect.topleft + self.all_sprites.offset # adjust position to cam offset
            pygame.draw.rect(self.screen, RED, (*hitbox_draw_pos, *self.player.hitbox_rect.size), 2)
            """

            if self.player_won:
                if self.bg_music_playing:
                    pygame.mixer.music.stop()
                    self.bg_music_playing = False
                self.win_text = self.font.render("You have purified the museum!", True, WHITE)
                self.screen.blit(self.win_text, (WIDTH//4 + 150, HEIGHT//2-100))
                self.screen.blit(self.win_img,(WIDTH//4+100,HEIGHT//4+100))

            if self.game_over:
                if self.bg_music_playing:
                    pygame.mixer.music.stop()
                    self.bg_music_playing = False
                self.caught_animation.update()
                self.screen.blit(self.caught_animation.image, (0, 0))

            pygame.display.flip()

        pygame.quit()

    def check_win_zone(self):
        # Check if player is in win zone
        if pygame.sprite.spritecollide(self.player, self.win_zone_sprites, False):
            if not self.in_win_zone:  # Just entered the zone
                self.in_win_zone = True
                self.showing_win_prompt = True
        else:
            self.in_win_zone = False
            self.showing_win_prompt = False

    def win_input(self):
        keys = pygame.key.get_pressed()
        if self.in_win_zone and keys[pygame.K_f] and self.score >= self.total_artifacts:
            self.trigger_win()
            self.showing_win_prompt = False

    def trigger_win(self):
        self.win_sound.play()
        self.player_won = True
        for ghost in self.ghost_sprites:
            ghost.stop_moving()

    def draw_win_prompt(self):
        if self.showing_win_prompt:
            # Create semi-transparent background for popup
            popup_surface = pygame.Surface((600, 100))
            popup_surface.fill((0, 0, 0))
            popup_surface.set_alpha(128)

            # Position popup in center of screen
            popup_rect = popup_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(popup_surface, popup_rect)

            # Draw prompt text
            if self.score >= self.total_artifacts:
                prompt_text = "Press F to craft the Agimat"
            else:
                prompt_text = f"Collect all Agimat shards first! ({self.score}/{self.total_artifacts})"

            text_surface = self.popup_font.render(prompt_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(text_surface, text_rect)

    def check_game_over(self):
        if pygame.sprite.spritecollide(self.player, self.ghost_sprites, True):
            self.game_over = True
            pygame.mixer.music.unload()
            self.catch_sound.play()
            self.caught_animation.start_animation()
            self.player.speed = 0

    """
    kept for archive purposes
    def check_win_condition(self):
        if self.score >= self.total_artifacts:
            self.win_sound.play()
            self.player_won = True
            for ghost in self.ghost_sprites:
                ghost.stop_moving()
    """

if __name__ == '__main__':
    game = Game()
    game.run()