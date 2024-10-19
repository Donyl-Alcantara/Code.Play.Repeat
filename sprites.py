from settings import *
class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collisions, collectibles):
        super().__init__(groups)
        self.image = pygame.image.load(join('islaintragame','img', 'player', 'adventurer-idle-00.png')).convert_alpha()
        self.rect = self.image.get_rect(center = pos)
        self.hitbox_rect = self.rect.inflate(-30, 0)
        self.hitbox_rect.center = self.rect.center

        # Movement
        self.pos = pygame.math.Vector2(self.hitbox_rect.center)
        self.direction = pygame.Vector2()
        self.speed = 250

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
        self.input()
        self.move(dt)
        return self.collectible()

class Ghost(pygame.sprite.Sprite):
    def __init__(self, pos, groups, player):
        super().__init__(groups)
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 100
        self.player = player

    def update(self, dt):
        direction = pygame.math.Vector2(self.player.rect.center) - self.pos
        if direction.length() > 0:
            direction = direction.normalize()

        self.pos += direction * self.speed * dt
        self.rect.center = round(self.pos.x), round(self.pos.y)


# Sprites with collision
class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, pos, size, groups):
        super().__init__(groups)
        self.image = pygame.Surface(size)
        self.image.fill(BLACK)
        self.rect = self.image.get_rect(center = pos)

class Collectibles(pygame.sprite.Sprite):
    def __init__(self, pos, size, groups):
        super().__init__(groups)
        self.image = pygame.Surface(size)
        self.image.fill(BRATGREEN)
        self.rect = self.image.get_rect(center = pos)

# Sprite grouping
class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.screen = pygame.display.get_surface()
        self.offset = pygame.Vector2()

    # Draw sprites to display camera movement effect
    def draw(self, target_pos):
        self.offset.x = -(target_pos[0] - WIDTH // 2)
        self.offset.y = -(target_pos[1] - HEIGHT // 2)
        for sprite in self:
            self.screen.blit(sprite.image, sprite.rect.topleft + self.offset)

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