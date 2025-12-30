import pygame

# Screen
WIDTH, HEIGHT = 960, 540
FPS = 60

# CHANGED: Increased GROUND_Y so characters stand lower (closer to bottom)
# Screen height is 540, so 515 leaves a small 25px margin.
GROUND_Y = 515 

# Colors
WHITE = (240, 240, 240)
BLACK = (10, 10, 10)
RED = (200, 60, 60)
ORANGE = (200, 140, 60)
YELLOW = (240, 220, 120)
BLUE = (60, 120, 200)
GRAY = (90, 90, 90)
PURPLE = (160, 80, 200)
DARK_GREY = (40, 40, 40)
CRIMSON = (120, 0, 0)

# Game State Keys
STATE_MENU = "menu"
STATE_CUTSCENE = "cutscene"
STATE_DIALOGUE = "dialogue"
STATE_GAME_PAPIA = "papia_fight"
STATE_TRANSITION = "transition"
STATE_GAME_HARUS = "harus_fight"
STATE_ENDING = "ending"
STATE_GAMEOVER = "gameover"

def load_strip(path, frame_count, frame_w=None, frame_h=None):
    try:
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        if frame_w is None:
            frame_w = sheet.get_width() // frame_count
            frame_h = sheet.get_height()
            
        for i in range(frame_count):
            frame = sheet.subsurface((i * frame_w, 0, frame_w, frame_h))
            frames.append(frame)
        return frames
    except Exception as e:
        print(f"ERROR loading {path}: {e}")
        s = pygame.Surface((frame_w or 64, frame_h or 64))
        s.fill((255, 0, 255))
        return [s]