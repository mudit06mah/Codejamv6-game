# helma.py
# Final boss: Helma (sword + shield)
# Controls:
#   Move: A / D
#   Jump: W
#   Light attack: J
#   Dash: K
#   Heavy attack (deflects shield when timed): SPACE

import pygame, math, random
from pygame.math import Vector2

pygame.init()
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Helma: The Iron Wall")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("arial", 18)

GROUND_Y = 440
FPS = 60

# Colors
WHITE = (240,240,240)
RED = (200,60,60)
BLUE = (60,120,200)
YELLOW = (240,220,120)
ORANGE = (200,140,60)
GRAY = (40,40,40)
BLACK = (10,10,10)
GREEN = (80,200,120)
SILVER = (180,180,190)
DARK_METAL = (80,80,90)
MAGIC = (140, 90, 200)

BOSS_SCALE = 0.75

def rect_point_distance(rect: pygame.Rect, point: Vector2) -> float:
    dx = 0
    if point.x < rect.left:
        dx = rect.left - point.x
    elif point.x > rect.right:
        dx = point.x - rect.right
    dy = 0
    if point.y < rect.top:
        dy = rect.top - point.y
    elif point.y > rect.bottom:
        dy = point.y - rect.bottom
    return math.hypot(dx, dy)

# -------------------------
# Player (light attack, dash, heavy)
# -------------------------
class Player:
    def __init__(self):
        self.pos = Vector2(220, GROUND_Y)
        self.vel = Vector2(0,0)
        self.facing = 1
        self.on_ground = True
        self.hp = 12  # Slight HP buff for tougher fight

        # Light attack state
        self.attack_state = "ready"   # ready, windup, active, recovery
        self.attack_timer = 0
        self.attack_hitbox = None
        self.attack_damage_applied = False

        # Heavy attack (space) - big windup, active, recovery + cooldown
        self.heavy_state = "ready"    # ready, windup, active, recovery
        self.heavy_timer = 0
        self.heavy_cooldown = 0.0     # cooldown remaining
        # COOLDOWN INCREASED: You cannot spam heavy to break shield.
        # You must wait for the right moment.
        self.heavy_cooldown_time = 3.8 

        # Dash (K)
        self.dash_cooldown = 0.0
        self.dash_timer = 0.0
        self.is_dashing = False
        self.dash_speed = 740.0
        self.dash_time = 0.20
        self.dash_cooldown_time = 0.65
        self.invulnerable_during_dash = True

        # Launcher
        self.launcher_state = "ready"   # ready, windup, active, recovery
        self.launcher_timer = 0
        self.launcher_hitbox = None
        self.launcher_used = False

        # hit recovery invuln
        self.hit_recovery_timer = 0

        # jump
        self.jump_hold = 0

    def hurtbox(self):
        return pygame.Rect(self.pos.x-20, self.pos.y-80, 40, 80)

    def attack_tip(self) -> Vector2:
        if not self.attack_hitbox:
            return Vector2(self.pos.x, self.pos.y)
        if self.facing == 1:
            return Vector2(self.attack_hitbox.right, self.attack_hitbox.centery)
        else:
            return Vector2(self.attack_hitbox.left, self.attack_hitbox.centery)

    def start_light_attack(self):
        if self.attack_state != "ready" or self.is_dashing or self.heavy_state in ("windup","active"):
            return
        self.attack_state = "windup"
        self.attack_timer = 0.10
        self.attack_hitbox = None
        self.attack_damage_applied = False

    def start_heavy(self):
        if self.heavy_state != "ready" or self.is_dashing or self.attack_state in ("windup","active") or self.heavy_cooldown > 0:
            return
        self.heavy_state = "windup"
        self.heavy_timer = 0.25   # longer windup (telegraphed)
        self.heavy_cooldown = self.heavy_cooldown_time
        self.attack_damage_applied = False

    def start_dash(self):
        if self.dash_cooldown > 0 or self.is_dashing or self.attack_state != "ready" or self.heavy_state!="ready":
            return
        self.is_dashing = True
        self.dash_timer = self.dash_time
        self.dash_cooldown = self.dash_cooldown_time
        self.vel.x = self.dash_speed * self.facing
        if self.invulnerable_during_dash:
            self.hit_recovery_timer = self.dash_time

    def start_launcher(self):
        if self.attack_state != "ready" or self.heavy_state != "ready" or self.is_dashing:
            return
        self.launcher_state = "windup"
        self.launcher_timer = 0.12
        self.launcher_used = False

    def update(self, dt, keys):

        if keys[pygame.K_j] and keys[pygame.K_s] and self.launcher_state == "ready":
            self.start_launcher()

        # timers
        if self.hit_recovery_timer > 0:
            self.hit_recovery_timer -= dt
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.heavy_cooldown > 0:
            self.heavy_cooldown -= dt

        # gravity
        self.vel.y += 1300 * dt

        # movement allowed mostly only when not mid-attack windup/active (heavy winds up too)
        can_move = (self.attack_state in ("ready","recovery")) and (self.heavy_state in ("ready","recovery")) and not self.is_dashing

        if can_move:
            if keys[pygame.K_a]:
                self.facing = -1
                self.vel.x = -200
            elif keys[pygame.K_d]:
                self.facing = 1
                self.vel.x = 200
            else:
                self.vel.x = 0

            # jump
            if keys[pygame.K_w] and self.on_ground:
                self.vel.y = -300
                self.jump_hold = 0.3
                self.on_ground = False

            if not keys[pygame.K_w]:
                self.jump_hold = 0

            if self.jump_hold > 0:
                self.vel.y -= 900 * dt
                self.jump_hold -= dt

            # attack inputs
            if keys[pygame.K_j] and self.attack_state == "ready":
                self.start_light_attack()
            if keys[pygame.K_k]:
                self.start_dash()
            if keys[pygame.K_SPACE]:
                self.start_heavy()
        else:
            # restrict horizontal control during attack windups/active
            if self.attack_state in ("windup","active") or self.heavy_state in ("windup","active"):
                self.vel.x = 0

        # dash handling
        if self.is_dashing:
            self.dash_timer -= dt
            # stop at walls
            if self.pos.x < 20 or self.pos.x > WIDTH - 20:
                self.dash_timer = 0
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.vel.x = 0

        # Light attack state machine
        if self.attack_state == "windup":
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "active"
                self.attack_timer = 0.12
                offset = 48 * self.facing
                w, h = 56, 24
                x = self.pos.x + offset if self.facing == 1 else self.pos.x + offset - w
                self.attack_hitbox = pygame.Rect(x, self.pos.y - 60, w, h)
        elif self.attack_state == "active":
            if self.attack_hitbox:
                w = self.attack_hitbox.width
                offset = 48 * self.facing
                x = self.pos.x + offset if self.facing == 1 else self.pos.x + offset - w
                self.attack_hitbox.x = x
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "recovery"
                self.attack_timer = 0.20
                self.attack_hitbox = None
        elif self.attack_state == "recovery":
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_state = "ready"

        # Heavy attack state machine
        if self.heavy_state == "windup":
            self.heavy_timer -= dt
            # allow special visual hint by leaving player slightly immobile
            if self.heavy_timer <= 0:
                self.heavy_state = "active"
                self.heavy_timer = 0.18
                # heavy active: bigger hitbox and longer reach
                offset = 70 * self.facing
                w, h = 100, 28
                x = self.pos.x + offset if self.facing == 1 else self.pos.x + offset - w
                self.heavy_hitbox = pygame.Rect(x, self.pos.y - 62, w, h)
        elif self.heavy_state == "active":
            # follow player position
            if hasattr(self, 'heavy_hitbox'):
                w = self.heavy_hitbox.width
                offset = 70 * self.facing
                x = self.pos.x + offset if self.facing == 1 else self.pos.x + offset - w
                self.heavy_hitbox.x = x
            self.heavy_timer -= dt
            if self.heavy_timer <= 0:
                self.heavy_state = "recovery"
                self.heavy_timer = 0.45
                if hasattr(self, 'heavy_hitbox'):
                    del self.heavy_hitbox
        elif self.heavy_state == "recovery":
            self.heavy_timer -= dt
            if self.heavy_timer <= 0:
                self.heavy_state = "ready"

        if self.launcher_state == "windup":
            self.launcher_timer -= dt
            if self.launcher_timer <= 0:
                self.launcher_state = "active"
                self.launcher_timer = 0.14
                w, h = 36, 48
                x = self.pos.x + (32 * self.facing) - (w if self.facing == -1 else 0)
                y = self.pos.y - 72
                self.launcher_hitbox = pygame.Rect(x, y, w, h)
        elif self.launcher_state == "active":
            if self.launcher_hitbox:
                self.launcher_hitbox.x = (
                    self.pos.x + (32 * self.facing) - self.launcher_hitbox.width
                    if self.facing == -1 else
                    self.pos.x + 32
                )
            self.launcher_timer -= dt
            if self.launcher_timer <= 0:
                self.launcher_state = "recovery"
                self.launcher_timer = 0.28
                self.launcher_hitbox = None
        elif self.launcher_state == "recovery":
            self.launcher_timer -= dt
            if self.launcher_timer <= 0:
                self.launcher_state = "ready"

        # clamp horizontal speed (unless dashing)
        if abs(self.vel.x) > 400 and not self.is_dashing:
            self.vel.x = 400 * (1 if self.vel.x > 0 else -1)

        self.pos += self.vel * dt

        if self.pos.y >= GROUND_Y:
            self.pos.y = GROUND_Y
            self.vel.y = 0
            self.on_ground = True

    def draw(self):
        if self.launcher_hitbox:
            pygame.draw.rect(screen, (160, 200, 255), self.launcher_hitbox, 2)

        # flash when in hit recovery (but avoid flashing while dashing)
        if self.hit_recovery_timer > 0 and not self.is_dashing:
            if int(self.hit_recovery_timer*10) % 2 == 0:
                color = GREEN
            else:
                color = BLUE
        else:
            color = BLUE
        pygame.draw.rect(screen, color, self.hurtbox())

        # draw light attack hitbox
        if self.attack_hitbox:
            pygame.draw.rect(screen, YELLOW, self.attack_hitbox, 2)

        # draw heavy attack hitbox
        if hasattr(self, 'heavy_hitbox'):
            pygame.draw.rect(screen, MAGIC, self.heavy_hitbox, 2)

        # dash trail
        if self.is_dashing:
            for i in range(3):
                alpha = max(0, 200 - i*60)
                s = pygame.Surface((44,44), pygame.SRCALPHA)
                s.fill((120, 200, 255, alpha))
                screen.blit(s, (self.pos.x-22 - i*10*self.facing, self.pos.y-70))

