import pygame
import random
import math
from enum import Enum

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
RED_TRANSPARENT = (255, 0, 0, 40)
BLUE = (50, 100, 255)
GRID_COLOR = (150, 150, 150)
RANGE_COLOR = (255, 100, 100, 30)
YELLOW = (255, 255, 0)

# Game settings
PLAYER_SPEED = 5.8
GUARD_SPEED = 4.0
GUARD_DETECTION_RADIUS = 150
GUARD_CHASE_SPEED_MULTIPLIER = 1.3
GUARD_TERRITORY_CHASE_MULTIPLIER = 1.6
GUARD_TAG_RANGE = 42
GUARD_REACH_ANGLE = 360

class Direction(Enum):
    HORIZONTAL = 1
    VERTICAL = 2

class GuardState(Enum):
    PATROL = 1
    CHASE = 2
    INTERCEPT = 3
    RETURN = 4

class AlertIndicator:
    def __init__(self):
        self.active = False
        self.animation_time = 0
        self.duration = 1.0
        self.height = 30
        self.scale = 1.0
        
        # Create exclamation mark surface
        self.surface = pygame.Surface((20, 30), pygame.SRCALPHA)
        pygame.draw.rect(self.surface, YELLOW, (8, 2, 4, 20))
        pygame.draw.circle(self.surface, YELLOW, (10, 26), 2)

    def activate(self):
        self.active = True
        self.animation_time = 0
        self.scale = 0.1

    def update(self, delta_time):
        if self.active:
            self.animation_time += delta_time
            if self.animation_time < 0.2:
                self.scale = min(1.0, self.scale + delta_time * 8)
            if self.animation_time >= self.duration:
                self.active = False

    def draw(self, screen, position):
        if self.active:
            scaled_surface = pygame.transform.scale(
                self.surface, 
                (int(20 * self.scale), int(30 * self.scale))
            )
            pos = (
                position[0] - scaled_surface.get_width() // 2,
                position[1] - self.height - scaled_surface.get_height() // 2
            )
            bounce_offset = math.sin(self.animation_time * 10) * 3 if self.animation_time < 0.5 else 0
            pos = (pos[0], pos[1] + bounce_offset)
            screen.blit(scaled_surface, pos)

