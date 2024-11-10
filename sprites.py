import pygame.draw
import random
import math
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collisions, collectibles):
        super().__init__(groups)
        # Draw player sprites
        self.animation = SpriteSheet(self)
        self.animation.add_animation('idle', 'img//player//idle.png', 12)
        self.animation.add_animation('run', 'img//player//run.png', 12)

        # Draw player rect
        self.rect = self.image.get_rect(center = pos)
        self.hitbox_rect = self.rect.inflate(-10, 0)
        self.hitbox_rect.center = self.rect.center

        # Movement
        self.pos = pygame.math.Vector2(self.hitbox_rect.center)
        self.direction = pygame.Vector2()
        self.base_speed = 120
        self.speed = self.base_speed
        self.can_move = False

        # Sprint mechanics
        self.sprint_multiplier = 1.4  # Sprint is 1.6x normal speed
        self.is_sprinting = False
        self.stamina = 100  # Max stamina
        self.current_stamina = self.stamina
        self.stamina_drain_rate = 20  # Stamina points drained per second while sprinting
        self.stamina_regen_rate = 5  # Stamina points regenerated per second while not sprinting
        self.stamina_regen_delay = 0.5  # Seconds to wait before regenerating stamina
        self.stamina_regen_timer = 0  # Timer to track delay before regeneration

        # Object interaction
        self.collision_sprites = collisions
        self.collectible_sprites = collectibles

    def update_animation_state(self):
        # Determine which animation to play based on movement
        if self.direction.magnitude() == 0:
            self.animation.set_animation('idle', 5)
        else:
            self.animation.set_animation('run', 15 if self.is_sprinting else 10)

        # Update facing direction
        if self.direction.x > 0:
            self.animation.facing_right = True
        elif self.direction.x < 0:
            self.animation.facing_right = False

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

    def sprint(self, dt):
        keys = pygame.key.get_pressed()

        # Check for sprint input and sufficient stamina
        if keys[pygame.K_LSHIFT] and self.current_stamina > 0:
            self.is_sprinting = True
            self.speed = self.base_speed * self.sprint_multiplier
            # Drain stamina while sprinting
            self.current_stamina = max(0, self.current_stamina - self.stamina_drain_rate * dt)
            self.stamina_regen_timer = 0
        else:
            self.is_sprinting = False
            self.speed = self.base_speed

            # Handle stamina regeneration
            if not self.is_sprinting:
                self.stamina_regen_timer += dt
                if self.stamina_regen_timer >= self.stamina_regen_delay:
                    self.current_stamina = min(self.stamina, self.current_stamina + self.stamina_regen_rate * dt)

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

    def draw_stamina_bar(self, screen):
        # Bar dimensions and position
        bar_width = 280
        bar_height = 20
        x = 10
        y = 40  # Position below score display

        # Draw background (empty bar)
        pygame.draw.rect(screen, (64, 64, 64), (x, y, bar_width, bar_height))

        # Draw stamina level
        stamina_width = (self.current_stamina / self.stamina) * bar_width
        stamina_color = (0, 255, 0) if not self.is_sprinting else (
        255, 165, 0)  # Green when normal, orange when sprinting
        pygame.draw.rect(screen, stamina_color, (x, y, stamina_width, bar_height))

        # Draw border
        pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 2)

    def update(self, dt):
        if self.can_move:
            self.input()
            self.move(dt)
            self.sprint(dt)
        self.update_animation_state()
        self.animation.animate(dt)
        return self.hitbox_rect.center

