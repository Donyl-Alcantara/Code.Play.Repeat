# Alexa Villarroel
# Updated on Nov. 4, 2024
# El Nido Mini Game of ISLA (LT9)
# The player answers trivia questions through "island hopping"

# Added alternative questions so that the experience when played again is different
# Added a scoring system (although currently it does not show the final score at the end)
# Cohesive storyline (player answers questions through island hopping with relevant questions)

# Rafa
    # Optimized a performance issue especially found when loading the 'four pics' question type
    # by preloading the image assets in an image cache before drawing them on the screen
    # Added bg music
    # Fixed text wrapping & answer boxes


import pygame
import random
import json
import os
import textwrap

# Initialize paths
GAME_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize Pygame and its mixer
pygame.init()
pygame.mixer.init()

# Game constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
BLUE = (0, 0, 255)
TRANSPARENT = (255, 255, 255, 128)

class Question:
    def __init__(self, data):
        self.number = data['question_number']
        self.type = data['type']
        self.text = data['question_text']
        self.correct_answer = data['correct_answer']
        self.options = data.get('options', [])
        self.images = data.get('images', [])
        self.background = data.get('background_image')
        self.attempts = 0
        self.max_score = 100
        self.fade_alpha = 0

    def calculate_score(self):
        return max(0, self.max_score - (self.attempts * 25))

class GameAudio:
    def __init__(self):
        self.background_music = None
        self.wave_sound = None
        self.correct_sound = None
        self.wrong_sound = None
        self.load_audio()
        
    def load_audio(self):
        try:
            audio_paths = {
                'background': 'assets/audio/sunbathing.mp3',
                'wave': 'assets/audio/wave.mp3',
                'correct': 'assets/audio/correct.mp3',
                'wrong': 'assets/audio/wrong.mp3'
            }
            
            for audio_type, path in audio_paths.items():
                full_path = os.path.join(GAME_DIR, path)
                if not os.path.exists(full_path):
                    print(f"Warning: Audio file not found: {full_path}")
                    continue
                    
                try:
                    sound = pygame.mixer.Sound(full_path)
                    if audio_type == 'background':
                        self.background_music = sound
                        sound.set_volume(0.3)
                    elif audio_type == 'wave':
                        self.wave_sound = sound
                        sound.set_volume(0.4)
                    elif audio_type == 'correct':
                        self.correct_sound = sound
                        sound.set_volume(0.5)
                    elif audio_type == 'wrong':
                        self.wrong_sound = sound
                        sound.set_volume(0.5)
                except pygame.error as e:
                    print(f"Error loading {path}: {e}")
        except Exception as e:
            print(f"Error in load_audio: {e}")

    def play_background(self):
        if self.background_music:
            try:
                self.background_music.play(-1)
            except pygame.error as e:
                print(f"Error playing background music: {e}")

    def stop_background(self):
        if self.background_music:
            try:
                self.background_music.stop()
            except pygame.error as e:
                print(f"Error stopping background music: {e}")

    def play_wave(self):
        if self.wave_sound:
            self.wave_sound.play()

    def play_correct(self):
        if self.correct_sound:
            self.correct_sound.play()

    def play_wrong(self):
        if self.wrong_sound:
            self.wrong_sound.play()

class TextBox:
    def __init__(self, font, width, padding=10):
        self.font = font
        self.width = width
        self.padding = padding
        self.background = pygame.Surface((width + 2 * padding, 150))
        self.background.fill(WHITE)
        self.background.set_alpha(180)

    def render(self, screen, text, pos, centered=False):
        words = text.split()
        lines = []
        current_line = []
        current_width = 0

        for word in words:
            word_surface = self.font.render(word + ' ', True, BLACK)
            word_width = word_surface.get_width()

            if current_width + word_width >= self.width:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width

        if current_line:
            lines.append(' '.join(current_line))

        total_height = len(lines) * self.font.get_linesize()
        background = pygame.Surface((self.width + 2 * self.padding, total_height + 2 * self.padding))
        background.fill(WHITE)
        background.set_alpha(180)

        if centered:
            x = pos[0] - (self.width + 2 * self.padding) // 2
            y = pos[1] - (total_height + 2 * self.padding) // 2
        else:
            x, y = pos

        screen.blit(background, (x, y))

        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, BLACK)
            if centered:
                text_rect = text_surface.get_rect(center=(
                    pos[0],
                    y + self.padding + i * self.font.get_linesize() + self.font.get_linesize() // 2
                ))
            else:
                text_rect = text_surface.get_rect(topleft=(
                    x + self.padding,
                    y + self.padding + i * self.font.get_linesize()
                ))
            screen.blit(text_surface, text_rect)