# -------------------------
# Helma boss
# -------------------------
class HelmaBoss:
    def __init__(self):
        self.shield_disabled_timer = 0.0
        # SHIELD RECOVERS FASTER THAN PLAYER HEAVY (2.2s vs 3.8s)
        self.heavy_shield_break_time = 2.2 

        self.launcher_uses = 0
        self.max_launcher_uses = 2

        self.vel = Vector2(0, 0)
        self.on_ground = True

        self.pos = Vector2(700, GROUND_Y)
        self.hp = 40
        self.half_width = int(46 * BOSS_SCALE)
        self.hurt_height = int(160 * BOSS_SCALE)
        self.facing = -1
        self.state = "idle"   # idle, telegraph, active, recovery, stunned
        self.state_timer = 0.0

        # shield logic
        self.shield_up = True
        self.shield_timer = 0.0
        self.shield_cycle = 2.6   
        self.shield_down_duration = 1.1
        self.parry_window = False   
        self.parry_time = 0.0

        # attack choices and lock facing
        self.attack_facing = self.facing
        self.next_action_cooldown = 0.5 + random.random()*0.4 # Faster aggression

        # attack params
        self.attacks = ["slash", "dash_slash", "shield_bash", "launcher"]
        self.current_attack = None
        self.telegraph_time = 0.55
        self.active_time = 0.22
        self.recovery_time = 0.6

        # for visual telegraphs and hitboxes
        self.slash_angle = 0
        self.slash_radius = 170 # Increased radius
        self.slash_tip_radius = 26
        self.slash_start_angle = 0
        self.slash_target_angle = 0
        self._slash_rotation = 0
        self.attack_hitbox = None
        self._dash_velocity = 0 # store boss dash vel

        # stunned
        self.stunned_timer = 0.0

    def hurtbox(self):
        return pygame.Rect(self.pos.x-self.half_width, self.pos.y-self.hurt_height, self.half_width*2, self.hurt_height)

    def shield_rect(self):
        # shield is a circular/rect area in front of Helma
        w, h = int(60 * BOSS_SCALE), int(120 * BOSS_SCALE)
        if self.attack_facing == 1:
            return pygame.Rect(self.pos.x + 10 * self.attack_facing, self.pos.y - int(130*BOSS_SCALE), w, h)
        else:
            return pygame.Rect(self.pos.x - 10*self.attack_facing - w, self.pos.y - int(130*BOSS_SCALE), w, h)

    def update(self, dt, player):
        # Shield disabled by heavy
        if self.shield_disabled_timer > 0:
            self.shield_disabled_timer -= dt
            self.shield_up = False
        else:
            # shield can behave normally again
            pass

        # gravity
        if not self.on_ground:
            self.vel.y += 1400 * dt
            self.pos.y += self.vel.y * dt

        dist = abs(player.pos.x - self.pos.x)
        # decide facing when idle
        if self.state in ("idle","recovery"):
            self.facing = 1 if player.pos.x > self.pos.x else -1

        # stunned handling
        if self.state == "stunned":
            self.stunned_timer -= dt
            if self.stunned_timer <= 0:
                self.state = "recovery"
                self.state_timer = 0.6 # Recover fast from stun
                # drop shield briefly after stun
                self.shield_up = False
                self.shield_timer = 1.0
            return

        # shield auto-cycle (if not recently stunned)
        if self.shield_up:
            # while shield is up, occasionally open a parry window right before some attacks
            if self.parry_window:
                self.parry_time -= dt
                if self.parry_time <= 0:
                    self.parry_window = False
        else:
            # shield down state
            if self.shield_disabled_timer > 0:
                self.shield_up = False
            elif self.shield_timer > 0:
                self.shield_timer -= dt
            else:
                self.shield_up = True
                self.parry_window = False

        # action cooldown
        if self.next_action_cooldown > 0:
            self.next_action_cooldown -= dt

        # picking actions
        if self.state == "idle" and self.next_action_cooldown <= 0:
            r = random.random()

            can_launcher = (
                self.launcher_uses < self.max_launcher_uses
                and dist < 120
                and player.on_ground
            )

            if can_launcher and r < 0.25:
                self.start_attack("launcher")
            elif dist < 180:
                # CLOSE RANGE: High chance of Swing (Slash)
                # This gives the player more chances to Parry, but feels aggressive
                if r < 0.8: 
                    self.start_attack("slash")
                else:
                    self.start_attack("shield_bash")
            else:
                # LONG RANGE: Dash Slash
                self.start_attack("dash_slash")


        # update telegraph/active/recovery states
        if self.state == "telegraph":
            # telegraph anim 
            self.state_timer -= dt
            
            if self.current_attack == "slash":
                # INCREASED PARRY WINDOW:
                # Open window for the last 0.35s of telegraph (easier to hit)
                if self.state_timer <= 0.35:
                    if self.shield_up:
                        self.parry_window = True
                        self.parry_time = 0.1 # keep refreshing it until active

            if self.state_timer <= 0:
                self.start_active()

        elif self.state == "active":
            self.state_timer -= dt
            if self.current_attack == "slash":
                # rotate slash to target
                total = self.active_time
                elapsed = total - self.state_timer
                t = max(0.0, min(1.0, elapsed/total))
                # ease out
                t_eased = 1 - (1 - t)*(1 - t)
                self._slash_rotation = (1-t_eased)*self._slash_rotation + t_eased*self.slash_target_angle
                # compute tip and check hits
                tip = self.slash_tip_pos()
            elif self.current_attack == "dash_slash":
                pass
            elif self.current_attack == "shield_bash":
                pass

            if self.state_timer <= 0:
                self.end_attack()

        elif self.state == "recovery":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "idle"
                self.next_action_cooldown = 0.4 + random.random()*0.5

        if self.pos.y >= GROUND_Y:
            self.pos.y = GROUND_Y
            self.vel.y = 0
            self.on_ground = True


    # --------------------
    def start_attack(self, kind):
        # lock facing when starting
        self.attack_facing = self.facing
        self.current_attack = kind
        self.state = "telegraph"
        self.state_timer = self.telegraph_time if kind!="shield_bash" else self.telegraph_time*0.6
        self.next_action_cooldown = 0.5 + random.random()*0.5
        
        # attack-specific setup
        if kind == "slash":
            # WIDER ARC for better visuals and parry feel
            self.slash_radius = int(170*BOSS_SCALE)
            self.slash_tip_radius = int(28*BOSS_SCALE)
            if self.attack_facing == 1:
                self.slash_start_angle = -160 # Start further back
                self.slash_target_angle = 60  # End further down
            else:
                self.slash_start_angle = -20
                self.slash_target_angle = -240
            self._slash_rotation = self.slash_start_angle
            self.attack_hitbox = None
            
        elif kind == "dash_slash":
            # HUGE RANGE BUFF
            self.attack_hitbox = None
            self.dash_speed = 850  # Much faster
            self.dash_time = 0.35  # Longer dash
            
        elif kind == "shield_bash":
            self.attack_hitbox = None
        elif kind == "launcher":
            self.state = "telegraph"
            self.state_timer = 0.35
            self.current_attack = "launcher"
            self.attack_hitbox = None

    def start_active(self):
        self.state = "active"
        self.state_timer = self.active_time if self.current_attack!="shield_bash" else 0.18
        
        # During active, shield stops blocking (offensive usage)
        # Note: Parry window is closed now. You missed your chance to deflect.
        self.parry_window = False

        if self.current_attack == "slash":
            self._slash_rotation = self.slash_start_angle
            
        elif self.current_attack == "dash_slash":
            # HUGE HITBOX BUFF
            w, h = int(180 * BOSS_SCALE), int(28 * BOSS_SCALE) # Tripled width
            if self.attack_facing == 1:
                x = self.pos.x
            else:
                x = self.pos.x - w
            self.attack_hitbox = pygame.Rect(x, self.pos.y - 60, w, h)
            self._dash_velocity = self.dash_speed * self.attack_facing
            self.state_timer = self.dash_time # Active lasts as long as the dash
            
        elif self.current_attack == "shield_bash":
            w, h = int(60 * BOSS_SCALE), int(28 * BOSS_SCALE)
            if self.attack_facing == 1:
                x = self.pos.x + 18
            else:
                x = self.pos.x - 18 - w
            self.attack_hitbox = pygame.Rect(x, self.pos.y - 70, w, h)
            
        elif self.current_attack == "launcher":
            w, h = 48, 42
            if self.attack_facing == 1:
                x = self.pos.x + 24
            else:
                x = self.pos.x - 24 - w
            y = self.pos.y - 64
            self.attack_hitbox = pygame.Rect(x, y, w, h)

    def end_attack(self):
        self.state = "recovery"
        self.state_timer = self.recovery_time
        self.attack_hitbox = None
        # Shield comes back up unless disabled
        if not self.shield_up and self.shield_disabled_timer <= 0:
            self.shield_timer = self.shield_down_duration
        
        self.next_action_cooldown = 0.4 + random.random()*0.4

    def on_parried(self):
        # heavy attack successfully deflected the shield: stunned
        self.state = "stunned"
        self.stunned_timer = 1.2
        self.shield_up = False
        self.parry_window = False
        self.pos.x += -self.attack_facing * 50 # Bigger knockback on parry

    def slash_tip_pos(self):
        center = Vector2(self.pos.x, self.pos.y - int(120 * BOSS_SCALE))
        rad = math.radians(self._slash_rotation)
        tip = Vector2(math.cos(rad) * self.slash_radius, math.sin(rad) * self.slash_radius)
        return center + tip

    def draw(self):
        # draw body
        pygame.draw.rect(screen, DARK_METAL, self.hurtbox())

        # draw shield
        srect = self.shield_rect()

        # CASE 1: Shield disabled by heavy
        if self.shield_disabled_timer > 0:
            surf = pygame.Surface((srect.width, srect.height), pygame.SRCALPHA)
            surf.fill((120, 80, 80, 160))
            screen.blit(surf, (srect.x, srect.y))
            pygame.draw.rect(screen, (200, 120, 120), srect, 2)

        # CASE 2: Shield up
        elif self.shield_up:
            pygame.draw.rect(screen, SILVER, srect)
            # pulse glow
            a = int(80 + 80 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 180)))
            glow = pygame.Surface((srect.width, srect.height), pygame.SRCALPHA)
            glow.fill((200, 200, 220, a))
            screen.blit(glow, (srect.x, srect.y))

            # parry window highlight (VISUAL CUE FOR PLAYER)
            if self.parry_window:
                g = pygame.Surface((srect.width + 10, srect.height + 10), pygame.SRCALPHA)
                pygame.draw.ellipse(
                    g, (255, 255, 0, 200), # BRIGHT YELLOW
                    (0, 0, srect.width + 10, srect.height + 10), 8
                )
                screen.blit(g, (srect.x - 5, srect.y - 5))

        # CASE 3: Shield down normally
        else:
            surf = pygame.Surface((srect.width, srect.height), pygame.SRCALPHA)
            surf.fill((80, 80, 90, 120))
            screen.blit(surf, (srect.x, srect.y))

        # draw telegraphs / attacks
        if self.state in ("telegraph","active","recovery","stunned"):
            if self.current_attack == "slash":
                tip = self.slash_tip_pos()
                color = ORANGE if self.state == "telegraph" else RED if self.state == "active" else WHITE
                pygame.draw.circle(screen, color, (int(tip.x), int(tip.y)), self.slash_tip_radius, 2)
                center = Vector2(self.pos.x, self.pos.y - 120)
                pygame.draw.line(screen, color, (center.x, center.y), (tip.x, tip.y), 4)
                # sample arc
                for i in range(0, 11):
                    a = (i/10.0)
                    ang = (1-a)*self.slash_start_angle + a*self.slash_target_angle
                    p = center + Vector2(math.cos(math.radians(ang))*self.slash_radius, math.sin(math.radians(ang))*self.slash_radius)
                    pygame.draw.circle(screen, (90,90,90), (int(p.x), int(p.y)), 2)
            
            elif self.current_attack == "dash_slash":
                color = ORANGE if self.state == "telegraph" else RED if self.state == "active" else WHITE
                # Long telegraph line
                start = (self.pos.x, self.pos.y - 70)
                end = (self.pos.x + self.attack_facing * 300, self.pos.y - 70)
                pygame.draw.line(screen, color, start, end, 6)
                if self.attack_hitbox:
                    pygame.draw.rect(screen, RED if self.state=="active" else ORANGE, self.attack_hitbox, 2)
            
            elif self.current_attack == "shield_bash":
                color = ORANGE if self.state == "telegraph" else RED if self.state == "active" else WHITE
                srect = self.shield_rect()
                pygame.draw.circle(screen, color, (srect.centerx, srect.centery), 44, 3)
            
            elif self.current_attack == "launcher":
                color = ORANGE if self.state == "telegraph" else RED
                center = (int(self.pos.x), int(self.pos.y - 90))
                pygame.draw.circle(screen, color, center, 36, 3)

