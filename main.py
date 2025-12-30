import pygame, sys, random
from settings import *
from player import Player
from bosses import PapiaBoss, HarusBoss, rect_point_distance
from pygame.math import Vector2
# from cutscene import CutsceneManager

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fading Memory")
clock = pygame.time.Clock()
font_ui = pygame.font.SysFont("arial", 20)
font_big = pygame.font.SysFont("arial", 48)

# Load UI Assets
try:
    wife_portrait = pygame.image.load("assets/ui/wife_portrait.png").convert_alpha()
    wife_portrait = pygame.transform.scale(wife_portrait, (100, 100))
except:
    wife_portrait = pygame.Surface((100, 100))
    wife_portrait.fill((200, 150, 150))

# Game Variables
current_state = STATE_MENU
player = Player()
boss = None
memory_opacity = 255 
checkpoint_reached = False 

# Screen Shake
shake_timer = 0.0
shake_intensity = 0.0

def start_shake(intensity, duration=0.2):
    global shake_timer, shake_intensity
    shake_timer = duration
    shake_intensity = intensity

def draw_ui(screen, player, boss_name, boss_hp, boss_max):
    pygame.draw.rect(screen, RED, (20, 20, player.hp * 20, 20))
    pygame.draw.rect(screen, WHITE, (20, 20, player.max_hp * 20, 20), 2)
    
    if boss_hp > 0:
        bar_w = 300
        ratio = boss_hp / boss_max
        pygame.draw.rect(screen, PURPLE, (WIDTH - 320, 20, bar_w * ratio, 20))
        pygame.draw.rect(screen, WHITE, (WIDTH - 320, 20, bar_w, 20), 2)
        txt = font_ui.render(boss_name, True, WHITE)
        screen.blit(txt, (WIDTH - 320, 45))

    wife_portrait.set_alpha(memory_opacity)
    screen.blit(wife_portrait, (20, 60))
    
    if player.can_dash:
        col = BLUE if player.dash_cooldown <= 0 else GRAY
        pygame.draw.circle(screen, col, (40, 180), 10)
        txt = font_ui.render("DASH (K)", True, col)
        screen.blit(txt, (60, 170))

def draw_text_centered(text, y_offset=0, color=WHITE):
    surf = font_big.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH//2, HEIGHT//2 + y_offset))
    screen.blit(surf, rect)

