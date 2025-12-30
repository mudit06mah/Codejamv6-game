import pygame, math, random
from pygame.math import Vector2
from settings import *

def rect_point_distance(rect: pygame.Rect, point: Vector2) -> float:
    dx = 0
    if point.x < rect.left: dx = rect.left - point.x
    elif point.x > rect.right: dx = point.x - rect.right
    dy = 0
    if point.y < rect.top: dy = rect.top - point.y
    elif point.y > rect.bottom: dy = point.y - rect.bottom
    return math.hypot(dx, dy)

def ease_out(t):
    return 1 - (1 - t) * (1 - t)

# ==========================================
# PAPIA (Boss 1)
# ==========================================
class PapiaBoss:
    def __init__(self):
        self.pos = Vector2(700, GROUND_Y)
        self.hp = 25
        self.max_hp = 25
        self.half_hp = self.hp // 2
        
        self.half_width = 36
        self.hurt_height = 120
        self.state = "idle"
        self.facing = -1
        self.next_action_cooldown = 0.8
        self.meteors = []
        self.orb = None

        self.grid_positions = list(range(80, WIDTH-80, 40)) 
        self.meteor_count = 6
        self.meteor_delay_between = 0.14
        self.current_parity = 0

        self.orb_speed = 560.0
        self.orb_life = 1.7
        self.use_phase_combo = True
        self.combo_enabled = False

        self.is_casting = False
        self.cast_anim = 0.0
        
        self.shake_requested = 0

        # Sprites
        self.anim_idle = load_strip("assets/papia/idle..png", 7, 256, 256) 
        self.anim_cast = load_strip("assets/papia/cast.png", 7, 256, 256)
        self.frame_index = 0
        self.anim_timer = 0

        # SFX
        try:
            self.sfx_whisper = pygame.mixer.Sound("assets/SFX/PAPIA IDLE CARELESS WHISPERS.wav")
            self.sfx_whisper.set_volume(0.1) 
            self.sfx_spell = pygame.mixer.Sound("assets/SFX/SPELL ATTACK #1.wav")
            self.sfx_spell.set_volume(0.1) 
            
            # Start whispering immediately
            self.sfx_whisper.play(-1)
        except:
            self.sfx_whisper = None
            self.sfx_spell = None

    def hurtbox(self):
        return pygame.Rect(self.pos.x-self.half_width, self.pos.y-self.hurt_height, self.half_width*2, self.hurt_height)

    def cleanup(self):
        if self.sfx_whisper:
            self.sfx_whisper.stop()

    def update(self, dt, player):
        self.shake_requested = 0
        self.facing = 1 if player.pos.x > self.pos.x else -1
        
        self.anim_timer += dt
        if self.anim_timer > 0.15:
            self.anim_timer = 0
            frames = self.anim_cast if self.is_casting else self.anim_idle
            self.frame_index = (self.frame_index + 1) % len(frames)

        # Meteor + Shake
        for m in self.meteors:
            was_impact = m.impact
            m.update(dt)
            if not was_impact and m.impact:
                self.shake_requested = 5

        self.meteors = [m for m in self.meteors if not (m.impact and m.impact_timer <= 0)]
        
        if self.orb:
            if not self.orb.update(dt): self.orb = None

        if self.next_action_cooldown > 0: self.next_action_cooldown -= dt
        if self.cast_anim > 0:
            self.cast_anim -= dt
            if self.cast_anim <= 0: self.is_casting = False

        if self.use_phase_combo and not self.combo_enabled and self.hp <= self.half_hp:
            self.combo_enabled = True

        can_pick = (self.next_action_cooldown <= 0) and (len(self.meteors) == 0) and (self.orb is None) and (not self.is_casting)
        
        if self.state == "idle" and can_pick:
            r = random.random()
            combo_chance = 0.38 if self.combo_enabled else 0.0
            if r < combo_chance: self.start_combo(player)
            else:
                if random.random() < 0.65: self.start_meteor_shower(player)
                else: self.start_single_orb(player)

        if self.state != "idle" and not self.is_casting: self.state = "idle"

    def start_meteor_shower(self, player):
        if self.sfx_spell: self.sfx_spell.play()
        self.state = "casting_meteors"
        self.is_casting = True
        self.cast_anim = 0.9
        self.next_action_cooldown = 1.0 + random.random()*0.6
        self.frame_index = 0
        
        self.current_parity = random.choice([0,1])
        parity_positions = [ (i,x) for i,x in enumerate(self.grid_positions) if (i % 2) == self.current_parity ]
        base_x = int(player.pos.x)
        parity_positions.sort(key=lambda t: abs(t[1]-base_x))
        
        chosen = []
        near = sorted(parity_positions, key=lambda t: abs(t[1]-base_x))[:max(3, self.meteor_count)]
        
        temp_set = set()
        for i, x in near:
            if len(chosen) < self.meteor_count:
                chosen.append(x)
                temp_set.add(x)
        
        available = [x for i,x in parity_positions]
        random.shuffle(available)
        for x in available:
            if len(chosen) < self.meteor_count and x not in temp_set:
                chosen.append(x)
                
        for i,x in enumerate(chosen):
            m = Meteor(x, delay=0.9 + i*self.meteor_delay_between)
            self.meteors.append(m)

    def start_single_orb(self, player, delayed=0.0):
        if self.sfx_spell and delayed == 0: self.sfx_spell.play()
        self.state = "casting_orb"
        self.is_casting = True
        self.cast_anim = 0.55 + delayed
        self.next_action_cooldown = 1.0 + random.random()*0.5 + delayed
        self.frame_index = 0
        
        spawn_x = self.pos.x + random.randint(-40, 40)
        spawn_y = self.pos.y - 120 + random.randint(-10,10)
        orb = LargeOrb(Vector2(spawn_x, spawn_y), player, speed=self.orb_speed, life=self.orb_life)
        orb.windup += delayed
        self.orb = orb

    def start_combo(self, player):
        self.state = "casting_combo"
        self.is_casting = True
        self.cast_anim = 1.1
        self.next_action_cooldown = 1.6 + random.random()*0.6
        self.frame_index = 0
        self.start_meteor_shower(player)
        self.start_single_orb(player, delayed=0.45)

    def draw(self, screen, offset=(0,0)):
        frames = self.anim_cast if self.is_casting else self.anim_idle
        if frames:
            img = frames[self.frame_index % len(frames)]
            SCALE = 1.5
            if self.facing == -1: img = pygame.transform.flip(img, True, False)
            img = pygame.transform.scale(img, (int(img.get_width()*SCALE), int(img.get_height()*SCALE)))
            draw_x = self.pos.x - img.get_width() // 2 + offset[0]
            draw_y = self.pos.y - img.get_height() + offset[1]
            screen.blit(img, (draw_x, draw_y))
        
        for m in self.meteors: m.draw(screen, offset)
        if self.orb: self.orb.draw(screen, offset)
        
        if any((not m.active and not m.impact) for m in self.meteors):
            for i, x in enumerate(self.grid_positions):
                if (i % 2) == self.current_parity:
                    surf = pygame.Surface((30,30), pygame.SRCALPHA)
                    a = int(120 + 120 * (0.5 + 0.5*math.sin(pygame.time.get_ticks()/180 + i)))
                    pygame.draw.circle(surf, (220,70,40,a), (15,15), 12, 3)
                    screen.blit(surf, (x-15 + offset[0], GROUND_Y-15 + offset[1]))

