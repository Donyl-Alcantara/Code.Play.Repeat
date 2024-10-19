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

        # Sprite groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.collectible_sprites = pygame.sprite.Group()
        self.ghost_sprites = pygame.sprite.Group()

        # Sprites
        self.player = Player((WIDTH//2,HEIGHT//2), self.all_sprites, self.collision_sprites, self.collectible_sprites)

        for block in range(20): # spawn blocks (temporary, will replace with sprites)
            x, y = randint(0, WIDTH), randint(0, HEIGHT)
            w, h = randint(32, 94), randint(32, 94)
            CollisionSprite((x, y), (w, h), (self.all_sprites, self.collision_sprites))

        self.score = 0
        self.total_artifacts = 15
        for artifact in range(self.total_artifacts):
            x, y = randint(0, WIDTH), randint(0, HEIGHT)
            Collectibles((x, y), (20, 20), (self.all_sprites, self.collectible_sprites))

        # Add ghost
        self.ghost = Ghost((randint(0, WIDTH), randint(0, HEIGHT)), (self.all_sprites, self.ghost_sprites), self.player)

        # Load sounds
        pygame.mixer.init()
        self.catch_sound = pygame.mixer.Sound(join('audio',"jumpscare.wav"))

        # Load images
        self.win_img = pygame.image.load(join('img', 'win.png'))

        # Load gif frames for jumpscare
        self.caught_frames = self.load_gif_frames(join("fnaf-jrs.gif"), scale=2.5)
        self.caught_animation = AnimatedSprite(self.caught_frames, 0, 0, scale=2.5)

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

            # Event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            if not self.game_over and not self.player_won:
                # Update game
                self.all_sprites.update(dt)
                collected = self.player.update(dt)  # Get the number of collected items
                self.score += collected  # Update the score
                self.check_win_condition()
                self.check_game_over()

            if self.player_won:
                self.win_text = self.font.render("You have purified the museum", True, GREEN)

            # Update game
            self.all_sprites.update(dt)
            self.player.update(dt)

            # Draw sprites
            self.screen.fill(WHITE)
            self.all_sprites.draw(self.player.rect.center)

            self.score_text = self.font.render(f"Artifacts Obtained: {self.score}/{self.total_artifacts}", True, BLACK)
            self.screen.blit(self.score_text, (10, 10))

            # Draw player hitbox
            hitbox_draw_pos = self.player.hitbox_rect.topleft + self.all_sprites.offset # adjust position to cam offset
            #pygame.draw.rect(self.screen, RED, (*hitbox_draw_pos, *self.player.hitbox_rect.size), 2) #remove hashtag to activate

            if self.game_over:
                self.caught_animation.update()
                self.screen.blit(self.caught_animation.image, (0, 0))

            pygame.display.flip()

        pygame.quit()

    def check_collisions(self):
        # Check for artifact collection
        collected = pygame.sprite.spritecollide(self.player, self.collectible_sprites, True)
        self.score += len(collected)

    def check_win_condition(self):
        if self.score >= self.total_artifacts:
            self.player_won = True

    def check_game_over(self):
        if pygame.sprite.spritecollide(self.player, self.ghost_sprites, False):
            self.game_over = True
            self.catch_sound.play()
            self.caught_animation.start_animation()

if __name__ == '__main__':
    game = Game()
    game.run()


"""

# Boundary settings
BOUNDARY_SIZE = 2000
boundary = pygame.Rect(-BOUNDARY_SIZE//2, -BOUNDARY_SIZE//2, BOUNDARY_SIZE, BOUNDARY_SIZE)
   
    # Boundary collision
    player_rect.clamp_ip(boundary)

    # Draw boundary
    pygame.draw.rect(screen, BLUE, boundary.move(-camera_x, -camera_y), 2)

"""