# -------------------------
# Game setup
# -------------------------
player = Player()
boss = HelmaBoss()
running = True

def player_hits_boss_light(player, boss):
    # returns tuple(hit, was_on_shield)
    if player.attack_state == "active" and player.attack_hitbox:
        # if shield up and attack hits shield_rect -> blocked
        srect = boss.shield_rect()
        if boss.shield_up and player.attack_hitbox.colliderect(srect):
            return (False, True)
        # otherwise if attack collides hurtbox -> damage
        if player.attack_hitbox.colliderect(boss.hurtbox()):
            return (True, False)
    return (False, False)

def player_hits_boss_heavy(player, boss):
    if player.heavy_state == "active" and hasattr(player, 'heavy_hitbox'):
        srect = boss.shield_rect()
        # heavy can deflect shield only during boss.parry_window (clear telegraph)
        if boss.shield_up and boss.parry_window and player.heavy_hitbox.colliderect(srect):
            return ("deflect", True)
        # heavy hitting hurtbox normally deals damage
        if player.heavy_hitbox.colliderect(boss.hurtbox()):
            return ("hit", False)
    return (False, False)


while running:
    dt = clock.tick(FPS)/1000.0
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    player.update(dt, keys)
    boss.update(dt, player)

    # Boss motion for dash_slash active phase: move boss forward while active
    if boss.state == "active" and boss.current_attack == "dash_slash" and boss.attack_hitbox:
        # move attack hitbox and boss simultaneously
        dx = boss._dash_velocity * dt
        boss.pos.x += dx
        boss.attack_hitbox.x += dx

    # ----------------
    # Collision & combat resolution
    # ----------------

    # Player light attack interactions
    hit, on_shield = player_hits_boss_light(player, boss)
    if on_shield:
        # blocked by shield: push player back and apply recovery penalty
        if player.attack_state == "active" and player.attack_hitbox:
            # simple bounce and damage to player (minor)
            if player.hit_recovery_timer <= 0:
                player.hit_recovery_timer = 0.45
                player.vel.x = -260 * boss.facing if player.pos.x > boss.pos.x else 260 * boss.facing
                player.attack_state = "recovery"
                player.attack_timer = 0.35
            
    elif hit:
        if not player.attack_damage_applied:
            # normal light attack only deals 1 HP, but if boss shield was down it's valid
            boss.hp -= 1
            player.attack_damage_applied = True
            # small stagger
            boss.pos.x += -boss.attack_facing * 8

    # Player heavy interactions
    heavy_result = player_hits_boss_heavy(player, boss)
    if heavy_result:
        res, was_shield = heavy_result
        if res == "deflect":
            # heavy used correctly: deflect shield, stun boss and deal damage
            boss.on_parried()
            boss.hp -= 2
            player.attack_damage_applied = True
            boss.shield_disabled_timer = boss.heavy_shield_break_time
        elif res == "hit":
            # heavy hit normal hurtbox
            if not player.attack_damage_applied:
                boss.hp -= 2
                player.attack_damage_applied = True
                boss.shield_disabled_timer = boss.heavy_shield_break_time


    if (
        boss.current_attack == "launcher"
        and boss.state == "active"
        and boss.attack_hitbox
        and boss.attack_hitbox.colliderect(player.hurtbox())
        and player.hit_recovery_timer <= 0
    ):
        player.vel.y = -480
        player.vel.x = 160 * boss.attack_facing
        player.on_ground = False
        player.hit_recovery_timer = 0.8
        boss.launcher_uses += 1
        player.hp -= 2 
        boss.end_attack()

    # Boss attack collisions on player
    # Slash: tip overlap distance check
    if boss.current_attack == "slash" and boss.state == "active":
        tip = boss.slash_tip_pos()
        d = rect_point_distance(player.hurtbox(), tip)
        if d <= boss.slash_tip_radius:
            if player.hit_recovery_timer <= 0 and not player.is_dashing:
                player.hp -= 2
                player.hit_recovery_timer = 0.9
                player.vel.x = -240 * boss.attack_facing
                boss.end_attack()

    # Dash slash rectangle
    if boss.attack_hitbox and boss.current_attack == "dash_slash" and boss.state == "active":
        if boss.attack_hitbox.colliderect(player.hurtbox()):
            if player.hit_recovery_timer <= 0 and not player.is_dashing:
                player.hp -= 3 # DASH HURTS MORE NOW
                player.hit_recovery_timer = 0.9
                player.vel.x = -300 * boss.attack_facing
                boss.end_attack()

    # shield bash active
    if boss.attack_hitbox and boss.current_attack == "shield_bash" and boss.state == "active":
        if boss.attack_hitbox.colliderect(player.hurtbox()):
            if player.hit_recovery_timer <= 0:
                player.hp -= 1
                player.hit_recovery_timer = 0.8
                player.vel.x = -180 * boss.attack_facing
                boss.end_attack()

    # If player dashes into boss shield
    if player.is_dashing and boss.shield_up:
        # simple check overlap
        if player.hurtbox().colliderect(boss.shield_rect()):
            if player.hit_recovery_timer <= 0:
                player.hit_recovery_timer = 0.35
                player.is_dashing = False
                player.vel.x = -200 * boss.attack_facing

    # If boss is stunned, allow player to hit freely (light attacks apply)
    if boss.state == "stunned":
        if player.attack_state == "active" and player.attack_hitbox and player.attack_hitbox.colliderect(boss.hurtbox()):
            if not player.attack_damage_applied:
                boss.hp -= 1
                player.attack_damage_applied = True

    # Clamp boss position to arena
    boss.pos.x = max(80, min(WIDTH-80, boss.pos.x))

    # ----------------
    # Draw
    # ----------------
    screen.fill(BLACK)
    pygame.draw.rect(screen, GRAY, (0,GROUND_Y,WIDTH,HEIGHT-GROUND_Y))

    player.draw()
    boss.draw()

    # HUD / indicators
    hud = [
        f"Player HP: {player.hp}",
        f"Light: J  |  Heavy: SPACE  |  Dash: K",
        f"Heavy Cooldown: {max(0, player.heavy_cooldown):.1f}s",
        f"Boss HP: {boss.hp}",
    ]
    for i, line in enumerate(hud):
        screen.blit(FONT.render(line, True, WHITE), (20, 18 + i*20))

    # Extra telegraph text when shield parry window is open
    if boss.parry_window and boss.shield_up:
        txt = FONT.render("!! PARRY NOW (SPACE) !!", True, YELLOW)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 100))

    pygame.display.flip()

pygame.quit()