class TriviaGame:
    def __init__(self):
        pygame.display.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Palawan Trivia Game")
        self.clock = pygame.time.Clock()

        # Load fonts
        try:
            font_path = os.path.join(GAME_DIR, 'assets/fonts/pixel_font.ttf')
            self.font = pygame.font.Font(font_path, 28)
            self.score_font = pygame.font.Font(font_path, 22)
            self.instructions_font = pygame.font.Font(font_path, 18)
            self.instructions_text_box = TextBox(self.instructions_font, 600)
        except pygame.error as e:
            print(f"Error loading font: {e}")
            self.font = pygame.font.Font(None, 28)
            self.score_font = pygame.font.Font(None, 22)
            self.instructions_font = pygame.font.Font(None, 18)
            self.instructions_text_box = TextBox(self.instructions_font, 600)

        self.text_box = TextBox(self.font, 600)
        self.questions = []
        self.current_question = None
        self.current_index = 0
        self.total_score = 0
        self.answered_questions = 0
        self.click_positions = []
        self.image_cache = {}
        self.game_over = False
        self.audio = GameAudio()
        self.last_background = None
        self.QUESTION_Y_POS = 100

    def load_questions(self, filename):
        json_path = os.path.join(GAME_DIR, filename)
        try:
            if not os.path.exists(json_path):
                raise FileNotFoundError(f"Questions file not found: {json_path}")
                
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for q_data in data['ordered_questions']:
                alt = random.choice(q_data['alternatives'])
                alt['question_number'] = q_data['question_number']
                self.questions.append(Question(alt))
                
            self.questions.sort(key=lambda x: x.number)
            if self.questions:
                self.current_question = self.questions[0]
                self.preload_images()
            else:
                raise ValueError("No valid questions loaded")
                
        except Exception as e:
            print(f"Error loading questions: {e}")
            pygame.quit()
            exit(1)

    def preload_images(self):
        """Preload all images used in the game to improve performance."""
        print("Preloading images...")
        try:
            # Preload all question images
            for question in self.questions:
                if hasattr(question, 'images') and question.images:
                    for img_path in question.images:
                        if img_path not in self.image_cache:
                            print(f"Loading image: {img_path}")  # Debug print
                            image = self.load_image(img_path, (200, 200))
                            if image:
                                self.image_cache[img_path] = image

                # Preload background images
                if hasattr(question, 'background') and question.background:
                    if question.background not in self.image_cache:
                        print(f"Loading background: {question.background}")  # Debug print
                        bg_image = self.load_image(question.background, (WINDOW_WIDTH, WINDOW_HEIGHT))
                        if bg_image:
                            self.image_cache[question.background] = bg_image
        except Exception as e:
            print(f"Error preloading images: {e}")

    def load_image(self, path, size=None):
        try:
            full_path = os.path.join(GAME_DIR, path)
            if not os.path.exists(full_path):
                print(f"Image not found: {full_path}")
                return None

            image = pygame.image.load(full_path).convert_alpha()  # Use convert_alpha for all images
            if size:
                try:
                    image = pygame.transform.scale(image, size)
                except pygame.error as e:
                    print(f"Error scaling image: {e}")
                    return None
            return image
        except pygame.error as e:
            print(f"Error loading image {path}: {e}")
            return None

    def draw_text(self, text, pos, centered=False, color=BLACK, is_score=False, is_instruction=False):
        if is_score:
            text_surface = self.score_font.render(text, True, color)
            self.screen.blit(text_surface, pos)
        elif is_instruction:
            self.instructions_text_box.render(self.screen, text, pos, centered)
        else:
            self.text_box.render(self.screen, text, pos, centered)

    def draw_background(self):
        self.screen.fill(WHITE)
        if hasattr(self.current_question, 'background') and self.current_question.background:
            bg = self.image_cache.get(self.current_question.background)
            if bg:
                fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                fade_surface.fill(WHITE)
                fade_surface.set_alpha(255 - self.current_question.fade_alpha)

                self.screen.blit(bg, (0, 0))
                self.screen.blit(fade_surface, (0, 0))

                if self.current_question.fade_alpha < 255:
                    self.current_question.fade_alpha += 10  # Faster fade

    def handle_multiple_choice(self, events):
        button_height = 40
        button_spacing = 15

        for i, option in enumerate(self.current_question.options):
            button = pygame.Rect(
                (WINDOW_WIDTH - 350) // 2,
                350 + i * (button_height + button_spacing),
                350,
                button_height
            )

            button_surface = pygame.Surface((350, button_height))
            button_surface.fill(GRAY)
            button_surface.set_alpha(180)
            self.screen.blit(button_surface, button.topleft)

            self.draw_text(option, button.center, True)

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if button.collidepoint(event.pos):
                        if option == self.current_question.correct_answer:
                            self.audio.play_correct()
                            self.advance_question()
                        else:
                            self.audio.play_wrong()
                            self.current_question.attempts += 1

    def handle_four_pics(self, events, input_text):
        image_size = 200
        margin = 20
        start_y = self.QUESTION_Y_POS + 100
        for i, img_path in enumerate(self.current_question.images[:4]):
            image = self.image_cache.get(img_path)
            if image:
                x = WINDOW_WIDTH // 2 - image_size - margin//2 + (i % 2) * (image_size + margin)
                y = start_y + (i // 2) * (image_size + margin)
                self.screen.blit(image, (x, y))

        input_rect = pygame.Rect((WINDOW_WIDTH - 400) // 2, 625, 400, 50)
        pygame.draw.rect(self.screen, WHITE, input_rect)
        pygame.draw.rect(self.screen, BLACK, input_rect, 2)
        if input_text:
            text_surface = self.font.render(input_text, True, BLACK)
            # If text is too wide, truncate input_text
            if text_surface.get_width() > input_rect.width - 20:  # 20 pixels padding
                return input_text[:-1]  # Remove last character
            # Draw text if it fits
            text_rect = text_surface.get_rect(topleft=(input_rect.x + 10, input_rect.y + 15))
            self.screen.blit(text_surface, text_rect)

        return self.handle_text_input(events, input_text)

    def handle_photo_click(self, events):
        if self.current_question.images:
            image_path = self.current_question.images[0]
            image = self.image_cache.get(image_path)
            if image:
                image_rect = image.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
                self.screen.blit(image, image_rect)

                # Draw markers for previous clicks
                for pos in self.click_positions:
                    marker = pygame.Surface((10, 10))
                    marker.fill(BLUE)
                    marker.set_alpha(128)
                    self.screen.blit(marker, (image_rect.x + pos[0] - 5, image_rect.y + pos[1] - 5))

                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if image_rect.collidepoint(event.pos):
                            click_pos = (event.pos[0] - image_rect.x, event.pos[1] - image_rect.y)
                            self.click_positions.append(click_pos)
                            if f"{click_pos[0]},{click_pos[1]}" == self.current_question.correct_answer:
                                self.audio.play_correct()
                                self.advance_question()
                            else:
                                self.audio.play_wrong()
                                self.current_question.attempts += 1

    def handle_photo_type(self, events, input_text):
        if hasattr(self.current_question, 'images') and self.current_question.images:
            image_path = self.current_question.images[0]
            image = self.image_cache.get(image_path)
            if image:
                self.screen.blit(image, image.get_rect(center=(WINDOW_WIDTH//2, 350)))

        input_rect = pygame.Rect((WINDOW_WIDTH - 400) // 2, 625, 400, 50)
        pygame.draw.rect(self.screen, WHITE, input_rect)
        pygame.draw.rect(self.screen, BLACK, input_rect, 2)
        if input_text:
            text_surface = self.font.render(input_text, True, BLACK)
            # If text is too wide, truncate input_text
            if text_surface.get_width() > input_rect.width - 20:  # 20 pixels padding
                return input_text[:-1]  # Remove last character
            # Draw text if it fits
            text_rect = text_surface.get_rect(topleft=(input_rect.x + 10, input_rect.y + 15))
            self.screen.blit(text_surface, text_rect)

        return self.handle_text_input(events, input_text)

    def handle_text_input(self, events, input_text):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Convert input to lowercase for case-insensitive comparison
                    user_answer = input_text.lower()
                    # Handle both list and string correct answers
                    if isinstance(self.current_question.correct_answer, list):
                        # Check if user's answer matches any of the acceptable answers
                        if any(user_answer == ans.lower() for ans in self.current_question.correct_answer):
                            self.audio.play_correct()
                            self.advance_question()
                            return ""
                    else:
                        # Handle single string answer
                        if user_answer == self.current_question.correct_answer.lower():
                            self.audio.play_correct()
                            self.advance_question()
                            return ""

                    # If we get here, the answer was incorrect
                    self.audio.play_wrong()
                    self.current_question.attempts += 1
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    # Test if new character would fit before adding it
                    test_text = input_text + event.unicode
                    test_surface = self.font.render(test_text, True, BLACK)
                    # Only add character if it fits within input box (with padding)
                    if test_surface.get_width() <= 380:  # 400 - 20 padding
                        input_text += event.unicode
        return input_text

    def advance_question(self):
        self.total_score += self.current_question.calculate_score()
        self.answered_questions += 1
        self.current_index += 1
        if self.current_index < len(self.questions):
            self.current_question = self.questions[self.current_index]
            self.current_question.fade_alpha = 0
            self.click_positions = []
        else:
            self.current_question = None

        if self.current_question and self.current_question.background:
            self.last_background = self.current_question.background

    def run(self):
        if not self.questions:
            print("No questions loaded. Exiting game.")
            return

        self.audio.play_background()
        if self.current_index == 0:
            self.audio.play_wave()
        
        running = True
        input_text = ""
        
        while running:
            try:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        running = False
                        break

                self.screen.fill(WHITE)

                if self.current_question is None:
                    if not self.game_over:
                        self.game_over = True
                        self.click_positions = []

                    if self.last_background:
                        bg = self.image_cache.get(self.last_background)
                        if bg:
                            self.screen.blit(bg, (0, 0))
                    else:
                        self.screen.fill(WHITE)

                    self.draw_text(f"Game Over! Final Score: {self.total_score}",
                                   (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2), True)
                    self.draw_text("Press ENTER to exit",
                                   (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50), True)

                    # Check for player pressing ENTER
                    for event in events:
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                            running = False
                            break

                    pygame.display.flip()
                    self.clock.tick(FPS)
                    continue

                # Main game loop
                self.draw_background() # update background

                # Score Display
                score_text = f"Score: {self.total_score}"
                self.draw_text(score_text, (20, 20), is_score=True)

                # Question Text
                self.text_box = TextBox(self.font, 800)
                self.draw_text(self.current_question.text, (WINDOW_WIDTH // 2, self.QUESTION_Y_POS), True)

                # Handle different question types and set instructions accordingly
                instruction_text = ""
                if self.current_question.type == "multiple_choice":
                    self.handle_multiple_choice(events)
                    instruction_text = "Click the correct answer"
                elif self.current_question.type == "four_pics":
                    input_text = self.handle_four_pics(events, input_text)
                    instruction_text = "Type your answer and press Enter"
                elif self.current_question.type == "photo_click":
                    self.handle_photo_click(events)
                    instruction_text = "Click the correct location in the image"
                elif self.current_question.type == "photo_type":
                    input_text = self.handle_photo_type(events, input_text)
                    instruction_text = "Type your answer and press Enter"

                if instruction_text:
                    self.instructions_text_box = TextBox(self.instructions_font, 600)
                    self.draw_text(instruction_text, (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 20), True, is_instruction=True)

                pygame.display.flip()
                self.clock.tick(FPS)

            except pygame.error or Exception as e:
                print(f"Error in game loop: {e}")
                running = False
        
        self.cleanup()

    def cleanup(self):
        """Clean up resources before exiting."""
        try:
            self.audio.stop_background()
            pygame.quit()
        except Exception as e:
            print(f"Error during cleanup: {e}")

def main():
    try:
        game = TriviaGame()
        game.load_questions('questions.json')
        game.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        pygame.quit()

if __name__ == "__main__":
    main()