class Ghost(pygame.sprite.Sprite):
    def __init__(self, pos, groups, player, collisions):
        super().__init__(groups)
        # Draw ghost sprite
        self.animation = SpriteSheet(self)
        self.animation.add_animation('idle', 'img//npcs//idle.png', 1, scale=1)
        self.animation.add_animation('moving', 'img//npcs//moving.png', 5, scale=1)
        self.animation.set_animation('idle', 5)  # Set default to idle

        # Draw ghost rect
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-20, 0)
        self.pos = pygame.math.Vector2(self.hitbox_rect.center)

        self.speed = 200
        self.player = player
        self.collision_sprites = collisions
        self.can_see_player = False
        self.win_zone_rect = None

        # Add movement permission flag
        self.can_move = False
        self.initial_pos = pygame.math.Vector2(pos)  # Store initial position

        # Chase distance limits
        self.min_chase_distance = 0
        self.max_chase_distance = 200

        # Wandering behavior
        self.wander_direction = pygame.math.Vector2(random.randint(0,1), random.randint(0,1))
        self.wander_timer = 0
        self.wander_interval = random.randint(2, 3)
        self.is_paused = False
        self.pause_timer = 0
        self.pause_duration = random.randint(0, 2)
        self.pause_chance = 0.1
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
        distance = (end - start).length()

        # Only check line of sight if within max chase distance
        if distance > self.max_chase_distance:
            self.can_see_player = False
            return False

        ray_dir = (end - start).normalize()

        # Check fewer points along the line (step size of 8 instead of 1)
        for i in range(0, int(distance), 8):
            check_pos = start + ray_dir * i
            check_rect = pygame.Rect(check_pos.x - 1, check_pos.y - 1, 2, 2)

            # Use any() with generator expression instead of list comprehension
            if any(sprite.rect.colliderect(check_rect) for sprite in self.collision_sprites):
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

        # Test if next wandering position would enter win zone
        test_pos = self.pos + self.wander_direction * (self.speed * 0.4) * dt
        test_rect = self.hitbox_rect.copy()
        test_rect.center = test_pos

        # Only move if wouldn't enter win zone
        if not (self.win_zone_rect and self.win_zone_rect.colliderect(test_rect)):
            self.pos += self.wander_direction * (self.speed * 0.4) * dt

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

    def set_win_zone(self, win_zone):
        # Method to set the win zone reference
        self.win_zone_rect = win_zone.rect

    def update_animation_state(self, direction=None):
        """Update the ghost's animation based on its state and direction"""
        # If we're not moving (during pause or at start), use idle
        if self.is_paused or not self.can_move:
            self.animation.set_animation('idle', 5)
        else:
            self.animation.set_animation('moving', 5)

        # Update facing direction based on movement or target direction
        if direction is not None and direction.length() > 0:
            self.animation.facing_right = direction.x > 0

    def update(self, dt):
        if not self.can_move:  # Stops ghosts from moving at the start of the game
            self.update_animation_state()
            self.animation.animate(dt)
            return

        # Store the old position
        self.old_hitbox = self.hitbox_rect.copy()

        # Movement direction for animation
        movement_direction = pygame.math.Vector2(0, 0)

        # Update animation
        self.animation.animate(dt)

        if self.win_zone_rect and self.win_zone_rect.colliderect(self.player.rect):
            self.wander(dt)
            self.update_animation_state(self.wander_direction)
        else:
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
                    # Test if next position would be in win zone
                    test_pos = self.pos + direction * self.speed * dt
                    test_rect = self.hitbox_rect.copy()
                    test_rect.center = test_pos
                    
                    # Only move if wouldn't enter win zone
                    if not (self.win_zone_rect and self.win_zone_rect.colliderect(test_rect)):
                        self.pos += direction * self.speed * dt
                        movement_direction = direction
                        self.update_animation_state(movement_direction)

            else:
                # Wander around if can't see player
                self.wander(dt)
                self.update_animation_state(self.wander_direction)

        # Update positions and check collisions
        self.hitbox_rect.centerx = round(self.pos.x)
        self.collision('horizontal')
        self.hitbox_rect.centery = round(self.pos.y)
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

class Blocks(pygame.sprite.Sprite):
    def __init__(self, pos, size, groups):
        super().__init__(groups)
        self.block_images = {
            'stone1': "img//env//stone1.png",
            'stone2': "img//env//stone2.png",
            'stone3': "img//env//stone3.png",
            'stone4': "img//env//stone4.png",
            'stone5': "img//env//stone5.png"
        }
        selected_image = random.choice(list(self.block_images.values()))
        self.image = pygame.image.load(selected_image).convert_alpha()
        if size != (self.image.get_width(), self.image.get_height()):
            self.image = pygame.transform.scale(self.image, size)
        self.rect = self.image.get_rect(center = pos)
        self.hitbox_rect = self.rect.inflate(-10, -10)
        self.hitbox_rect.center = self.rect.center

