import pygame, sys, random
from settings import *
from player import Player
from bosses import PapiaBoss, HarusBoss, rect_point_distance
from story import CutsceneManager, DialogueSystem
from pygame.math import Vector2

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vanitas")
clock = pygame.time.Clock()

# --- MUSIC ---
try:
    pygame.mixer.music.load("assets/SFX/pain.mp3")
    pygame.mixer.music.set_volume(0.2) 
    pygame.mixer.music.play(-1) 
except Exception as e:
    print(f"Music Warning: {e}")

# --- FONTS ---
try:
    font_path = "assets/font.ttf"
    font_ui = pygame.font.Font(font_path, 20)
    font_big = pygame.font.Font(font_path, 56)
except:
    font_ui = pygame.font.SysFont("georgia", 20)
    font_big = pygame.font.SysFont("times new roman", 60, bold=True)

# --- LOAD ASSETS ---
def load_img(path, scale=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if scale:
            img = pygame.transform.scale(img, scale)
        return img
    except Exception as e:
        print(f"Missing Asset: {path}")
        s = pygame.Surface((scale if scale else (100,100)))
        s.fill((50, 0, 0)) 
        return s

# UI Assets
wife_portrait = load_img("assets/story/wife.png", (100, 100))

# Game Assets
img_bg_fight = load_img("assets/story/bg1.png", (WIDTH, HEIGHT))

# Story Assets
img_title = load_img("assets/story/title.png", (WIDTH, HEIGHT))
img_marriage = load_img("assets/story/marriage.png")
img_hand1 = load_img("assets/story/hand1.png")
img_hand2 = load_img("assets/story/hand2.png")
img_cave = load_img("assets/story/cave.png")
img_end = load_img("assets/story/end.png")

# --- GAME VARIABLES ---
current_state = STATE_MENU
player = Player()
boss = None
base_memory_opacity = 255 
checkpoint_reached = False 

# Story Systems
cutscene_mgr = CutsceneManager(screen)
dialogue_sys = DialogueSystem(screen)

# Screen Shake
shake_timer = 0.0
shake_intensity = 0.0

def start_shake(intensity, duration=0.2):
    global shake_timer, shake_intensity
    shake_timer = duration
    shake_intensity = intensity

def draw_ui(screen, player, boss_name, boss_hp, boss_max):
    # Health Bar
    pygame.draw.rect(screen, RED, (20, 20, player.hp * 20, 20))
    pygame.draw.rect(screen, WHITE, (20, 20, player.max_hp * 20, 20), 2)
    
    # Boss Health Bar
    if boss_hp > 0:
        bar_w = 300
        ratio = boss_hp / boss_max
        pygame.draw.rect(screen, PURPLE, (WIDTH - 320, 20, bar_w * ratio, 20))
        pygame.draw.rect(screen, WHITE, (WIDTH - 320, 20, bar_w, 20), 2)
        txt = font_ui.render(boss_name, True, WHITE)
        screen.blit(txt, (WIDTH - 320, 45))

    # --- WIFE PORTRAIT LOGIC ---
    # Draw Frame
    frame_rect = pygame.Rect(18, 58, 104, 104)
    pygame.draw.rect(screen, (220, 220, 220), frame_rect, 3)
    
    # Calculate Opacity
    current_alpha = base_memory_opacity
    if boss and boss_max > 0:
        hp_percent = max(0, boss_hp / boss_max)
        if boss_name == "PAPIA":
            current_alpha = 100 + int((190 - 100) * hp_percent)
        elif "HARUS" in boss_name:
            current_alpha = int(100 * hp_percent)
    
    # Draw Photo
    if current_alpha > 0:
        wife_portrait.set_alpha(current_alpha)
        screen.blit(wife_portrait, (20, 60))

def draw_text_centered(text, y_offset=0, color=WHITE, font=font_big):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH//2, HEIGHT//2 + y_offset))
    screen.blit(surf, rect)

# --- STORY FLOW ---

def start_intro_cutscene():
    global current_state
    current_state = STATE_CUTSCENE
    cutscene_mgr.start_sequence([
        {"image": img_marriage, "text": "She was my beloved", "duration": 3.0},
        {"image": img_hand1, "text": "But they...", "duration": 2.0},
        {"image": img_hand2, "text": "They took her from me", "duration": 2.5},
        {"image": img_cave, "text": "I finally tracked them, I must take my revenge", "duration": 3.0},
    ])

def finish_intro_cutscene():
    global current_state
    current_state = STATE_DIALOGUE
    dialogue_sys.start_dialogue(
        "To enter, you must shed the weight of your past.\nForget your FIRST DATE to gain speed?    ", 
        unlock_dash_and_start,
        refusal_text="I won't turn back, I must seek revenge"
    )

def unlock_dash_and_start():
    global current_state, boss, base_memory_opacity
    player.can_dash = True
    base_memory_opacity = 190 
    current_state = STATE_GAME_PAPIA
    boss = PapiaBoss()
    player.pos = Vector2(100, GROUND_Y)

def start_transition_dialogue():
    global current_state
    current_state = STATE_DIALOGUE
    dialogue_sys.start_dialogue(
        "Papia falls, but the killer remains.\nForget her VOICE to gain strength?    ",
        unlock_checkpoint_and_start,
        refusal_text="I'm so close, I won't turn back"
    )

def unlock_checkpoint_and_start():
    global current_state, boss, base_memory_opacity, checkpoint_reached
    base_memory_opacity = 100
    current_state = STATE_GAME_HARUS
    boss = HarusBoss()
    player.pos = Vector2(100, GROUND_Y)
    player.hp = player.max_hp
    checkpoint_reached = True

def start_ending_sequence():
    global current_state, base_memory_opacity
    current_state = STATE_ENDING
    base_memory_opacity = 0 
    cutscene_mgr.start_sequence([
        {"image": img_end, "text": "My revenge is complete, yet I cannot remember her name", "duration": 999}
    ])

# --- MAIN LOOP ---
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if current_state == STATE_DIALOGUE:
            dialogue_sys.handle_input(event)
            continue 

        if event.type == pygame.KEYDOWN:
            if current_state == STATE_MENU:
                if event.key == pygame.K_SPACE:
                    start_intro_cutscene()
                    
            elif current_state == STATE_ENDING:
                if event.key == pygame.K_SPACE:
                    current_state = STATE_MENU
                    player = Player()
                    base_memory_opacity = 255
                    checkpoint_reached = False
                    
            elif current_state == STATE_GAMEOVER:
                if event.key == pygame.K_SPACE:
                    if checkpoint_reached:
                        start_transition_dialogue()
                        player = Player()
                        player.can_dash = True
                    else:
                        current_state = STATE_MENU
                        player = Player()
                        base_memory_opacity = 255
                        checkpoint_reached = False

    # Logic
    if current_state in [STATE_CUTSCENE, STATE_ENDING]:
        cutscene_mgr.update(dt)
        if current_state == STATE_CUTSCENE and cutscene_mgr.finished:
            finish_intro_cutscene()

    elif current_state in [STATE_GAME_PAPIA, STATE_GAME_HARUS]:
        keys = pygame.key.get_pressed()
        player.update(dt, keys)
        
        if boss:
            boss.update(dt, player)
            if hasattr(boss, 'shake_requested') and boss.shake_requested > 0:
                start_shake(boss.shake_requested)
            
            # Interactions
            if player.attack_state == "active" and player.attack_hitbox:
                if player.attack_hitbox.colliderect(boss.hurtbox()):
                    if not player.attack_damage_applied:
                        boss.hp -= 1
                        player.attack_damage_applied = True
                        if hasattr(boss, 'on_parried') and boss.parry_window: boss.on_parried()

                if isinstance(boss, PapiaBoss) and boss.orb:
                    if player.attack_hitbox.colliderect(pygame.Rect(boss.orb.pos.x - 20, boss.orb.pos.y - 20, 40, 40)):
                        boss.orb = None
                        boss.hp -= 1
                        player.attack_damage_applied = True

            # Damage
            boss_hit = False
            if hasattr(boss, 'attack_hitbox') and boss.attack_hitbox and boss.attack_active:
                if boss.attack_hitbox.colliderect(player.hurtbox()): boss_hit = True
            
            if isinstance(boss, PapiaBoss):
                for m in boss.meteors:
                    if m.hits_player(player): boss_hit = True
                if boss.orb and (boss.orb.pos - player.pos).length() < 40:
                    boss_hit = True
                    boss.orb = None 

            if isinstance(boss, HarusBoss):
                for s in boss.shockwaves:
                    if s.rect.colliderect(player.hurtbox()):
                        boss_hit = True
                        s.active = False
                if boss.attack_type == "swing" and boss.attack_active:
                    if rect_point_distance(player.hurtbox(), boss.axe_tip_pos()) <= boss.swing_tip_radius:
                        boss_hit = True

            if boss_hit and player.hit_recovery_timer <= 0:
                player.hp -= 1
                player.hit_recovery_timer = 1.0
                player.vel.x = -300 * player.facing
                start_shake(5, 0.2)

            if player.hp <= 0:
                if hasattr(boss, 'cleanup'): boss.cleanup()
                boss = None
                current_state = STATE_GAMEOVER
                
            elif boss.hp <= 0:
                if hasattr(boss, 'cleanup'): boss.cleanup()
                boss = None
                if current_state == STATE_GAME_PAPIA:
                    start_transition_dialogue()
                else:
                    start_ending_sequence()

    # Drawing
    offset = (0, 0)
    if shake_timer > 0:
        shake_timer -= dt
        offset = (random.randint(-int(shake_intensity), int(shake_intensity)), 
                  random.randint(-int(shake_intensity), int(shake_intensity)))

    screen.fill(BLACK)
    
    if current_state == STATE_MENU:
        screen.blit(img_title, (0,0))
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            surf = font_ui.render("Press SPACE to Start", True, GRAY)
            screen.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT - 80)))

    elif current_state in [STATE_CUTSCENE, STATE_ENDING]:
        cutscene_mgr.draw()
        
    elif current_state == STATE_DIALOGUE:
        pygame.draw.rect(screen, (15, 15, 20), (0,0,WIDTH,HEIGHT))
        if current_state == STATE_DIALOGUE and img_cave and "FIRST DATE" in dialogue_sys.text:
             s_cave = pygame.transform.scale(img_cave, (WIDTH, HEIGHT))
             screen.blit(s_cave, (0,0))
             
        dialogue_sys.draw()

    elif current_state in [STATE_GAME_PAPIA, STATE_GAME_HARUS]:
        # Draw Background Image with offset
        screen.blit(img_bg_fight, (offset[0], offset[1]))
        
        if boss: boss.draw(screen, offset)
        player.draw(screen, offset)
        
        boss_name = "PAPIA" if current_state == STATE_GAME_PAPIA else "HARUS"
        if boss: draw_ui(screen, player, boss_name, boss.hp, boss.max_hp)

    elif current_state == STATE_GAMEOVER:
        draw_text_centered("DEATH", -20, RED)
        msg = "(press space to retry)"
        surf = font_ui.render(msg, True, WHITE)
        screen.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))

    pygame.display.flip()

pygame.quit()