running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if current_state == STATE_MENU:
                if event.key == pygame.K_SPACE:
                    current_state = STATE_INTRO
                    
            elif current_state == STATE_INTRO:
                if event.key == pygame.K_SPACE:
                    player.can_dash = True
                    memory_opacity = 180
                    current_state = STATE_GAME_PAPIA
                    boss = PapiaBoss()
                    player.pos = Vector2(100, GROUND_Y)
                
            elif current_state == STATE_TRANSITION:
                if event.key == pygame.K_SPACE:
                    memory_opacity = 80
                    current_state = STATE_GAME_HARUS
                    boss = HarusBoss()
                    player.pos = Vector2(100, GROUND_Y)
                    player.hp = player.max_hp
                    checkpoint_reached = True 
                    
            elif current_state == STATE_ENDING:
                if event.key == pygame.K_SPACE:
                    current_state = STATE_MENU
                    player = Player()
                    memory_opacity = 255
                    checkpoint_reached = False
                    
            elif current_state == STATE_GAMEOVER:
                if event.key == pygame.K_SPACE:
                    if checkpoint_reached:
                        current_state = STATE_TRANSITION
                        player = Player()
                        player.can_dash = True
                        memory_opacity = 80
                    else:
                        current_state = STATE_MENU
                        player = Player()
                        memory_opacity = 255
                        checkpoint_reached = False

    # Logic
    keys = pygame.key.get_pressed()

    if current_state in [STATE_GAME_PAPIA, STATE_GAME_HARUS]:
        player.update(dt, keys)
        if boss:
            boss.update(dt, player)
            
            # Check Shake
            if hasattr(boss, 'shake_requested') and boss.shake_requested > 0:
                start_shake(boss.shake_requested)
            
            # Player hits Boss
            if player.attack_state == "active" and player.attack_hitbox:
                if player.attack_hitbox.colliderect(boss.hurtbox()):
                    if not player.attack_damage_applied:
                        boss.hp -= 1
                        player.attack_damage_applied = True
                
                # Player destroys Orb
                if isinstance(boss, PapiaBoss) and boss.orb:
                    orb_rect = pygame.Rect(boss.orb.pos.x - 20, boss.orb.pos.y - 20, 40, 40)
                    if player.attack_hitbox.colliderect(orb_rect):
                        boss.orb = None
                        boss.hp -= 1
                        player.attack_damage_applied = True

            # Boss hits Player
            boss_hit = False
            
            # 1. Generic Hitbox (ONLY IF ACTIVE) - Fixes damage during telegraph
            if hasattr(boss, 'attack_hitbox') and boss.attack_hitbox:
                if boss.attack_active and boss.attack_hitbox.colliderect(player.hurtbox()):
                    boss_hit = True
            
            # 2. Papia Projectiles
            if isinstance(boss, PapiaBoss):
                for m in boss.meteors:
                    # Check both impact AND air collision
                    if m.hits_player(player):
                        boss_hit = True
                if boss.orb and (boss.orb.pos - player.pos).length() < 40:
                    boss_hit = True
                    boss.orb = None 

            # 3. Harus Shockwaves & Swing
            if isinstance(boss, HarusBoss):
                # Shockwaves
                for s in boss.shockwaves:
                    if s.rect.colliderect(player.hurtbox()):
                        boss_hit = True
                        s.active = False 
                
                # Swing Tip (Axe Collision)
                if boss.attack_type == "swing" and boss.attack_active:
                    tip = boss.axe_tip_pos()
                    # Check distance from tip to player hurtbox
                    d = rect_point_distance(player.hurtbox(), tip)
                    if d <= boss.swing_tip_radius:
                        boss_hit = True

            if boss_hit and player.hit_recovery_timer <= 0:
                player.hp -= 1
                player.hit_recovery_timer = 1.0
                player.vel.x = -300 * player.facing

            if player.hp <= 0:
                if hasattr(boss, 'cleanup'): boss.cleanup()
                boss = None
                current_state = STATE_GAMEOVER
            elif boss.hp <= 0:
                if hasattr(boss, 'cleanup'): boss.cleanup()
                if current_state == STATE_GAME_PAPIA:
                    boss = None
                    current_state = STATE_TRANSITION
                else:
                    boss = None
                    current_state = STATE_ENDING

    # Shake Calculation
    offset = (0, 0)
    if shake_timer > 0:
        shake_timer -= dt
        offset = (random.randint(-int(shake_intensity), int(shake_intensity)), 
                  random.randint(-int(shake_intensity), int(shake_intensity)))

    # Draw
    screen.fill(BLACK)
    
    bg_rect_sky = pygame.Rect(0 + offset[0], 0 + offset[1], WIDTH, GROUND_Y)
    bg_rect_gnd = pygame.Rect(0 + offset[0], GROUND_Y + offset[1], WIDTH, HEIGHT-GROUND_Y)

    if current_state == STATE_MENU:
        draw_text_centered("FADING MEMORY")
        draw_text_centered("Press SPACE to Start", 50, GRAY)
        
    elif current_state == STATE_INTRO:
        draw_text_centered("I saw him kill her...", -40)
        draw_text_centered("To hunt him, I must move faster.", 0)
        draw_text_centered("I will sacrifice the memory of our First Date.", 40)
        draw_text_centered("[Press SPACE to Forget & Gain DASH]", 100, BLUE)
        
    elif current_state == STATE_GAME_PAPIA:
        pygame.draw.rect(screen, (30, 30, 40), bg_rect_sky) 
        pygame.draw.rect(screen, (20, 20, 20), bg_rect_gnd)
        player.draw(screen, offset)
        if boss: boss.draw(screen, offset)
        if boss: draw_ui(screen, player, "PAPIA", boss.hp, boss.max_hp)
        
    elif current_state == STATE_TRANSITION:
        draw_text_centered("Papia is dead. But he is still out there.", -40)
        draw_text_centered("To face the killer, I need strength.", 0)
        draw_text_centered("I will sacrifice the memory of her Voice.", 40)
        draw_text_centered("[Press SPACE to Forget & Continue]", 100, BLUE)

    elif current_state == STATE_GAME_HARUS:
        pygame.draw.rect(screen, (40, 0, 0), bg_rect_sky) 
        pygame.draw.rect(screen, (20, 20, 20), bg_rect_gnd)
        player.draw(screen, offset)
        if boss: boss.draw(screen, offset)
        if boss: draw_ui(screen, player, "HARUS (KILLER)", boss.hp, boss.max_hp)

    elif current_state == STATE_ENDING:
        memory_opacity = 0
        draw_text_centered("It is done.", -40)
        draw_text_centered("I have my revenge...", 0)
        draw_text_centered("But I cannot remember her name.", 40, RED)
        draw_ui(screen, player, "", 0, 1)

    elif current_state == STATE_GAMEOVER:
        draw_text_centered("YOU DIED", 0, RED)
        if checkpoint_reached:
             draw_text_centered("Press SPACE to Retry (Checkpoint: Harus)", 50)
        else:
             draw_text_centered("Press SPACE to Restart", 50)

    pygame.display.flip()

pygame.quit()