class Meteor:
    def __init__(self, x, delay=1.1):
        self.x = x
        self.y = -80
        self.target_y = GROUND_Y - 6
        self.radius = 26
        self.windup = delay
        self.fall_speed = 700.0
        self.active = False
        self.impact = False
        self.impact_timer = 0.0
        
        # ANIMATION VARIABLES
        self.frames = load_strip("assets/effects/meteor.png", 4, 128, 128)
        self.frame_index = 0.0
        self.anim_speed = 12.0 # Speed of animation

    def update(self, dt):
        if self.impact:
            self.impact_timer -= dt
            return self.impact_timer > 0
        
        if self.windup > 0:
            self.windup -= dt
            if self.windup <= 0: self.active = True
            return True
            
        if self.active:
            # Animate while falling
            self.frame_index += self.anim_speed * dt
            
            self.y += self.fall_speed * dt
            if self.y >= self.target_y:
                self.y = self.target_y
                self.impact = True
                self.impact_timer = 0.30
                self.active = False
            return True
        return True

    def hits_player(self, player):
        # 1. Check Impact (Explosion on ground)
        if self.impact:
            center = Vector2(player.hurtbox().centerx, player.hurtbox().centery)
            d = math.hypot(center.x - self.x, center.y - GROUND_Y)
            return d <= (self.radius + 20)
        
        # 2. Check Air Collision (Falling)
        if self.active:
            tip = Vector2(self.x, self.y)
            d = rect_point_distance(player.hurtbox(), tip)
            return d <= 30 # Slightly larger for sprite
        return False

    def draw(self, screen, offset=(0,0)):
        x_draw = int(self.x + offset[0])
        y_draw_g = int(GROUND_Y + offset[1])
        y_draw_cur = int(self.y + offset[1])

        # 1. Telegraph (Shadow/Indicator on ground)
        if not self.active and not self.impact:
            t = max(0.0, min(1.0, 1.0 - self.windup / 1.0))
            r = int(self.radius + 10 * (0.8 + 0.2 * math.sin(pygame.time.get_ticks()/150)))
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            alpha = int(100 + 120 * t)
            pygame.draw.circle(surf, (220,90,40, alpha), (r, r), r, 3)
            screen.blit(surf, (x_draw - r, y_draw_g - r))

        # 2. Falling Meteor (New Sprite)
        if self.active:
            if self.frames:
                # Get current frame
                frame = self.frames[int(self.frame_index) % len(self.frames)]
                
                # Optional: Rotate frame to face down if needed (or random rotation)
                # frame = pygame.transform.rotate(frame, -90) 
                
                # Scale if 64x64 is too small/big
                SCALE = 1.5 
                frame = pygame.transform.scale(frame, (int(64*SCALE), int(64*SCALE)))
                
                # Center sprite on x,y
                draw_x = x_draw - frame.get_width() // 2
                draw_y = y_draw_cur - frame.get_height() // 2
                screen.blit(frame, (draw_x, draw_y))
            else:
                # Fallback if image fails to load
                pygame.draw.circle(screen, ORANGE, (x_draw, y_draw_cur), 12)

        # 3. Impact (Explosion)
        if self.impact:
            # You can also use the sprite here if you want it to "poof"
            # For now, keeping the shape-based explosion or use a single frame
            t = max(0.0, min(1.0, self.impact_timer / 0.30))
            r = int(self.radius * (1.2 + 1.4 * (1-t)))
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            a = int(180 * t)
            pygame.draw.circle(surf, (240,120,60,a), (r,r), r)
            screen.blit(surf, (x_draw - r, y_draw_g - r))

