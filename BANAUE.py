import pygame
import random
import sys
import os
from typing import List, Tuple

# Initialize Pygame
pygame.init()

# Asset paths configuration
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(GAME_DIR, "assets")
CARDS_DIR = os.path.join(GAME_DIR, "front_cards")
BACKGROUND_PATH = os.path.join(GAME_DIR, "background.png")
MUSIC_PATH = os.path.join(GAME_DIR, "background_music.mp3")
CARD_BACK_PATH = os.path.join(GAME_DIR, "card_back.png")

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CARD_WIDTH = 120
CARD_HEIGHT = 160
CARD_MARGIN = 20
FONT_SIZE = 32

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)

# Load and play background music
try:
    pygame.mixer.music.load(MUSIC_PATH)
    pygame.mixer.music.play(-1)  # -1 makes it loop indefinitely
    pygame.mixer.music.set_volume(0.7)  # Set volume to 70%
except pygame.error as e:
    print(f"Error loading music: {e}")

class Card:
    def __init__(self, x: int, y: int, pair_id: int, image_path: str):
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self.pair_id = pair_id
        self.is_flipped = False
        self.is_matched = False
        
        # Load and scale card image
        try:
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.scale(self.image, (CARD_WIDTH, CARD_HEIGHT))
        except pygame.error as e:
            print(f"Error loading card image {image_path}: {e}")
            # Create a fallback image
            self.image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.image.fill(WHITE)
            
        # Load card back image
        try:
            self.back = pygame.image.load(CARD_BACK_PATH)
            self.back = pygame.transform.scale(self.back, (CARD_WIDTH, CARD_HEIGHT))
        except pygame.error as e:
            print(f"Error loading card back image: {e}")
            # Create a fallback back image
            self.back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.back.fill(GRAY)
            pygame.draw.rect(self.back, BLACK, pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT), 2)
       
    def draw(self, screen):
        if self.is_matched or self.is_flipped:
            screen.blit(self.image, self.rect)
        else:
            screen.blit(self.back, self.rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Card Matching Game")
        
        # Load background
        try:
            self.background = pygame.image.load(BACKGROUND_PATH)
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error as e:
            print(f"Error loading background: {e}")
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background.fill(WHITE)
        
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.story_font = pygame.font.SysFont(None, FONT_SIZE - 8)
        
        self.cards: List[Card] = []
        self.flipped_cards: List[Card] = []
        self.story_progress = 0
        self.matches_found = 0
        
        self.initialize_cards()
        
        self.flip_timer = 0
        self.waiting_to_flip_back = False

    def find_card_files(self) -> List[Tuple[str, str]]:
        """Find all card files in the current directory that match the pattern 'card_'."""
        card_pairs = []
        directory = CARDS_DIR
        
        for i in range(1, 9):  # For 8 pairs
            card1 = os.path.join(directory, f"pair{i}_card1.png")
            card2 = os.path.join(directory, f"pair{i}_card2.png")
            if os.path.exists(card1) and os.path.exists(card2):
                card_pairs.append((card1, card2))
        
        # Make sure we have enough pairs
        if len(card_pairs) < 8:
            raise Exception(f"Not enough card images found. Found {len(card_pairs)}, need at least 8.")
        
        return card_pairs[:8]

    def initialize_cards(self):
        try:
            card_pairs = self.find_card_files()
            
            total_cards = 16  # 8 pairs
            cards_per_row = 4
            rows = total_cards // cards_per_row
            
            start_x = (SCREEN_WIDTH - (cards_per_row * (CARD_WIDTH + CARD_MARGIN))) // 2
            start_y = (SCREEN_HEIGHT - (rows * (CARD_HEIGHT + CARD_MARGIN))) // 2
            
            cards_to_place = []
            for pair_id, (card1_path, card2_path) in enumerate(card_pairs):
                cards_to_place.append((card1_path, pair_id))
                cards_to_place.append((card2_path, pair_id))
            
            random.shuffle(cards_to_place)
        
            self.cards = []
            for i in range(total_cards):
                row = i // cards_per_row
                col = i % cards_per_row
                x = start_x + col * (CARD_WIDTH + CARD_MARGIN)
                y = start_y + row * (CARD_HEIGHT + CARD_MARGIN)
                image_path, pair_id = cards_to_place[i]
                self.cards.append(Card(x, y, pair_id, image_path))
                
        except Exception as e:
            error_text = f"Error initializing cards: {e}"
            print(error_text)
            # Display error message on screen
            font = pygame.font.SysFont(None, 36)
            text = font.render(error_text, True, (255, 0, 0))
            self.screen.fill(BLACK)
            self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 
                                  SCREEN_HEIGHT//2 - text.get_height()//2))
            pygame.display.flip()
            pygame.time.wait(3000)  # Show error for 3 seconds
            pygame.quit()
            sys.exit(1)

    def handle_click(self, pos):
        if self.waiting_to_flip_back:
            return
            
        for card in self.cards:
            if card.rect.collidepoint(pos) and not card.is_flipped and not card.is_matched:
                if len(self.flipped_cards) < 2:
                    card.is_flipped = True
                    self.flipped_cards.append(card)
                    
                    if len(self.flipped_cards) == 2:
                        if self.flipped_cards[0].pair_id == self.flipped_cards[1].pair_id:
                            self.flipped_cards[0].is_matched = True
                            self.flipped_cards[1].is_matched = True
                            self.matches_found += 1
                            self.flipped_cards = []
                        else:
                            self.waiting_to_flip_back = True
                            self.flip_timer = pygame.time.get_ticks()
                break

    def update(self):
        if self.waiting_to_flip_back and pygame.time.get_ticks() - self.flip_timer > 1000:
            for card in self.flipped_cards:
                card.is_flipped = False
            self.flipped_cards = []
            self.waiting_to_flip_back = False

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        
        # Draw cards
        for card in self.cards:
            card.draw(self.screen)
        
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
            
            self.update()
            self.draw()
            clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()