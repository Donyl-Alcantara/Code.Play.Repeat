import pygame
import random
from settings import *

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Intramuros Demo 2")

# Player settings
player_size = 40
player_x = 0
player_y = 0
player_speed = 5

# Camera settings
camera_x = 0
camera_y = 0

# Boundary settings
BOUNDARY_SIZE = 2000
boundary = pygame.Rect(-BOUNDARY_SIZE//2, -BOUNDARY_SIZE//2, BOUNDARY_SIZE, BOUNDARY_SIZE)

# Create obstacles
num_obstacles = 20
obstacles = []
for _ in range(num_obstacles):
    obstacle_x = random.randint(boundary.left, boundary.right - 100)
    obstacle_y = random.randint(boundary.top, boundary.bottom - 100)
    obstacle_size = random.randint(20, 100)
    obstacles.append(pygame.Rect(obstacle_x, obstacle_y, obstacle_size, obstacle_size))

# Player rectangle for collision detection
player_rect = pygame.Rect(player_x, player_y, player_size, player_size)

# Game loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Store previous position for collision resolution
    prev_x, prev_y = player_rect.center

    # Player movement using WASD keys
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:  # Left
        player_rect.x -= player_speed
    if keys[pygame.K_d]:  # Right
        player_rect.x += player_speed
    if keys[pygame.K_w]:  # Up
        player_rect.y -= player_speed
    if keys[pygame.K_s]:  # Down
        player_rect.y += player_speed

    # Collision detection with obstacles
    for obstacle in obstacles:
        if player_rect.colliderect(obstacle):
            player_rect.center = prev_x, prev_y

    # Boundary collision
    player_rect.clamp_ip(boundary)

    # Update camera position
    camera_x = max(boundary.left, min(player_rect.centerx - WIDTH // 2, boundary.right - WIDTH))
    camera_y = max(boundary.top, min(player_rect.centery - HEIGHT // 2, boundary.bottom - HEIGHT))

    # Clear the screen
    screen.fill(WHITE)

    # Draw boundary
    pygame.draw.rect(screen, BLUE, boundary.move(-camera_x, -camera_y), 2)

    # Draw obstacles
    for obstacle in obstacles:
        pygame.draw.rect(screen, RED, obstacle.move(-camera_x, -camera_y))

    # Draw player
    screen_player_x = player_rect.x - camera_x
    screen_player_y = player_rect.y - camera_y
    pygame.draw.rect(screen, GREEN, (screen_player_x, screen_player_y, player_size, player_size))

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()