class LargeOrb:
    def __init__(self, pos, target_player, speed=520.0, life=2.0):
        self.pos = Vector2(pos)
        self.target_player = target_player
        self.speed = speed
        self.life = life
        self.radius = 20
        self.windup = 0.45
        self.launched = False
        self.vel = Vector2(0,0)
        self.color = PURPLE

    def update(self, dt):
        if self.windup > 0:
            self.windup -= dt
            if self.windup <= 0:
                dir = (self.target_player.pos - self.pos)
                if dir.length() == 0: dir = Vector2(1,0)
                self.vel = dir.normalize() * self.speed
                self.launched = True
            return True
        if self.life <= 0: return False
        if self.launched:
            to_player = (self.target_player.pos - self.pos)
            if to_player.length() > 0.1:
                desired = to_player.normalize() * self.speed
                self.vel = self.vel.lerp(desired, min(1.0, 2.0 * dt))
            self.pos += self.vel * dt
            self.pos.x = max(0, min(WIDTH, self.pos.x))
            self.pos.y = max(-200, min(HEIGHT+200, self.pos.y))
            self.life -= dt
        return True

    def draw(self, screen, offset=(0,0)):
        x_draw = int(self.pos.x + offset[0])
        y_draw = int(self.pos.y + offset[1])

        if self.windup > 0:
            t = max(0.0, min(1.0, 1.0 - self.windup / 0.45))
            r = int(self.radius + 10 * (1.0 - t))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (140,80,200, int(130*t)), (r,r), r, 3)
            screen.blit(s, (x_draw-r, y_draw-r))
        pygame.draw.circle(screen, self.color, (x_draw, y_draw), self.radius)
        g = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
        pygame.draw.circle(g, (120,60,180,60), (self.radius*2, self.radius*2), self.radius*2)
        screen.blit(g, (x_draw - self.radius*2, y_draw - self.radius*2))