class Guard(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, patrol_range, line_y=None, phase_offset=0, territory_bounds=None):
        super().__init__()
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(self.image, RED, (12, 12), 12)
        pygame.draw.circle(self.image, (255, 100, 100), (12, 12), 8)
        if direction == Direction.HORIZONTAL:
            pygame.draw.line(self.image, (255, 100, 100), (6, 12), (18, 12), 2)
        else:
            pygame.draw.line(self.image, (255, 100, 100), (12, 6), (12, 18), 2)

        self.rect = self.image.get_rect()
        self.hitbox = self.rect.inflate(-8, -8)
        self.rect.centerx = x
        self.rect.centery = y
        self.hitbox.center = self.rect.center
        
        self.position = pygame.math.Vector2(x, y)
        self.direction = direction
        self.speed = GUARD_SPEED
        self.patrol_range = patrol_range
        self.line_y = line_y
        self.fixed_x = x if direction == Direction.VERTICAL else None
        
        self.state = GuardState.PATROL
        self.patrol_time = random.uniform(0, 2) + phase_offset
        self.patrol_direction = pygame.math.Vector2(1, 0) if direction == Direction.HORIZONTAL else pygame.math.Vector2(0, 1)
        self.change_direction_time = random.uniform(2, 4)
        self.target_velocity = pygame.math.Vector2(0, 0)
        self.velocity = pygame.math.Vector2(0, 0)
        
        self.original_pos = pygame.math.Vector2(x, y)
        self.patrol_point = None
        self.wait_timer = 0
        self.reaction_delay = 0
        self.last_player_pos = None
        self.territory_bounds = territory_bounds
        self.patrol_y = y
        self.grid_left = None
        self.grid_right = None
        
        self.range_surface = pygame.Surface((GUARD_TAG_RANGE * 2, GUARD_TAG_RANGE * 2), pygame.SRCALPHA)
        self.update_range_indicator()
        
        self.alert = AlertIndicator()
        self.territory_alert_cooldown = 0
        self.territory_violation = False
        self.acceleration = 1.0
        self.chase_target = None

    def set_grid_boundaries(self, left, right):
        self.grid_left = left
        self.grid_right = right

    def is_player_in_territory(self, player_pos):
        if self.territory_bounds is None or self.grid_left is None:
            return False
            
        if self.direction == Direction.HORIZONTAL:
            territory_top = self.patrol_y - 25
            territory_bottom = self.patrol_y + 25
            return (self.grid_left <= player_pos.x <= self.grid_right and 
                   territory_top <= player_pos.y <= territory_bottom)
        else:
            territory_left = self.position.x - 25
            territory_right = self.position.x + 25
            if self.line_y:
                return (territory_left <= player_pos.x <= territory_right and 
                       self.patrol_y <= player_pos.y <= self.line_y)
            return False

    def update(self, player, grid_bounds):
        delta_time = 1/60
        player_pos = pygame.math.Vector2(player.rect.center)
        to_player = player_pos - self.position
        distance = to_player.length()
        
        # Check territory violation
        in_territory = self.is_player_in_territory(player_pos)
        if in_territory and not self.territory_violation:
            self.territory_violation = True
            if self.territory_alert_cooldown <= 0:
                self.alert.activate()
                self.territory_alert_cooldown = 2.0
        elif not in_territory:
            self.territory_violation = False
        
        if self.territory_alert_cooldown > 0:
            self.territory_alert_cooldown -= delta_time
        
        self.alert.update(delta_time)
        
        player_detected = (distance < GUARD_DETECTION_RADIUS or in_territory)
        
        # Adjust acceleration based on territory violation
        if in_territory:
            target_acceleration = 1.6
            self.acceleration = min(self.acceleration + delta_time * 2, target_acceleration)
        else:
            target_acceleration = 1.0
            self.acceleration = max(self.acceleration - delta_time, target_acceleration)
        
        if player_detected:
            if self.reaction_delay <= 0:
                self.last_player_pos = player_pos
                if in_territory:
                    player_velocity = pygame.math.Vector2(player.velocity)
                    prediction_time = 0.5
                    predicted_pos = player_pos + player_velocity * prediction_time
                    self.chase_target = predicted_pos
                else:
                    self.chase_target = player_pos
            else:
                self.reaction_delay -= delta_time
        
        if self.state == GuardState.PATROL:
            if player_detected:
                self.state = GuardState.CHASE
                self.reaction_delay = random.uniform(0.1, 0.2)
            else:
                self.sophisticated_patrol(grid_bounds)
                
        elif self.state == GuardState.CHASE:
            if not player_detected:
                self.state = GuardState.RETURN
                self.patrol_point = self.original_pos
            else:
                self.enhanced_chase(to_player, player, in_territory)
                
        elif self.state == GuardState.RETURN:
            if player_detected:
                self.state = GuardState.CHASE
            elif self.return_to_patrol(grid_bounds):
                self.state = GuardState.PATROL
        
        self.apply_movement_constraints(grid_bounds)
        self.rect.center = self.position
        self.hitbox.center = self.position

    def sophisticated_patrol(self, grid_bounds):
        self.patrol_time += 1/60
        
        if self.patrol_time >= self.change_direction_time:
            if random.random() < 0.3:
                self.wait_timer = random.uniform(0.5, 1.0)
                self.target_velocity *= 0
            else:
                if self.direction == Direction.HORIZONTAL:
                    self.patrol_direction.x *= -1
                else:
                    self.patrol_direction.y *= -1
                self.speed = GUARD_SPEED * random.uniform(0.9, 1.1)
                
            self.patrol_time = 0
            self.change_direction_time = random.uniform(2, 4)
        
        if self.wait_timer > 0:
            self.wait_timer -= 1/60
            self.target_velocity *= 0.9
        else:
            self.target_velocity = self.patrol_direction * self.speed

    def enhanced_chase(self, to_player, player, in_territory):
        if self.direction == Direction.HORIZONTAL:
            to_player.y = 0
        else:
            to_player.x = 0
            
        if self.last_player_pos is not None:
            player_velocity = (pygame.math.Vector2(player.rect.center) - self.last_player_pos) * 60
            prediction_factor = 0.7 if in_territory else 0.5
            intercept_pos = pygame.math.Vector2(player.rect.center) + player_velocity * prediction_factor
            
            if in_territory:
                if self.direction == Direction.HORIZONTAL:
                    if abs(self.position.x - intercept_pos.x) > self.patrol_range / 2:
                        self.acceleration = max(self.acceleration, 1.8)
            
            to_intercept = intercept_pos - self.position
            
            if self.direction == Direction.HORIZONTAL:
                to_intercept.y = 0
            else:
                to_intercept.x = 0
            
            if to_intercept.length() > 0:
                to_player = to_intercept
        
        if to_player.length() > 0:
            speed_multiplier = GUARD_TERRITORY_CHASE_MULTIPLIER if in_territory else GUARD_CHASE_SPEED_MULTIPLIER
            self.target_velocity = to_player.normalize() * (self.speed * speed_multiplier * self.acceleration)
        
        self.last_player_pos = pygame.math.Vector2(player.rect.center)

    def return_to_patrol(self, grid_bounds):
        to_origin = self.original_pos - self.position
        if to_origin.length() < 2:
            self.position = self.original_pos
            return True
        
        if self.direction == Direction.HORIZONTAL:
            to_origin.y = 0
        else:
            to_origin.x = 0
        
        if to_origin.length() > 0:
            self.target_velocity = to_origin.normalize() * self.speed
        return False

    def apply_movement_constraints(self, grid_bounds):
        self.velocity = self.velocity.lerp(self.target_velocity, 0.15)
        new_pos = self.position + self.velocity
        
        if self.direction == Direction.HORIZONTAL:
            if grid_bounds.left + 12 <= new_pos.x <= grid_bounds.right - 12:
                self.position.x = new_pos.x
            else:
                self.patrol_direction.x *= -1
                self.target_velocity = self.patrol_direction * self.speed
        else:
            if grid_bounds.top + 12 <= new_pos.y <= self.line_y - 12:
                self.position.y = new_pos.y
            else:
                self.patrol_direction.y *= -1
                self.target_velocity = self.patrol_direction * self.speed
            self.position.x = self.fixed_x

    def can_tag_player(self, player_pos):
        direct_distance = (player_pos - self.position).length()
        in_territory = self.is_player_in_territory(player_pos)
        return direct_distance <= GUARD_TAG_RANGE or in_territory

    def update_range_indicator(self):
        self.range_surface.fill((0, 0, 0, 0))
        center = (GUARD_TAG_RANGE, GUARD_TAG_RANGE)
        pygame.draw.circle(self.range_surface, RANGE_COLOR, center, GUARD_TAG_RANGE)

    def draw(self, screen):
        # Draw range
        range_pos = (self.position.x - GUARD_TAG_RANGE, self.position.y - GUARD_TAG_RANGE)
        screen.blit(self.range_surface, range_pos)
        
        # Draw guard
        screen.blit(self.image, self.rect)
        
        # Draw alert
        self.alert.draw(screen, self.rect.midtop)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (12, 12), 12)
        pygame.draw.circle(self.image, (100, 150, 255), (12, 12), 8)
        pygame.draw.line(self.image, (100, 150, 255), (6, 12), (18, 12), 2)
        
        self.rect = self.image.get_rect()
        self.hitbox = self.rect.inflate(-8, -8)
        self.rect.centerx = x
        self.rect.centery = y
        self.hitbox.center = self.rect.center
        
        self.velocity = pygame.math.Vector2(0, 0)
        self.position = pygame.math.Vector2(x, y)
        self.speed = PLAYER_SPEED

    def move(self, keys, screen_width, screen_height, grid_bounds):
        dx = keys[pygame.K_d] - keys[pygame.K_a]
        dy = keys[pygame.K_s] - keys[pygame.K_w]
        
        movement = pygame.math.Vector2(dx, dy)
        if movement.length() > 0:
            movement = movement.normalize()
        
        target_velocity = movement * self.speed
        # Smoother acceleration/deceleration
        self.velocity = self.velocity.lerp(target_velocity, 0.3)
        
        # Calculate new position with boundary checking
        new_pos = pygame.math.Vector2(self.position)
        test_pos = new_pos + self.velocity
        
        # Handle horizontal movement
        if grid_bounds.left + 12 <= test_pos.x <= grid_bounds.right - 12:
            new_pos.x = test_pos.x
        else:
            # Stop horizontal velocity when hitting boundaries
            self.velocity.x = 0
            new_pos.x = max(grid_bounds.left + 12, min(test_pos.x, grid_bounds.right - 12))
        
        # Handle vertical movement
        if grid_bounds.top + 12 <= test_pos.y <= screen_height - 30:
            new_pos.y = test_pos.y
        else:
            # Stop vertical velocity when hitting boundaries
            self.velocity.y = 0
            new_pos.y = max(grid_bounds.top + 12, min(test_pos.y, screen_height - 30))
        
        self.position = new_pos
        self.rect.center = self.position
        self.hitbox.center = self.position