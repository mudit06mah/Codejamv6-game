import pygame
from settings import *

class CutsceneManager:
    def __init__(self, screen):
        self.screen = screen
        try:
            # Try loading a custom pixel/medieval font if available
            self.font = pygame.font.Font("assets/font.ttf", 28)
        except:
            # Fallback to a Serif font for a more medieval look than Courier
            self.font = pygame.font.SysFont("georgia", 24, bold=True)
            
        self.scenes = [] 
        self.current_index = 0
        self.timer = 0
        self.finished = False
        self.fade_alpha = 0

    def start_sequence(self, sequence_data):
        """
        sequence_data = [
            {"image": surface, "text": "Line 1", "duration": 3.0},
            ...
        ]
        """
        self.scenes = sequence_data
        self.current_index = 0
        self.timer = sequence_data[0]["duration"]
        self.finished = False
        self.fade_alpha = 255

    def update(self, dt):
        if self.finished: return

        # Simple fade-in effect logic (optional polish)
        if self.fade_alpha > 0:
            self.fade_alpha -= 1000 * dt
            if self.fade_alpha < 0: self.fade_alpha = 0

        self.timer -= dt
        if self.timer <= 0:
            self.current_index += 1
            if self.current_index >= len(self.scenes):
                self.finished = True
            else:
                self.timer = self.scenes[self.current_index]["duration"]
                self.fade_alpha = 255 # Reset fade for next slide

    def draw(self):
        if self.finished: return
        
        data = self.scenes[self.current_index]
        
        # 1. Draw Image
        if data.get("image"):
            # Scale to fit screen
            img = data["image"]
            img = pygame.transform.scale(img, (WIDTH, HEIGHT))
            self.screen.blit(img, (0,0))
        else:
            self.screen.fill(BLACK)
        
        # 2. Draw Text (Centered at bottom with shadow)
        if data.get("text"):
            text_str = data["text"]
            
            # Shadow
            shad = self.font.render(text_str, True, BLACK)
            shad_rect = shad.get_rect(center=(WIDTH//2, HEIGHT - 50 + 2))
            self.screen.blit(shad, shad_rect)
            
            # Main Text
            surf = self.font.render(text_str, True, WHITE)
            rect = surf.get_rect(center=(WIDTH//2, HEIGHT - 50))
            self.screen.blit(surf, rect)

        # 3. Fade Transition
        if self.fade_alpha > 0:
            fade = pygame.Surface((WIDTH, HEIGHT))
            fade.fill(BLACK)
            fade.set_alpha(int(self.fade_alpha))
            self.screen.blit(fade, (0,0))

class DialogueSystem:
    def __init__(self, screen):
        self.screen = screen
        try:
            self.font = pygame.font.Font("assets/font.ttf", 22)
        except:
            self.font = pygame.font.SysFont("georgia", 20)
            
        self.active = False
        self.text = ""
        self.refusal_text = "I cannot turn back."
        self.choices = ["YES", "NO"]
        self.selected_index = 0
        self.on_confirm = None 

    def start_dialogue(self, text, callback_yes, refusal_text="I won't turn back."):
        self.active = True
        self.text = text
        self.refusal_text = refusal_text
        self.on_confirm = callback_yes
        self.selected_index = 0

    def handle_input(self, event):
        if not self.active: return
        
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_a, pygame.K_LEFT]:
                self.selected_index = 0
            elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                self.selected_index = 1
            elif event.key == pygame.K_SPACE:
                if self.selected_index == 0: # YES
                    self.active = False
                    if self.on_confirm: self.on_confirm()
                else: # NO
                    # Show the refusal text
                    self.text = self.refusal_text
                    self.selected_index = 0 # Reset cursor to YES to force them eventually

    def draw(self):
        if not self.active: return
        
        # Draw Box (Centered)
        box_w, box_h = 600, 200
        box_rect = pygame.Rect((WIDTH - box_w)//2, (HEIGHT - box_h)//2, box_w, box_h)
        
        # Background with slight transparency
        s = pygame.Surface((box_w, box_h))
        s.set_alpha(220)
        s.fill((20, 20, 20))
        self.screen.blit(s, (box_rect.x, box_rect.y))
        
        # Border
        pygame.draw.rect(self.screen, (150, 150, 150), box_rect, 3)
        
        # Draw Main Text (Wrapped)
        lines = self.text.split('\n')
        y_off = 40
        for line in lines:
            surf = self.font.render(line, True, WHITE)
            rect = surf.get_rect(center=(WIDTH//2, box_rect.y + y_off))
            self.screen.blit(surf, rect)
            y_off += 30
            
        # Draw Choices
        y_choice = box_rect.bottom - 40
        
        # YES
        col_yes = (255, 215, 0) if self.selected_index == 0 else (100, 100, 100)
        yes_txt = self.font.render(f"> YES <" if self.selected_index == 0 else "  YES  ", True, col_yes)
        yes_rect = yes_txt.get_rect(center=(box_rect.centerx - 80, y_choice))
        self.screen.blit(yes_txt, yes_rect)

        # NO
        col_no = (255, 215, 0) if self.selected_index == 1 else (100, 100, 100)
        no_txt = self.font.render(f"> NO <" if self.selected_index == 1 else "  NO  ", True, col_no)
        no_rect = no_txt.get_rect(center=(box_rect.centerx + 80, y_choice))
        self.screen.blit(no_txt, no_rect)