# ==========================================
# HARUS (Boss 2)
# ==========================================
class Shockwave:
    def __init__(self, x, y, direction, frames):
        self.rect = pygame.Rect(x, y-40, 80, 60)
        self.speed = 380 * direction
        self.active = True
        self.frames = frames
        self.frame_idx = 0.0
        self.anim_speed = 10.0 
        self.direction = direction

    def update(self, dt):
        self.rect.x += self.speed * dt
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.active = False
        if self.frames:
            self.frame_idx += self.anim_speed * dt
            if self.frame_idx >= len(self.frames):
                self.frame_idx = 0.0

    def draw(self, screen, offset=(0,0)):
        if self.frames:
            frame = self.frames[int(self.frame_idx) % len(self.frames)]
            if self.direction == -1:
                frame = pygame.transform.flip(frame, True, False)
            SCALE = 0.8
            frame = pygame.transform.scale(frame, (int(frame.get_width()*SCALE), int(frame.get_height()*SCALE)))
            dx = self.rect.centerx - frame.get_width() // 2 + offset[0]
            dy = self.rect.bottom - frame.get_height() + offset[1]
            screen.blit(frame, (dx, dy))
        else:
            r = self.rect.copy()
            r.x += offset[0]
            r.y += offset[1]
            pygame.draw.rect(screen, RED, r, 2)


