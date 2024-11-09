# Alexa Villarroel
# Updated on Nov. 4, 2024
# El Nido Mini Game of ISLA (LT9)
# The player answers trivia questions through "island hopping"

# Added alternative questions so that the experience when played again is different
# Added a scoring system (although currently it does not show the final score at the end)
# Cohesive storyline (player answers questions through island hopping with relevant questions)

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
                'background': 'assets/audio/background_music.mp3',
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
        self.background = pygame.Surface((width + 2 * padding, 100))
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
        
        try:
            font_path = os.path.join(GAME_DIR, 'assets/fonts/pixel_font.ttf')
            if os.path.exists(font_path):
                self.font = pygame.font.Font(font_path, 28)  # Smaller font size
                self.score_font = pygame.font.Font(font_path, 36)  # Score font size
            else:
                print(f"Warning: Font file not found at {font_path}")
                self.font = pygame.font.Font(None, 28)
                self.score_font = pygame.font.Font(None, 36)
        except pygame.error as e:
            print(f"Error loading font: {e}")
            self.font = pygame.font.Font(None, 28)
            self.score_font = pygame.font.Font(None, 36)
        
        self.text_box = TextBox(self.font, 600)
        self.questions = []
        self.current_question = None
        self.current_index = 0
        self.total_score = 0
        self.answered_questions = 0
        self.click_positions = []
        
        self.audio = GameAudio()

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
            else:
                raise ValueError("No valid questions loaded")
                
        except Exception as e:
            print(f"Error loading questions: {e}")
            pygame.quit()
            exit(1)

    def load_image(self, path, size=None):
        try:
            full_path = os.path.join(GAME_DIR, path)
            if not os.path.exists(full_path):
                print(f"Image not found: {full_path}")
                return None
                
            image = pygame.image.load(full_path)
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

    def draw_text(self, text, pos, centered=False, color=BLACK, is_score=False):
        if is_score:
            text_surface = self.score_font.render(text, True, color)
            self.screen.blit(text_surface, pos)
        else:
            self.text_box.render(self.screen, text, pos, centered)

    def draw_background(self):
        self.screen.fill(WHITE)
        if self.current_question.background:
            bg = self.load_image(self.current_question.background, (WINDOW_WIDTH, WINDOW_HEIGHT))
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
        for i, img_path in enumerate(self.current_question.images[:4]):
            image = self.load_image(img_path, (image_size, image_size))
            if image:
                x = WINDOW_WIDTH//2 - image_size - margin//2 + (i % 2) * (image_size + margin)
                y = 250 + (i // 2) * (image_size + margin)
                self.screen.blit(image, (x, y))

        input_rect = pygame.Rect((WINDOW_WIDTH - 400) // 2, 600, 400, 50)
        pygame.draw.rect(self.screen, WHITE, input_rect)
        pygame.draw.rect(self.screen, BLACK, input_rect, 2)
        self.draw_text(input_text, (input_rect.x + 10, input_rect.y + 10))

        return self.handle_text_input(events, input_text)

    def handle_photo_click(self, events):
        if self.current_question.images:
            image = self.load_image(self.current_question.images[0], (600, 400))
            if image:
                image_rect = image.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
                self.screen.blit(image, image_rect)
                
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
        if self.current_question.images:
            image = self.load_image(self.current_question.images[0], (600, 400))
            if image:
                self.screen.blit(image, image.get_rect(center=(WINDOW_WIDTH//2, 350)))

        input_rect = pygame.Rect((WINDOW_WIDTH - 400) // 2, 600, 400, 50)
        pygame.draw.rect(self.screen, WHITE, input_rect)
        pygame.draw.rect(self.screen, BLACK, input_rect, 2)
        self.draw_text(input_text, (input_rect.x + 10, input_rect.y + 10))

        return self.handle_text_input(events, input_text)

    def handle_text_input(self, events, input_text):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_text.lower() == self.current_question.correct_answer.lower():
                        self.audio.play_correct()
                        self.advance_question()
                        return ""
                    else:
                        self.audio.play_wrong()
                        self.current_question.attempts += 1
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
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

                if not self.current_question:
                    # Enhanced game over screen with semi-transparent background
                    self.screen.fill(WHITE)
                    game_over_bg = pygame.Surface((600, 200))
                    game_over_bg.fill(WHITE)
                    game_over_bg.set_alpha(180)
                    
                    bg_rect = game_over_bg.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
                    self.screen.blit(game_over_bg, bg_rect)
                    
                    self.draw_text(f"Game Over! Final Score: {self.total_score}", 
                                 (WINDOW_WIDTH//2, WINDOW_HEIGHT//2), True)
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    running = False
                    continue

                self.draw_background()
                
                # Enhanced score display with special font and positioning
                score_text = f"Score: {self.total_score}"
                score_x = 20
                score_y = 20
                self.draw_text(score_text, (score_x, score_y), is_score=True)

                # Enhanced question text presentation with TextBox
                self.draw_text(self.current_question.text, (WINDOW_WIDTH//2, 150), True)

                # Handle different question types with enhanced visuals
                if self.current_question.type == "multiple_choice":
                    self.handle_multiple_choice(events)
                elif self.current_question.type == "four_pics":
                    input_text = self.handle_four_pics(events, input_text)
                elif self.current_question.type == "photo_click":
                    self.handle_photo_click(events)
                    # Draw semi-transparent click markers
                    for pos in self.click_positions:
                        marker = pygame.Surface((10, 10))
                        marker.fill(BLUE)
                        marker.set_alpha(128)
                        image = self.load_image(self.current_question.images[0], (600, 400))
                        if image:
                            image_rect = image.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
                            self.screen.blit(marker, (image_rect.x + pos[0] - 5, image_rect.y + pos[1] - 5))
                elif self.current_question.type == "photo_type":
                    input_text = self.handle_photo_type(events, input_text)

                # Add subtle instruction text based on question type
                instruction_text = ""
                if self.current_question.type == "multiple_choice":
                    instruction_text = "Click the correct answer"
                elif self.current_question.type in ["four_pics", "photo_type"]:
                    instruction_text = "Type your answer and press Enter"
                elif self.current_question.type == "photo_click":
                    instruction_text = "Click the correct location in the image"

                if instruction_text:
                    instruction_bg = pygame.Surface((400, 30))
                    instruction_bg.fill(WHITE)
                    instruction_bg.set_alpha(150)
                    self.screen.blit(instruction_bg, ((WINDOW_WIDTH - 400)//2, WINDOW_HEIGHT - 40))
                    self.draw_text(instruction_text, (WINDOW_WIDTH//2, WINDOW_HEIGHT - 30), True)

                pygame.display.flip()
                self.clock.tick(FPS)
                
            except pygame.error as e:
                print(f"Error in game loop: {e}")
                running = False
            except Exception as e:
                print(f"Unexpected error: {e}")
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