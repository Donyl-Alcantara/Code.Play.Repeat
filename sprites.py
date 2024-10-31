import pygame.draw
import random
import math
from settings import *
class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collisions, collectibles):
        super().__init__(groups)
        self.image = pygame.image.load('img//player//adventurer-idle-00.png').convert_alpha() # replace w animated sprite
        self.rect = self.image.get_rect(center = pos)
        self.hitbox_rect = self.rect.inflate(-30, 0)
        self.hitbox_rect.center = self.rect.center

        # Movement
        self.pos = pygame.math.Vector2(self.hitbox_rect.center)
        self.direction = pygame.Vector2()
        self.speed = 150
        self.can_move = False

        # Object interaction
        self.collision_sprites = collisions
        self.collectible_sprites = collectibles

    # Movement input
    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction

    # Movement mechanics
    def move(self, dt):
        # Calculate the movement
        movement = self.direction * self.speed * dt

        # Move horizontally
        self.pos.x += movement.x
        self.hitbox_rect.centerx = round(self.pos.x)
        self.collision('horizontal')

        # Move vertically
        self.pos.y += movement.y
        self.hitbox_rect.centery = round(self.pos.y)
        self.collision('vertical')

        # Update the main rect to follow the hitbox
        self.rect.center = self.hitbox_rect.center

    # Player collision detection
    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0:  # Moving right
                        self.hitbox_rect.right = sprite.rect.left
                    elif self.direction.x < 0:  # Moving left
                        self.hitbox_rect.left = sprite.rect.right
                    self.pos.x = self.hitbox_rect.centerx
                else:
                    if self.direction.y > 0:  # Moving down
                        self.hitbox_rect.bottom = sprite.rect.top
                    elif self.direction.y < 0:  # Moving up
                        self.hitbox_rect.top = sprite.rect.bottom
                    self.pos.y = self.hitbox_rect.centery

    def collectible(self):
        collected = pygame.sprite.spritecollide(self, self.collectible_sprites, True)
        return len(collected)

    def update(self, dt):
        if self.can_move:  # Only process movement if allowed
            self.input()
            self.move(dt)
        return self.hitbox_rect.center

class Ghost(pygame.sprite.Sprite):
    def __init__(self, pos, groups, player, collisions):
        super().__init__(groups)
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED) # replace w animated ghost sprite
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-5, -5)  # Smaller hitbox for smoother collision
        self.pos = pygame.math.Vector2(self.hitbox_rect.center)
        self.speed = 100
        self.player = player
        self.collision_sprites = collisions
        self.can_see_player = False

        # Add movement permission flag
        self.can_move = False
        self.initial_pos = pygame.math.Vector2(pos)  # Store initial position

        # Chase distance limits
        self.min_chase_distance = 0
        self.max_chase_distance = 300

        # Wandering behavior
        self.wander_direction = pygame.math.Vector2(1, 0)
        self.wander_timer = 0
        self.wander_interval = random.randint(2, 3)
        self.is_paused = False
        self.pause_timer = 0
        self.pause_duration = random.randint(0, 2)
        self.pause_chance = 0.1  # 10% chance to pause when changing direction
        self.min_pause_duration = 1  # Minimum pause duration in seconds
        self.max_pause_duration = 3  # Maximum pause duration in seconds


    def start_moving(self):
        self.can_move = True

    def stop_moving(self):
        self.can_move = False

    def check_line_of_sight(self):
        # Get the start (ghost) and end (player) positions
        start = pygame.math.Vector2(self.pos)
        end = pygame.math.Vector2(self.player.rect.center)

        # Calculate distance to player
        distance_to_player = (end - start).length()

        # Calculate the ray direction
        ray_dir = end - start
        distance = ray_dir.length()

        if distance == 0:  # If ghost and player are in the same position
            return True

        ray_dir = ray_dir.normalize()

        # Check for collisions along the ray
        for i in range(int(distance)):
            check_pos = start + ray_dir * i
            check_rect = pygame.Rect(check_pos.x - 1, check_pos.y - 1, 2, 2)

            # Check each collision sprite
            for sprite in self.collision_sprites:
                if sprite.rect.colliderect(check_rect):
                    self.can_see_player = False
                    return False

        self.can_see_player = True
        return True

    def get_distance_to_player(self):
        ghost_pos = pygame.math.Vector2(self.pos)
        player_pos = pygame.math.Vector2(self.player.rect.center)
        return (player_pos - ghost_pos).length()

    def start_pause(self):
        self.is_paused = True
        self.pause_timer = 0
        self.pause_duration = random.uniform(self.min_pause_duration, self.max_pause_duration)

    def update_pause(self, dt):
        if self.is_paused:
            self.pause_timer += dt
            if self.pause_timer >= self.pause_duration:
                self.is_paused = False
                self.wander_timer = 0  # Reset wander timer after pause

    def wander(self, dt):
        # Update pause state if currently paused
        if self.is_paused:
            self.update_pause(dt)
            return

        # Update wander timer
        self.wander_timer += dt
        if self.wander_timer >= self.wander_interval:
            # Chance to pause when changing direction
            if random.random() < self.pause_chance:
                self.start_pause()
                return

            # Change to a random direction
            angle = random.uniform(0, 2 * math.pi)
            self.wander_direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
            self.wander_timer = 0
            self.wander_interval = random.randint(2, 3)  # Randomize next interval

        # Move in the wander direction
        self.pos += self.wander_direction * (self.speed * 0.6) * dt

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.hitbox_rect.right > sprite.rect.left and self.old_hitbox.right <= sprite.rect.left:
                        self.hitbox_rect.right = sprite.rect.left
                    elif self.hitbox_rect.left < sprite.rect.right and self.old_hitbox.left >= sprite.rect.right:
                        self.hitbox_rect.left = sprite.rect.right
                    self.pos.x = self.hitbox_rect.centerx
                else:
                    if self.hitbox_rect.bottom > sprite.rect.top and self.old_hitbox.bottom <= sprite.rect.top:
                        self.hitbox_rect.bottom = sprite.rect.top
                    elif self.hitbox_rect.top < sprite.rect.bottom and self.old_hitbox.top >= sprite.rect.bottom:
                        self.hitbox_rect.top = sprite.rect.bottom
                    self.pos.y = self.hitbox_rect.centery

    def update(self, dt):
        if not self.can_move:  # Check at the start of update
            return

        self.old_hitbox = self.hitbox_rect.copy()  # Store the old position

        # Check if we can see the player
        can_see = self.check_line_of_sight()
        distance = self.get_distance_to_player()

        if can_see and self.min_chase_distance <= distance <= self.max_chase_distance:
            # Reset pause state when chasing
            self.is_paused = False

            # Chase the player
            direction = pygame.math.Vector2(self.player.rect.center) - self.pos
            if direction.length() > 0:
                direction = direction.normalize()
                self.pos += direction * self.speed * dt

            # Draw chase radius (for debugging)
            screen = pygame.display.get_surface()
            camera_offset = AllSprites().offset
            ghost_screen_pos = self.rect.center + camera_offset

            # Draw detection ranges (comment out these lines to hide them)
            pygame.draw.circle(screen, (255, 0, 0, 128), ghost_screen_pos, self.min_chase_distance, 1)  # Min range
            pygame.draw.circle(screen, (255, 255, 0, 128), ghost_screen_pos, self.max_chase_distance, 1)  # Max range

            # Draw line of sight
            pygame.draw.line(screen,
                             RED,
                             ghost_screen_pos,
                             self.player.rect.center + camera_offset,
                             2)
        else:
            # Wander around if can't see player
            self.wander(dt)

        # Update positions and check collisions
        self.hitbox_rect.centerx = round(self.pos.x)
        self.collision('horizontal')
        self.hitbox_rect.centery = round(self.pos.y)
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