class HarusBoss:
    def __init__(self):
        self.pos = Vector2(700, GROUND_Y)
        self.hp = 45
        self.max_hp = 45
        self.state = "idle"
        self.timer = 0
        self.facing = -1
        
        self.half_width = 70
        self.attack_hitbox = None
        self.parry_window = False
        self.attack_active = False
        self.was_parried = False
        
        self.rotation = 0
        self.attack_type = None
        self.stunned_timer = 0
        self.shockwaves = []
        self.attack_facing = self.facing
        
        self.swing_reach = 160
        self.swing_tip_radius = 28
        self.swing_telegraph_time = 0.7
        self.swing_active_time = 0.35 
        self._shockwave_spawned = False
        self.prev_tip_y = None
        
        self.next_action_cooldown = 0.0
        self.shake_requested = 0

        self.animations = {
            "idle": load_strip("assets/harus/idle.png", 4, 256, 256),
            "walk": load_strip("assets/harus/walk.png", 4, 256, 256),
            "windup": load_strip("assets/harus/windup.png", 4, 256, 256),
            "attack": load_strip("assets/harus/attack.png", 3, 256, 256),
            "recover": load_strip("assets/harus/recover.png", 4, 256, 256),
            "spin": load_strip("assets/harus/spin.png", 4, 256, 256),
        }
        self.anim_state = "idle"
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.anim_speed = {"idle": 0.25, "walk": 0.15, "windup": 0.12, "attack": 0.10, "recover": 0.18, "spin": 0.10}

        self.shockwave_frames = load_strip("assets/effects/shockwave.png", 3, 256, 256)

        self.meteor_frames = load_strip("assets/effects/meteor.png", 4, 64, 64)

        # SFX
        try:
            self.sfx_swing = pygame.mixer.Sound("assets/SFX/AXE SWING.wav")
            self.sfx_grunt = pygame.mixer.Sound("assets/SFX/MALE GRUNT.wav")
            self.sfx_step = pygame.mixer.Sound("assets/SFX/BIG FOOTSTEPS(arush).wav")
            self.sfx_step.set_volume(0.6)
        except:
            self.sfx_swing = None
            self.sfx_grunt = None
            self.sfx_step = None
        
        self.is_walking_sfx = False

    def hurtbox(self):
        return pygame.Rect(self.pos.x-self.half_width, self.pos.y-180, self.half_width*2, 180)

    def cleanup(self):
        if self.sfx_step: self.sfx_step.stop()

    def axe_center(self) -> Vector2:
        return Vector2(self.pos.x, self.pos.y - 120)

    def axe_tip_pos(self) -> Vector2:
        center = self.axe_center()
        rad = math.radians(self.rotation)
        tip = Vector2(math.cos(rad)*self.swing_reach, math.sin(rad)*self.swing_reach)
        return center + tip

    def update(self, dt, player):
        self.shake_requested = 0
        dist = abs(player.pos.x - self.pos.x)
        
        if self.state == "idle":
            self.facing = 1 if player.pos.x > self.pos.x else -1
            
        if self.state == "stunned":
            self.stunned_timer -= dt
            if self.stunned_timer <= 0:
                self.state = "recovery"
                self.timer = 0.7
            return

        if self.next_action_cooldown > 0:
            self.next_action_cooldown -= dt

        # Walk Sound Logic
        moving = (self.state == "idle" and dist > 350)
        
        if moving:
            self.pos.x += (1 if player.pos.x > self.pos.x else -1) * 90 * dt
            if not self.is_walking_sfx and self.sfx_step:
                self.sfx_step.play(-1)
                self.is_walking_sfx = True
        else:
            if self.is_walking_sfx and self.sfx_step:
                self.sfx_step.stop()
                self.is_walking_sfx = False

        # AI Logic
        if self.state == "idle":
            if dist <= 350:
                if self.next_action_cooldown <= 0:
                    r = random.random()
                    if dist < 160:
                        if r < 0.7: self.start_spin()
                        else: self.start_swing()
                    elif dist < 350:
                        if r < 0.2: self.start_spin()
                        else: self.start_swing()
                    else:
                        self.next_action_cooldown = 0.6

        elif self.state == "telegraph":
            self.timer -= dt
            if self.attack_type == "swing":
                self.rotation = self.swing_start_angle
                self.parry_window = False
                self.attack_active = False
            else:
                self.rotation += 120 * dt
                self.parry_window = False
                
            if self.timer <= 0:
                self.state = "parry"
                self.timer = 0.12
                self.parry_window = False
                self.attack_facing = self.facing
                self._shockwave_spawned = False
                
        elif self.state == "parry":
            self.timer -= dt
            if self.timer <= 0:
                self.start_active()
                
        elif self.state == "active":
            tip = self.axe_tip_pos()
            
            if self.attack_type == "swing":
                if self.prev_tip_y is not None:
                    crossed_ground = (self.prev_tip_y < GROUND_Y - 6 and tip.y >= GROUND_Y - 6)
                    if crossed_ground and not self._shockwave_spawned:
                        self.spawn_shockwave()
                        self._shockwave_spawned = True
                        self.shake_requested = 10 
                self.prev_tip_y = tip.y
                
                total = self.swing_active_time
                elapsed = total - self.timer
                t = max(0.0, min(1.0, elapsed / total))
                t_eased = ease_out(t)
                self.rotation = (1 - t_eased) * self.swing_start_angle + t_eased * self.swing_target_angle
                self.attack_active = True
                
            self.timer -= dt
            if self.timer <= 0:
                self.end_attack()
                
        elif self.state == "recovery":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "idle"
                self.was_parried = False
                self.parry_window = False
                self.attack_hitbox = None
                self.attack_active = False
                self.next_action_cooldown = 0.4
                
        for s in self.shockwaves: s.update(dt)
        self.shockwaves = [s for s in self.shockwaves if s.active]
        
        self.update_animation(dt, player)

    def start_swing(self):
        if self.sfx_swing: self.sfx_swing.play()
        self.attack_facing = self.facing
        self.state = "telegraph"
        self.attack_type = "swing"
        self.swing_telegraph_time = 0.7
        self.swing_active_time = 0.35
        self.timer = self.swing_telegraph_time
        self.swing_reach = 160
        self.swing_tip_radius = 28
        
        if self.attack_facing == 1:
            self.swing_start_angle = -200
            self.swing_target_angle = 60
        else:
            self.swing_start_angle = 20
            self.swing_target_angle = -240
            
        self.rotation = self.swing_start_angle
        self.prev_tip_y = None
        self.was_parried = False
        self.parry_window = False
        self.attack_active = False
        self.attack_hitbox = None
        self._shockwave_spawned = False

    def start_spin(self):
        if self.sfx_swing: self.sfx_swing.play()
        self.attack_facing = self.facing
        self.state = "telegraph"
        self.attack_type = "spin"
        self.swing_telegraph_time = 0.8
        self.sw_spin_active_time = 0.75
        self.timer = self.swing_telegraph_time
        self.rotation = 0
        self.was_parried = False
        self.parry_window = False
        reach = 400
        height = 70
        x = self.pos.x - reach // 2
        self.attack_hitbox = pygame.Rect(x, self.pos.y - 90, reach, height)

    def start_active(self):
        self.state = "active"
        if self.sfx_grunt: self.sfx_grunt.play()
        
        self.timer = self.swing_active_time if self.attack_type == "swing" else self.sw_spin_active_time
        self.attack_active = True
        self.parry_window = True
        if self.attack_type == "swing":
            self.rotation = self.swing_start_angle

    def end_attack(self):
        self.state = "recovery"
        self.timer = 1.0
        self.attack_active = False
        self.attack_hitbox = None
        self.parry_window = False

    def on_parried(self):
        self.was_parried = True
        self.state = "stunned"
        self.stunned_timer = 0.9
        self.attack_hitbox = None
        self.attack_active = False
        self.parry_window = False
        self.pos.x -= self.attack_facing * 30

    def spawn_shockwave(self):
        self.shockwaves.append(Shockwave(self.pos.x+5 + self.attack_facing*120, self.pos.y, self.attack_facing, self.shockwave_frames))

    def update_animation(self, dt, player):
        if self.state == "telegraph": state = "windup"
        elif self.state == "active": state = "spin" if self.attack_type == "spin" else "attack"
        elif self.state in ("recovery", "stunned"): state = "recover"
        else: state = "walk" if abs(player.pos.x - self.pos.x) > 300 else "idle"
            
        if state != self.anim_state:
            self.anim_state = state
            self.anim_frame = 0
            self.anim_timer = 0.0
            
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed[self.anim_state]:
            self.anim_timer = 0
            self.anim_frame += 1
            if self.anim_frame >= len(self.animations[self.anim_state]):
                if self.anim_state in ("attack", "windup"):
                    self.anim_frame = len(self.animations[self.anim_state]) - 1
                else:
                    self.anim_frame = 0

    def draw(self, screen, offset=(0,0)):
        frames = self.animations[self.anim_state]
        if frames:
            frame = frames[self.anim_frame % len(frames)]
            if self.facing == -1: frame = pygame.transform.flip(frame, True, False)
            BOSS_SCALE = 2.0
            frame = pygame.transform.scale(frame, (int(frame.get_width() * BOSS_SCALE), int(frame.get_height() * BOSS_SCALE)))
            draw_x = self.pos.x - frame.get_width() // 2 + offset[0]
            draw_y = self.pos.y - frame.get_height() + offset[1]
            screen.blit(frame, (draw_x, draw_y))
        else:
            r = self.hurtbox()
            r.x += offset[0]
            r.y += offset[1]
            pygame.draw.rect(screen, RED, r)

        for s in self.shockwaves: s.draw(screen, offset)