class Collectibles(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.collectible_images = {
            'shard1': "img//env//shard1.png",
            'shard2': "img//env//shard2.png",
        }
        selected_image = random.choice(list(self.collectible_images.values()))
        self.base_image = pygame.image.load(selected_image).convert_alpha()
        
        # Create a larger surface for the glow effect
        glow_padding = 20  # Padding for glow effect
        self.image = pygame.Surface((self.base_image.get_width() + glow_padding*2,
                                   self.base_image.get_height() + glow_padding*2),
                                   pygame.SRCALPHA)
        
        # Create radial gradient for glow
        self.glow_radius = max(self.base_image.get_width(), self.base_image.get_height()) // 2 + glow_padding
        self.glow_surface = pygame.Surface((self.image.get_width(), self.image.get_height()), 
                                         pygame.SRCALPHA)
        
        # Animation parameters
        self.alpha = 0
        self.alpha_speed = 2
        self.alpha_direction = 1
        self.max_alpha = 60  # Maximum glow intensity
        
        # Position setup
        self.rect = self.image.get_rect(center=pos)
    
    def update(self, dt):
        # Update glow alpha
        self.alpha += self.alpha_speed * self.alpha_direction
        if self.alpha >= self.max_alpha:
            self.alpha_direction = -1
        elif self.alpha <= 0:
            self.alpha_direction = 1
        
        # Clear the surface
        self.image.fill((0,0,0,0))
        
        # Create radial glow
        for radius in range(self.glow_radius, 0, -1):
            alpha = int(max(0, self.alpha * (1 - radius/self.glow_radius)))
            pygame.draw.circle(self.glow_surface, (255, 247, 140, alpha), 
                             (self.image.get_width()//2, self.image.get_height()//2), radius)
        
        # Apply glow and main image
        self.image.blit(self.glow_surface, (0, 0))
        self.image.blit(self.base_image, 
                       (self.image.get_width()//2 - self.base_image.get_width()//2,
                        self.image.get_height()//2 - self.base_image.get_height()//2))

class WinZone(pygame.sprite.Sprite):
    def __init__(self, pos, size, groups):
        super().__init__(groups)
        self.image = pygame.Surface(size)
        self.image.fill((255, 247, 0, 128))  # Semi-transparent green
        self.image.set_alpha(32)  # Make it semi-transparent
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
    def __init__(self, game):
        super().__init__()
        self.game = game
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

        # Clamp camera to boundaries
        if self.game_area:
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

    def draw(self, target_pos, **kwargs):
        """Draw sprites with clamped camera position"""
        self.offset = self.calculate_camera(target_pos)

        # Draw background
        bg_pos = self.offset
        self.screen.blit(self.game.background_current, bg_pos)

        for sprite in self:
            offset_pos = sprite.rect.topleft + self.offset
            self.screen.blit(sprite.image, offset_pos)

class SpriteSheet:
    def __init__(self, sprite_obj):
        self.sprite = sprite_obj
        self.animations = {}
        self.frame_index = 0
        self.animation_speed = 5
        self.current_animation = None
        self.facing_right = True

    def load_spritesheet(self, path, num_frames, scale=1.2):
        """Load a spritesheet and return list of frames"""
        spritesheet = pygame.image.load(path).convert_alpha()
        frame_width = spritesheet.get_width() // num_frames
        frame_height = spritesheet.get_height()

        frames = []
        for i in range(num_frames):
            # Extract each frame from the spritesheet
            surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            surface.blit(spritesheet, (0, 0),
                         (i * frame_width, 0, frame_width, frame_height))
            scaled_surface = pygame.transform.scale(surface,
                                                    (int(frame_width * scale),
                                                     int(frame_height * scale)))
            frames.append(scaled_surface)
        return frames

    def add_animation(self, name, path, num_frames, scale=1.2):
        """Add a new animation to the animations dictionary"""
        self.animations[name] = self.load_spritesheet(path, num_frames, scale)
        if not self.current_animation:  # Set first added animation as default
            self.current_animation = name
            self.sprite.image = self.animations[name][0]

    def set_animation(self, name, speed=5):
        """Change current animation"""
        if self.current_animation != name:
            self.current_animation = name
            self.frame_index = 0
            self.animation_speed = speed

    def animate(self, dt):
        """Update animation frame"""
        if not self.current_animation:
            return

        # Update frame index
        self.frame_index += self.animation_speed * dt

        # Reset frame index when it exceeds animation length
        if self.frame_index >= len(self.animations[self.current_animation]):
            self.frame_index = 0

        # Update image
        self.sprite.image = self.animations[self.current_animation][int(self.frame_index)]

        # Flip sprite when changing directions
        if not self.facing_right:
            self.sprite.image = pygame.transform.flip(self.sprite.image, True, False)

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