class Blocks(pygame.sprite.Sprite):
    def __init__(self, pos, size, groups):
        super().__init__(groups)
        self.image = pygame.Surface(size)
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center = pos)

class Collectibles(pygame.sprite.Sprite):
    def __init__(self, pos, size, groups):
        super().__init__(groups)
        self.image = pygame.Surface(size)
        self.image.fill(BRATGREEN)
        self.rect = self.image.get_rect(center = pos)

class WinZone(pygame.sprite.Sprite):
    def __init__(self, pos, size, groups):
        super().__init__(groups)
        self.image = pygame.Surface(size)
        self.image.fill((255, 247, 0, 128))  # Semi-transparent green
        self.image.set_alpha(128)  # Make it semi-transparent
        self.rect = self.image.get_rect(center=pos)
        self.active = True

class Boundary(pygame.sprite.Sprite):
    def __init__(self, pos, size, groups):
        super().__init__(groups)
        self.image = pygame.Surface(size)
        self.image.fill((50, 50, 50))  # Dark gray color for boundaries
        self.rect = self.image.get_rect(topleft=pos)

# Sprite grouping
class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.screen = pygame.display.get_surface()
        self.offset = pygame.Vector2() # Cam offset setup

        # Store screen dimensions for calculations
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()

        # Reference to game boundaries (will be set by Game class)
        self.game_area = None

    def set_boundaries(self, game_area):
        """Set the game boundaries for camera clamping"""
        self.game_area = game_area

    def calculate_camera(self, target_pos):
        """Calculate camera position with boundary constraints"""
        # First calculate the ideal camera position (centered on target)
        desired_x = -(target_pos[0] - self.screen_width // 2)
        desired_y = -(target_pos[1] - self.screen_height // 2)

        if self.game_area:
            # Clamp camera to boundaries

            # Right boundary
            if desired_x < -(self.game_area['right'] - self.screen_width):
                desired_x = -(self.game_area['right'] - self.screen_width)
            # Left boundary
            if desired_x > -self.game_area['left']:
                desired_x = -self.game_area['left']

            # Bottom boundary
            if desired_y < -(self.game_area['bottom'] - self.screen_height):
                desired_y = -(self.game_area['bottom'] - self.screen_height)
            # Top boundary
            if desired_y > -self.game_area['top']:
                desired_y = -self.game_area['top']

        return pygame.Vector2(desired_x, desired_y)

    def draw(self, target_pos):
        """Draw sprites with clamped camera position"""
        self.offset = self.calculate_camera(target_pos)

        for sprite in self:
            offset_pos = sprite.rect.topleft + self.offset
            self.screen.blit(sprite.image, offset_pos)

# Animated Sprites
class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, frames, x, y, scale=1):
        super().__init__()
        self.frames = frames
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.animation_speed = 5
        self.animation_counter = 0
        self.scale = scale
        self.animating = False

    def start_animation(self):
        self.animating = True
        self.current_frame = 0

    def update(self):
        if self.animating:
            self.animation_counter += 1
            if self.animation_counter >= self.animation_speed:
                self.current_frame += 1
                if self.current_frame >= len(self.frames):
                    self.current_frame = len(self.frames) - 1
                    self.animating = False
                self.image = self.frames[self.current_frame]
                self.animation_counter = 0