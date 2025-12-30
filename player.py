import pygame
from pygame.math import Vector2
from settings import *

class Player:
    def __init__(self):
        self.pos = Vector2(220, GROUND_Y)
        self.vel = Vector2(0,0)
        self.facing = 1
        self.on_ground = True
        self.max_hp = 8
        self.hp = self.max_hp
        
        # Unlocks
        self.can_dash = False

        # Combat States
        self.attack_state = "ready"
        self.attack_timer = 0
        self.attack_hitbox = None
        self.attack_damage_applied = False
        self.cooldown = 0
        
        self.hit_recovery_timer = 0
        self.jump_hold = 0

        # Dash
        self.dash_cooldown = 0.0
        self.dash_timer = 0.0
        self.is_dashing = False
        self.dash_speed = 700.0
        self.dash_time = 0.14
        self.dash_cooldown_time = 0.6

        # Animations
        self.animations = {
            "idle": load_strip("assets/protag/idle.png", 4),
            "walk": load_strip("assets/protag/walk.png", 2),
            "windup": load_strip("assets/protag/windup.png", 2),
            "attack": load_strip("assets/protag/attack.png", 1),
            "recovery": load_strip("assets/protag/recovery.png", 1),
            "dash": load_strip("assets/protag/dash.png", 1)
        }
        self.anim_state = "idle"
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = {"idle": 0.25, "walk": 0.15, "windup": 0.10, "attack": 0.20, "recovery": 0.20, "dash": 0.1}

        # SFX
        try:
            self.sfx_dash = pygame.mixer.Sound("assets/SFX/DASH.wav")
            self.sfx_slash = pygame.mixer.Sound("assets/SFX/SWORD SLASH.wav")
            self.sfx_slash.set_volume(0.6)
        except:
            self.sfx_dash = None
            self.sfx_slash = None

    def hurtbox(self):
        return pygame.Rect(self.pos.x-20, self.pos.y-80, 40, 80)

    def start_attack(self):
        if self.attack_state != "ready" or self.is_dashing:
            return
        
        # CHANGED: Play SFX immediately here
        if self.sfx_slash: self.sfx_slash.play()
            
        self.attack_state = "windup"
        self.attack_timer = 0.10
        self.attack_hitbox = None
        self.attack_damage_applied = False
        
    def start_dash(self):
        if not self.can_dash: return
        if self.dash_cooldown > 0 or self.is_dashing or self.attack_state != "ready":
            return
        self.is_dashing = True
        self.dash_timer = self.dash_time
        self.dash_cooldown = self.dash_cooldown_time
        self.vel.x = self.dash_speed * self.facing
        self.hit_recovery_timer = self.dash_time
        if self.sfx_dash: self.sfx_dash.play()

    def update(self, dt, keys):
        if self.hit_recovery_timer > 0: self.hit_recovery_timer -= dt
        if self.dash_cooldown > 0: self.dash_cooldown -= dt
        if self.cooldown > 0: self.cooldown -= dt

        self.vel.y += 1300 * dt

        can_move = self.attack_state in ("ready", "recovery") and not self.is_dashing

        if can_move:
            if keys[pygame.K_a]:
                self.facing = -1
                self.vel.x = -200
            elif keys[pygame.K_d]:
                self.facing = 1
                self.vel.x = 200
            else:
                self.vel.x = 0

            if keys[pygame.K_w] and self.on_ground:
                self.vel.y = -300
                self.jump_hold = 0.3
                self.on_ground = False
            if not keys[pygame.K_w]:
                self.jump_hold = 0
            if self.jump_hold > 0:
                self.vel.y -= 900 * dt
                self.jump_hold -= dt

            if keys[pygame.K_j]: self.start_attack()
            if keys[pygame.K_k]: self.start_dash()
        else:
            if not self.is_dashing:
                self.vel.x = 0
        
        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.vel.x = 0

        if self.attack_state == "windup":
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "active"
                self.attack_timer = 0.12
                offset = 40 * self.facing 
                w, h = 50, 20
                x = self.pos.x + offset if self.facing == 1 else self.pos.x + offset - w
                self.attack_hitbox = pygame.Rect(x, self.pos.y - 60, w, h)
                
        elif self.attack_state == "active":
            if self.attack_hitbox:
                offset = 40 * self.facing
                x = self.pos.x + offset if self.facing == 1 else self.pos.x + offset - self.attack_hitbox.width
                self.attack_hitbox.x = x
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "recovery"
                self.attack_timer = 0.20
                self.attack_hitbox = None
                self.attack_damage_applied = False
                self.cooldown = 0.1
        elif self.attack_state == "recovery":
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "ready"

        if abs(self.vel.x) > 400 and not self.is_dashing:
            self.vel.x = 400 * (1 if self.vel.x > 0 else -1)
            
        self.pos += self.vel * dt
        
        if self.pos.y >= GROUND_Y:
            self.pos.y = GROUND_Y
            self.vel.y = 0
            self.on_ground = True
            
        self.update_animation(dt)

    def update_animation(self, dt):
        state = "idle"
        if self.is_dashing: state = "dash"
        elif self.attack_state == "windup": state = "windup"
        elif self.attack_state == "active": state = "attack"
        elif self.attack_state == "recovery": state = "recovery"
        elif not self.on_ground: state = "idle"
        elif abs(self.vel.x) > 10: state = "walk"
        
        if state != self.anim_state:
            self.anim_state = state
            self.anim_frame = 0
            self.anim_timer = 0
            
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed.get(state, 0.2):
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % len(self.animations[self.anim_state])

    def draw(self, screen, offset=(0,0)):
        if self.hit_recovery_timer > 0 and not self.is_dashing:
            if int(self.hit_recovery_timer * 10) % 2 == 0:
                return

        frames = self.animations.get(self.anim_state)
        if not frames: return
        
        frame = frames[self.anim_frame] if self.anim_frame < len(frames) else frames[0]
        SCALE = 2.0
        
        if self.facing == -1:
            frame = pygame.transform.flip(frame, True, False)
            
        frame = pygame.transform.scale(frame, (int(frame.get_width()*SCALE), int(frame.get_height()*SCALE)))
        
        draw_x = self.pos.x - frame.get_width() // 2 + offset[0]
        draw_y = self.pos.y - frame.get_height() + offset[1]
        screen.blit(frame, (draw_x, draw_y))