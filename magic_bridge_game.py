#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Magic Bouncy Bridge - Kid-Friendly Glass Bridge Game

A super cute bouncy bridge game for kids (age 5+)!
Inspired by Squid Game's Glass Bridge, but 100% safe and fun.
No death, no elimination, only cute falling + bouncing back!

Install: pip install pygame       (or: pip install pygame-ce for Python 3.14)
Run:     python3 magic_bridge_game.py

Controls:
  - Click LEFT side of screen = pick TOP pad
  - Click RIGHT side of screen = pick BOTTOM pad
  - Arrow keys LEFT/RIGHT also work
  - SPACE = start game
  - R = restart
"""

# ============================================================
# Imports
# ============================================================
import random
import math
import sys
import os

try:
    import pygame
except ImportError:
    print("=" * 50)
    print("Cannot find pygame!")
    print("")
    print("Please install it first:")
    print("  pip3 install pygame-ce   (for Python 3.14)")
    print("  pip3 install pygame      (for other versions)")
    print("=" * 50)
    sys.exit(1)

# ============================================================
# Initialize Pygame
# ============================================================
SOUND_ENABLED = False
try:
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.init()
    pygame.mixer.init()
    SOUND_ENABLED = True
except Exception:
    try:
        pygame.init()
    except Exception:
        pass
    SOUND_ENABLED = False

# ============================================================
# Game Constants (easy to tweak!)
# ============================================================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# -- Falling animation parameters --
# The falling effect uses simple physics:
#   velocity_y starts at -3 (small upward bounce)
#   each frame: velocity_y += GRAVITY  (accelerates downward)
#   each frame: bear_y += velocity_y   (moves the bear)
#   bear_x oscillates using sin(time) for a swaying effect
#   when bear_y reaches FALL_TARGET_Y, the bear bounces back
GRAVITY = 0.35                          # gravity acceleration per frame
FALL_TARGET_Y = SCREEN_HEIGHT * 0.72    # how far down the bear falls
BOUNCE_VELOCITY = -8.0                  # bounce-back speed (negative = upward)
FALL_SWING_AMPLITUDE = 25               # left-right sway while falling
FALL_SWING_SPEED = 6.0                  # sway speed
MAX_FALL_TIME = 1.5                     # max fall+bounce time (seconds)
SCREEN_SHAKE_AMOUNT = 4                 # screen shake intensity (pixels)

# -- Pad settings --
TOTAL_STEPS = 12            # how many steps on the bridge (10-14)
BOUNCE_CHANCE = 0.25        # chance of a bouncy pad (25%)

# ============================================================
# Colors
# ============================================================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 250)
LIGHT_BLUE = (173, 216, 255)
SAFE_GREEN = (100, 220, 100)
SAFE_GREEN_DARK = (70, 180, 70)
BOUNCE_PINK = (255, 150, 200)
BOUNCE_PINK_DARK = (220, 120, 170)
BOUNCE_YELLOW = (255, 230, 100)
GOLD = (255, 215, 0)
RED = (255, 100, 100)
ORANGE = (255, 180, 80)
PURPLE = (180, 130, 255)
RAINBOW_COLORS = [
    (255, 100, 100), (255, 180, 80), (255, 230, 100),
    (100, 220, 100), (100, 180, 255), (180, 130, 255)
]
CLOUD_WHITE = (255, 255, 255)
CLOUD_LIGHT = (240, 248, 255)
BALLOON_RED = (255, 80, 80)
BALLOON_BLUE = (80, 150, 255)
BALLOON_YELLOW = (255, 230, 50)
BALLOON_GREEN = (80, 220, 120)

# ============================================================
# Sound Generation (no external files needed!)
# ============================================================
def _make_sound(freq_start, freq_end, duration_ms, volume=0.25, overtone=0.0):
    """Generate a simple synthesized sound effect."""
    if not SOUND_ENABLED:
        return None
    try:
        sr = 22050
        n = int(sr * duration_ms / 1000.0)
        buf = bytearray(n * 2)
        mx = int(32767 * volume)
        for i in range(n):
            t = i / sr
            p = i / n
            freq = freq_start + (freq_end - freq_start) * p
            val = math.sin(2.0 * math.pi * freq * t)
            if overtone > 0:
                val += overtone * math.sin(2.0 * math.pi * freq * 2 * t)
            fade = 1.0 - p * 0.4
            s = int(val * mx * fade)
            s = max(-32768, min(32767, s))
            buf[i * 2] = s & 0xFF
            buf[i * 2 + 1] = (s >> 8) & 0xFF
        return pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        return None


snd_jump = _make_sound(600, 1000, 200, 0.25)        # happy jump: rising tone
snd_fall = _make_sound(500, 200, 400, 0.2)           # fall: descending tone
snd_bounce = _make_sound(300, 900, 250, 0.3, 0.3)   # bounce: boing!
# victory: multi-note fanfare
snd_victory = None
if SOUND_ENABLED:
    try:
        sr = 22050
        dur = 800
        n = int(sr * dur / 1000.0)
        buf = bytearray(n * 2)
        mx = int(32767 * 0.25)
        notes = [523, 659, 784, 1047]  # C5 E5 G5 C6
        for i in range(n):
            t = i / sr
            p = i / n
            freq = notes[min(int(p * len(notes)), len(notes) - 1)]
            val = math.sin(2 * math.pi * freq * t) + 0.5 * math.sin(4 * math.pi * freq * t)
            s = int(val * mx * (1 - p * 0.3))
            s = max(-32768, min(32767, s))
            buf[i * 2] = s & 0xFF
            buf[i * 2 + 1] = (s >> 8) & 0xFF
        snd_victory = pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        pass


def play_sound(sound):
    if sound and SOUND_ENABLED:
        try:
            sound.play()
        except Exception:
            pass


# ============================================================
# Display Setup
# ============================================================
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Magic Bouncy Bridge")
clock = pygame.time.Clock()

# ============================================================
# Fonts (use default pygame font - works everywhere!)
# ============================================================
font_large = pygame.font.Font(None, 52)
font_medium = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 26)
font_tiny = pygame.font.Font(None, 22)


# ============================================================
# Drawing Helpers
# ============================================================
def draw_star(surface, x, y, size, color, rotation=0):
    """Draw a 5-pointed star."""
    pts = []
    for i in range(10):
        a = math.radians(rotation + i * 36 - 90)
        r = size if i % 2 == 0 else size * 0.4
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    if len(pts) >= 3:
        pygame.draw.polygon(surface, color, pts)


def draw_cloud(surface, x, y, scale=1.0, color=CLOUD_WHITE):
    """Draw a cute puffy cloud."""
    s = scale
    pygame.draw.circle(surface, color, (int(x), int(y)), int(25 * s))
    pygame.draw.circle(surface, color, (int(x - 20 * s), int(y + 5 * s)), int(20 * s))
    pygame.draw.circle(surface, color, (int(x + 20 * s), int(y + 5 * s)), int(20 * s))
    pygame.draw.circle(surface, color, (int(x - 10 * s), int(y - 10 * s)), int(18 * s))
    pygame.draw.circle(surface, color, (int(x + 10 * s), int(y - 10 * s)), int(18 * s))


def draw_balloon(surface, x, y, color, size=20):
    """Draw a balloon with string."""
    pygame.draw.ellipse(surface, color,
                        (int(x - size * 0.6), int(y - size), int(size * 1.2), int(size * 1.4)))
    hi = tuple(min(255, c + 60) for c in color)
    pygame.draw.circle(surface, hi, (int(x - size * 0.15), int(y - size * 0.5)), int(size * 0.2))
    tri = [(int(x), int(y + size * 0.4)),
           (int(x - size * 0.15), int(y + size * 0.3)),
           (int(x + size * 0.15), int(y + size * 0.3))]
    pygame.draw.polygon(surface, color, tri)
    pygame.draw.line(surface, (150, 150, 150),
                     (int(x), int(y + size * 0.4)), (int(x), int(y + size * 0.9)), 1)


def draw_rainbow(surface, x, y, radius=60):
    """Draw a half-circle rainbow."""
    colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0),
              (0, 200, 0), (0, 150, 255), (75, 0, 130), (148, 0, 211)]
    for i, c in enumerate(colors):
        r = radius - i * 6
        if r > 5:
            pygame.draw.arc(surface, c, pygame.Rect(int(x - r), int(y - r), r * 2, r * 2),
                            0, math.pi, 4)


# ============================================================
# Particle System (stars, bubbles, confetti)
# ============================================================
class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime, shape='circle', size=5):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.shape = shape
        self.size = size
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-5, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.lifetime -= 1
        self.rotation += self.rot_speed

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        alpha = max(0, self.lifetime / self.max_lifetime)
        sz = max(1, int(self.size * alpha))
        dx, dy = int(self.x), int(self.y)
        if self.shape == 'circle':
            pygame.draw.circle(surface, self.color, (dx, dy), sz)
        elif self.shape == 'star':
            draw_star(surface, dx, dy, sz, self.color, self.rotation)
        elif self.shape == 'confetti':
            w, h = max(2, sz * 2), max(1, sz)
            pygame.draw.rect(surface, self.color, (dx - w // 2, dy - h // 2, w, h))

    @property
    def alive(self):
        return self.lifetime > 0


particles = []


def spawn_stars(x, y, count=8):
    for _ in range(count):
        particles.append(Particle(
            x, y, random.uniform(-3, 3), random.uniform(-4, -1),
            random.choice(RAINBOW_COLORS + [GOLD, WHITE]),
            random.randint(30, 50), 'star', random.randint(4, 8)))


def spawn_confetti(x, y, count=15):
    for _ in range(count):
        particles.append(Particle(
            x, y, random.uniform(-5, 5), random.uniform(-6, -1),
            random.choice(RAINBOW_COLORS),
            random.randint(40, 70), 'confetti', random.randint(3, 7)))


def spawn_bubbles(x, y, count=6):
    for _ in range(count):
        particles.append(Particle(
            x, y, random.uniform(-2, 2), random.uniform(-3, -0.5),
            random.choice([LIGHT_BLUE, CLOUD_WHITE, (200, 230, 255), PURPLE]),
            random.randint(25, 45), 'circle', random.randint(5, 12)))


def spawn_fireworks(x, y, count=30):
    for _ in range(count):
        a = random.uniform(0, math.pi * 2)
        sp = random.uniform(2, 7)
        particles.append(Particle(
            x, y, math.cos(a) * sp, math.sin(a) * sp,
            random.choice(RAINBOW_COLORS + [GOLD, WHITE]),
            random.randint(40, 80),
            random.choice(['star', 'confetti', 'circle']),
            random.randint(4, 10)))


# ============================================================
# Bear Character Drawing
# ============================================================
def draw_bear(surface, x, y, size, expression='happy', rotation=0):
    """
    Draw a cute bear character.
    expression: 'happy', 'surprised' (falling), 'super_happy' (bounced back)
    """
    temp_sz = size * 3
    temp = pygame.Surface((temp_sz, temp_sz), pygame.SRCALPHA)
    cx, cy = temp_sz // 2, temp_sz // 2
    s = size

    body_col = (180, 130, 80)
    belly_col = (240, 210, 170)
    ear_col = (150, 100, 60)
    cheek_col = (255, 180, 180)
    nose_col = (80, 50, 30)

    # Body
    pygame.draw.ellipse(temp, body_col, (cx - s // 2, cy - int(s * 0.3), s, int(s * 1.1)))
    # Belly
    pygame.draw.ellipse(temp, belly_col, (cx - int(s * 0.3), cy + int(s * 0.05),
                                          int(s * 0.6), int(s * 0.6)))
    # Head
    pygame.draw.ellipse(temp, body_col, (cx - int(s * 0.45), cy - int(s * 0.8),
                                         int(s * 0.9), int(s * 0.75)))
    # Ears
    for side in [-1, 1]:
        ex = cx + side * int(s * 0.35)
        ey = cy - int(s * 0.75)
        pygame.draw.circle(temp, ear_col, (ex, ey), int(s * 0.18))
        pygame.draw.circle(temp, cheek_col, (ex, ey), int(s * 0.1))

    fx, fy = cx, cy - int(s * 0.45)  # face center

    # Cheeks
    for side in [-1, 1]:
        pygame.draw.circle(temp, cheek_col,
                           (fx + side * int(s * 0.25), fy + int(s * 0.1)), int(s * 0.1))
    # Nose
    pygame.draw.circle(temp, nose_col, (fx, fy + int(s * 0.05)), int(s * 0.08))

    if expression == 'happy':
        # Dot eyes with highlights
        for side in [-1, 1]:
            pygame.draw.circle(temp, BLACK, (fx + side * int(s * 0.15), fy - int(s * 0.05)),
                               int(s * 0.06))
            pygame.draw.circle(temp, WHITE,
                               (fx + side * int(s * 0.15) + side * 2, fy - int(s * 0.07)),
                               int(s * 0.025))
        # Smile arc
        sr = pygame.Rect(fx - int(s * 0.12), fy + int(s * 0.05), int(s * 0.24), int(s * 0.12))
        pygame.draw.arc(temp, nose_col, sr, math.pi + 0.2, 2 * math.pi - 0.2, 2)

    elif expression == 'surprised':
        # Star eyes!
        for side in [-1, 1]:
            draw_star(temp, fx + side * int(s * 0.15), fy - int(s * 0.05), int(s * 0.1), GOLD)
        # O mouth
        pygame.draw.circle(temp, nose_col, (fx, fy + int(s * 0.12)), int(s * 0.08))
        pygame.draw.circle(temp, (255, 150, 150), (fx, fy + int(s * 0.12)), int(s * 0.05))
        # Raised arms
        for side in [-1, 1]:
            ax = cx + side * int(s * 0.5)
            ay = cy - int(s * 0.2)
            bx = cx + side * int(s * 0.75)
            by = ay - int(s * 0.3)
            pygame.draw.line(temp, body_col, (ax, ay), (bx, by), max(3, int(s * 0.12)))
            pygame.draw.circle(temp, belly_col, (bx, by), int(s * 0.08))

    elif expression == 'super_happy':
        # ^_^ squint eyes
        for side in [-1, 1]:
            ex = fx + side * int(s * 0.15) - int(s * 0.07)
            ey = fy - int(s * 0.12)
            pygame.draw.arc(temp, BLACK, (ex, ey, int(s * 0.14), int(s * 0.12)),
                            0, math.pi, 2)
        # Big happy mouth
        sr = pygame.Rect(fx - int(s * 0.15), fy + int(s * 0.02), int(s * 0.3), int(s * 0.18))
        pygame.draw.arc(temp, nose_col, sr, math.pi + 0.1, 2 * math.pi - 0.1, 2)
        pygame.draw.ellipse(temp, (255, 150, 150),
                            (fx - int(s * 0.1), fy + int(s * 0.06), int(s * 0.2), int(s * 0.1)))

    # Rotation
    if rotation != 0:
        temp = pygame.transform.rotate(temp, rotation)

    rect = temp.get_rect(center=(int(x), int(y)))
    surface.blit(temp, rect)


# ============================================================
# Pad Class
# ============================================================
class Pad:
    """A bridge pad: either Safe (green smiley) or Bouncy (pink spring)."""
    def __init__(self, index, is_left, is_safe):
        self.index = index
        self.is_left = is_left
        self.is_safe = is_safe
        self.revealed = False
        self.spring_anim = 0
        self.bounce_offset = 0

        start_x = 80
        end_x = SCREEN_WIDTH - 80
        spacing = (end_x - start_x) / (TOTAL_STEPS + 1)

        self.width = 52
        self.height = 40
        self.x = int(start_x + spacing * (index + 1))
        self.y = 280 if is_left else 340

    def update(self):
        if self.spring_anim > 0:
            self.spring_anim -= 1
            p = self.spring_anim / 20.0
            self.bounce_offset = math.sin(p * math.pi * 3) * 8 * p
        else:
            self.bounce_offset = 0

    def trigger_spring(self):
        self.spring_anim = 20

    def draw(self, surface, highlight=False):
        dy = self.y + int(self.bounce_offset)

        if self.revealed:
            col = SAFE_GREEN if self.is_safe else BOUNCE_PINK
            dark = SAFE_GREEN_DARK if self.is_safe else BOUNCE_PINK_DARK
        else:
            col = (200, 180, 255)
            dark = (170, 150, 220)

        # Shadow
        pygame.draw.rect(surface, (100, 100, 120),
                         (self.x - self.width // 2 + 3, dy - self.height // 2 + 3,
                          self.width, self.height), border_radius=8)
        # Body
        r = pygame.Rect(self.x - self.width // 2, dy - self.height // 2,
                        self.width, self.height)
        pygame.draw.rect(surface, col, r, border_radius=8)
        pygame.draw.rect(surface, dark, r, 3, border_radius=8)

        # Highlight glow
        if highlight:
            gr = pygame.Rect(self.x - self.width // 2 - 4, dy - self.height // 2 - 4,
                             self.width + 8, self.height + 8)
            pygame.draw.rect(surface, GOLD, gr, 3, border_radius=10)

        # Icons
        if self.revealed:
            if self.is_safe:
                # Smiley face
                pygame.draw.circle(surface, BLACK, (self.x - 7, dy - 5), 3)
                pygame.draw.circle(surface, BLACK, (self.x + 7, dy - 5), 3)
                pygame.draw.arc(surface, BLACK,
                                (self.x - 8, dy, 16, 8), math.pi + 0.3, 2 * math.pi - 0.3, 2)
            else:
                # Spring + star
                sx, sy = self.x, dy - 5
                for i in range(4):
                    yo = sy + i * 5
                    xo = 6 if i % 2 == 0 else -6
                    pygame.draw.line(surface, BOUNCE_YELLOW, (sx - xo, yo), (sx + xo, yo + 5), 2)
                draw_star(surface, sx, sy - 6, 6, GOLD)
        else:
            # Question mark
            t = font_small.render("?", True, WHITE)
            surface.blit(t, t.get_rect(center=(self.x, dy)))


# ============================================================
# Main Game Class
# ============================================================
class Game:
    ST_TITLE = 'title'
    ST_PLAYING = 'playing'
    ST_FALLING = 'falling'
    ST_BOUNCING = 'bouncing'
    ST_MESSAGE = 'message'
    ST_ADVANCING = 'advancing'
    ST_VICTORY = 'victory'

    # Encouraging messages shown after bouncing back
    ENCOURAGEMENTS = [
        "Oops! Haha~ No worries!",
        "Wheee~ That was fun!",
        "Boing! Let's try again!",
        "Haha~ We're the best!",
        "Bouncy bouncy~ So fun!",
        "Oopsie daisy~ Try again!",
        "That was silly! Hehe~",
        "Magic spring to the rescue!",
    ]
    SUB_MESSAGES = [
        "Balloon saved you~ Flying up!",
        "Cloud caught you! So cool!",
        "Magic spring~ Boing~ You're back!",
        "Up up and away~ Here we go!",
    ]

    def __init__(self):
        self.state = self.ST_TITLE
        self.total_wins = 0
        self.current_step = 0
        self.pads = []
        self._generate_pads()

        # Bear position
        self.bear_x = 40.0
        self.bear_y = 260.0
        self.bear_target_x = 40.0
        self.bear_target_y = 260.0

        # -- Falling animation state --
        # See constants at top for the physics explanation
        self.velocity_y = 0.0
        self.fall_time = 0.0
        self.fall_start_x = 0.0
        self.fall_start_y = 0.0
        self.fall_rotation = 0.0
        self.bear_expression = 'happy'
        self.bounce_cloud_y = 0.0
        self.bounce_phase = 0   # 0=falling, 1=cloud catch, 2=balloon rise
        self.balloon_y = 0.0

        # Screen shake
        self.shake_timer = 0
        self.shake_ox = 0
        self.shake_oy = 0

        # Message overlay
        self.message_text = ""
        self.message_sub = ""
        self.message_timer = 0

        # Advance animation
        self.advance_timer = 0

        # Victory
        self.victory_timer = 0
        self.firework_timer = 0

        # Title animation
        self.tick = 0
        self.blink = 0

        # Background clouds
        self.clouds = [{'x': random.randint(0, SCREEN_WIDTH),
                        'y': random.randint(30, 180),
                        'sp': random.uniform(0.2, 0.6),
                        'sc': random.uniform(0.5, 1.0)} for _ in range(5)]

    def _generate_pads(self):
        self.pads = []
        for i in range(TOTAL_STEPS):
            left_safe = random.random() > BOUNCE_CHANCE
            if left_safe:
                right_safe = random.random() > BOUNCE_CHANCE
                if not right_safe and not left_safe:
                    left_safe = True
            else:
                right_safe = True
            self.pads.append({
                'left': Pad(i, True, left_safe),
                'right': Pad(i, False, right_safe),
            })

    def reset(self):
        self.state = self.ST_PLAYING
        self.current_step = 0
        self._generate_pads()
        self.bear_x = 40.0
        self.bear_y = 260.0
        self.bear_target_x = 40.0
        self.bear_target_y = 260.0
        self.velocity_y = 0.0
        self.fall_time = 0.0
        self.bear_expression = 'happy'
        self.message_timer = 0
        self.victory_timer = 0
        particles.clear()

    def _pad_pos(self, step, is_left):
        if step < 0 or step >= TOTAL_STEPS:
            return 40.0, 260.0
        pad = self.pads[step]['left' if is_left else 'right']
        return float(pad.x), float(pad.y - 25)

    def choose(self, is_left):
        """Player picked left (top) or right (bottom) pad."""
        if self.state != self.ST_PLAYING or self.current_step >= TOTAL_STEPS:
            return

        side = 'left' if is_left else 'right'
        other = 'right' if is_left else 'left'
        pad = self.pads[self.current_step][side]
        self.pads[self.current_step][other].revealed = True
        pad.revealed = True

        if pad.is_safe:
            # Safe! Happy hop forward
            play_sound(snd_jump)
            tx, ty = self._pad_pos(self.current_step, is_left)
            self.bear_target_x = tx
            self.bear_target_y = ty
            self.state = self.ST_ADVANCING
            self.advance_timer = 25
            self.bear_expression = 'happy'
            spawn_stars(tx, ty - 10, 10)
        else:
            # Bouncy pad! Cute fall incoming~
            play_sound(snd_fall)
            pad.trigger_spring()
            tx, ty = self._pad_pos(self.current_step, is_left)
            self.bear_x = tx
            self.bear_y = ty
            self.fall_start_x = tx
            self.fall_start_y = ty
            self.velocity_y = -3.0  # tiny upward hop before falling
            self.fall_time = 0.0
            self.fall_rotation = 0.0
            self.bounce_phase = 0
            self.bear_expression = 'surprised'
            self.state = self.ST_FALLING
            self.shake_timer = 10

    # --------------------------------------------------------
    # Update methods
    # --------------------------------------------------------
    def _update_falling(self):
        """
        Falling animation physics:
        Phase 0 - Free fall:
          velocity_y += GRAVITY each frame (accelerating down)
          bear_y += velocity_y
          bear_x = start_x + sin(time * SWING_SPEED) * AMPLITUDE  (sway)
          rotation increases (funny spinning)
          particles spawn (bubbles, stars)
          -> when bear_y >= FALL_TARGET_Y, go to phase 1
        Phase 1 - Cloud catches bear (brief pause):
          bear stops, cloud appears underneath
          -> after short delay, go to phase 2
        Phase 2 - Balloon carries bear back up:
          velocity_y = BOUNCE_VELOCITY (negative = upward)
          velocity_y += GRAVITY * 0.3 (slow gravity, balloon floats)
          confetti + stars spawn
          -> when bear_y <= start_y, animation done
        """
        dt = 1.0 / FPS
        self.fall_time += dt

        if self.bounce_phase == 0:
            # Phase 0: Free fall with gravity
            self.velocity_y += GRAVITY
            self.bear_y += self.velocity_y
            # Sway left-right (sin wave)
            swing = math.sin(self.fall_time * FALL_SWING_SPEED) * FALL_SWING_AMPLITUDE
            self.bear_x = self.fall_start_x + swing
            # Spin
            self.fall_rotation += 3.0
            # Particles
            if random.random() < 0.3:
                spawn_bubbles(self.bear_x, self.bear_y + 15, 2)
            if random.random() < 0.15:
                spawn_stars(self.bear_x + random.randint(-20, 20),
                            self.bear_y + random.randint(-10, 10), 1)
            # Hit bottom?
            if self.bear_y >= FALL_TARGET_Y:
                self.bear_y = FALL_TARGET_Y
                self.bounce_phase = 1
                self.bounce_cloud_y = FALL_TARGET_Y + 20
                play_sound(snd_bounce)
                self.shake_timer = 8
                spawn_bubbles(self.bear_x, self.bear_y + 20, 12)
                spawn_stars(self.bear_x, self.bear_y, 15)

        elif self.bounce_phase == 1:
            # Phase 1: Cloud catches, brief pause
            self.fall_rotation *= 0.9
            self.bear_expression = 'super_happy'
            if self.fall_time > 0.8:
                self.bounce_phase = 2
                self.velocity_y = BOUNCE_VELOCITY

        elif self.bounce_phase == 2:
            # Phase 2: Balloon carries bear back up
            self.velocity_y += GRAVITY * 0.3
            self.bear_y += self.velocity_y
            self.fall_rotation *= 0.95
            self.bear_x += (self.fall_start_x - self.bear_x) * 0.08
            if random.random() < 0.2:
                spawn_confetti(self.bear_x, self.bear_y + 20, 3)
            if random.random() < 0.15:
                spawn_stars(self.bear_x, self.bear_y - 10, 2)

            if self.bear_y <= self.fall_start_y:
                # Back to position!
                self.bear_y = self.fall_start_y
                self.bear_x = self.fall_start_x
                self.velocity_y = 0
                self.fall_rotation = 0
                self.bear_expression = 'super_happy'
                self.state = self.ST_MESSAGE
                self.message_text = random.choice(self.ENCOURAGEMENTS)
                self.message_sub = random.choice(self.SUB_MESSAGES)
                self.message_timer = 100
                spawn_confetti(self.bear_x, self.bear_y, 20)
                spawn_stars(self.bear_x, self.bear_y - 20, 10)

        # Safety timeout
        if self.fall_time > MAX_FALL_TIME + 1.0:
            self.bear_y = self.fall_start_y
            self.bear_x = self.fall_start_x
            self.velocity_y = 0
            self.state = self.ST_MESSAGE
            self.message_text = "Boing~ You're back!"
            self.message_sub = "Let's try again!"
            self.message_timer = 80

    def _update_advancing(self):
        if self.advance_timer > 0:
            self.bear_x += (self.bear_target_x - self.bear_x) * 0.15
            self.bear_y += (self.bear_target_y - self.bear_y) * 0.15
            self.advance_timer -= 1
            self.bear_y += math.sin(self.advance_timer * 0.3) * 8

        if self.advance_timer <= 0:
            self.bear_x = self.bear_target_x
            self.bear_y = self.bear_target_y
            self.current_step += 1
            if self.current_step >= TOTAL_STEPS:
                self.state = self.ST_VICTORY
                self.victory_timer = 0
                self.total_wins += 1
                play_sound(snd_victory)
                for _ in range(5):
                    spawn_fireworks(random.randint(100, SCREEN_WIDTH - 100),
                                    random.randint(100, 300), 25)
            else:
                self.state = self.ST_PLAYING

    def _update_message(self):
        if self.message_timer > 0:
            self.message_timer -= 1
        if self.message_timer <= 0:
            self.state = self.ST_PLAYING

    def _update_victory(self):
        self.victory_timer += 1
        self.firework_timer += 1
        if self.firework_timer % 30 == 0:
            spawn_fireworks(random.randint(100, SCREEN_WIDTH - 100),
                            random.randint(80, 250), 20)
            spawn_confetti(random.randint(100, SCREEN_WIDTH - 100),
                           random.randint(80, 250), 15)
        self.bear_y = self.bear_target_y + math.sin(self.victory_timer * 0.1) * 15
        self.bear_expression = 'super_happy'

    def update(self):
        self.tick += 1
        self.blink += 1

        for c in self.clouds:
            c['x'] += c['sp']
            if c['x'] > SCREEN_WIDTH + 50:
                c['x'] = -50
                c['y'] = random.randint(30, 180)

        for pair in self.pads:
            pair['left'].update()
            pair['right'].update()

        for p in particles:
            p.update()
        particles[:] = [p for p in particles if p.alive]

        if self.shake_timer > 0:
            self.shake_timer -= 1
            self.shake_ox = random.randint(-SCREEN_SHAKE_AMOUNT, SCREEN_SHAKE_AMOUNT)
            self.shake_oy = random.randint(-SCREEN_SHAKE_AMOUNT, SCREEN_SHAKE_AMOUNT)
        else:
            self.shake_ox = self.shake_oy = 0

        if self.state == self.ST_FALLING:
            self._update_falling()
        elif self.state == self.ST_ADVANCING:
            self._update_advancing()
        elif self.state == self.ST_MESSAGE:
            self._update_message()
        elif self.state == self.ST_VICTORY:
            self._update_victory()

    # --------------------------------------------------------
    # Drawing methods
    # --------------------------------------------------------
    def _draw_bg(self, surf):
        for y in range(SCREEN_HEIGHT):
            r = y / SCREEN_HEIGHT
            surf.fill((int(135 + 65 * r), int(206 + 24 * r), int(250 + 5 * r)),
                       (0, y, SCREEN_WIDTH, 1))
        for c in self.clouds:
            draw_cloud(surf, c['x'], c['y'], c['sc'], CLOUD_LIGHT)
        # Grass
        pygame.draw.rect(surf, (120, 200, 80), (0, SCREEN_HEIGHT - 60, SCREEN_WIDTH, 60))
        pygame.draw.rect(surf, (100, 180, 60), (0, SCREEN_HEIGHT - 60, SCREEN_WIDTH, 5))
        # Flowers
        for i in range(15):
            fx = (i * 57 + 20) % SCREEN_WIDTH
            fy = SCREEN_HEIGHT - 45 + (i * 13) % 30
            pygame.draw.circle(surf, RAINBOW_COLORS[i % len(RAINBOW_COLORS)], (fx, fy), 4)
            pygame.draw.circle(surf, GOLD, (fx, fy), 2)

    def _draw_bridge(self, surf):
        # Ropes
        pygame.draw.line(surf, (180, 140, 100), (60, 265), (SCREEN_WIDTH - 60, 265), 3)
        pygame.draw.line(surf, (180, 140, 100), (60, 355), (SCREEN_WIDTH - 60, 355), 3)
        # Start label
        surf.blit(font_small.render("START", True, ORANGE), (10, 240))
        # Goal
        gx = SCREEN_WIDTH - 45
        draw_rainbow(surf, gx, 230, 40)
        pulse = math.sin(self.tick * 0.05) * 5
        draw_star(surf, gx, 200, int(20 + pulse), GOLD)
        surf.blit(font_small.render("GOAL!", True, RED), (gx - 22, 250))
        # Pads
        for i, pair in enumerate(self.pads):
            cur = (i == self.current_step and self.state == self.ST_PLAYING)
            pair['left'].draw(surf, highlight=cur)
            pair['right'].draw(surf, highlight=cur)
            t = font_tiny.render(str(i + 1), True, (150, 150, 180))
            surf.blit(t, t.get_rect(center=(pair['left'].x,
                                            (pair['left'].y + pair['right'].y) // 2)))

    def _draw_falling_fx(self, surf):
        if self.state != self.ST_FALLING:
            return
        if self.bounce_phase == 1:
            draw_cloud(surf, self.bear_x, self.bounce_cloud_y, 1.5, CLOUD_WHITE)
            t = font_small.render("Cloud caught you!", True, WHITE)
            surf.blit(t, t.get_rect(center=(self.bear_x, self.bounce_cloud_y + 40)))
        elif self.bounce_phase == 2:
            colors = [BALLOON_RED, BALLOON_BLUE, BALLOON_YELLOW, BALLOON_GREEN]
            for i, bc in enumerate(colors):
                draw_balloon(surf, self.bear_x + (i - 1.5) * 18, self.bear_y - 45, bc, 14)
            t = font_tiny.render("Balloon rescue~ Flying up!", True, GOLD)
            surf.blit(t, t.get_rect(center=(self.bear_x, self.bear_y - 70)))
        # Speech bubble during fall
        if self.bounce_phase == 0 and self.fall_time > 0.2:
            words = ["Wheee~!", "I'm flying!", "So fun!"]
            w = words[int(self.fall_time * 2) % len(words)]
            bt = font_tiny.render(w, True, BLACK)
            bx, by = self.bear_x + 40, self.bear_y - 30
            br = bt.get_rect(center=(bx, by))
            bg = br.inflate(16, 10)
            pygame.draw.ellipse(surf, WHITE, bg)
            pygame.draw.ellipse(surf, BLACK, bg, 2)
            surf.blit(bt, br)

    def _draw_message(self, surf):
        if self.state != self.ST_MESSAGE or self.message_timer <= 0:
            return
        ov = pygame.Surface((SCREEN_WIDTH, 130), pygame.SRCALPHA)
        ov.fill((255, 255, 255, 180))
        surf.blit(ov, (0, 195))
        t = font_medium.render(self.message_text, True, (80, 50, 150))
        surf.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, 230)))
        if self.message_sub:
            s = font_small.render(self.message_sub, True, (200, 100, 150))
            surf.blit(s, s.get_rect(center=(SCREEN_WIDTH // 2, 270)))
        h = font_medium.render("<3  <3  <3", True, RED)
        surf.blit(h, h.get_rect(center=(SCREEN_WIDTH // 2, 305)))

    def _draw_hud(self, surf):
        if self.state == self.ST_TITLE:
            return
        surf.blit(font_tiny.render(f"Step {self.current_step}/{TOTAL_STEPS}", True,
                                   (80, 80, 120)), (10, 10))
        surf.blit(font_tiny.render(f"Bridges crossed: {self.total_wins}", True, GOLD), (10, 35))
        if self.state == self.ST_PLAYING:
            t = font_tiny.render("Click LEFT = top pad    Click RIGHT = bottom pad",
                                 True, (120, 120, 160))
            surf.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)))

    def _draw_title(self, surf):
        # Title
        t1 = font_large.render("Magic Bouncy Bridge", True, PURPLE)
        s1 = font_large.render("Magic Bouncy Bridge", True, (100, 80, 150))
        surf.blit(s1, s1.get_rect(center=(SCREEN_WIDTH // 2 + 2, 102)))
        surf.blit(t1, t1.get_rect(center=(SCREEN_WIDTH // 2, 100)))
        # Subtitle
        t2 = font_medium.render("Kid's Pad Adventure!", True, ORANGE)
        surf.blit(t2, t2.get_rect(center=(SCREEN_WIDTH // 2, 150)))
        # Decorative stars
        for i in range(8):
            a = self.tick * 0.02 + i * math.pi / 4
            sx = SCREEN_WIDTH // 2 + math.cos(a) * 200
            sy = 120 + math.sin(a) * 50
            ssz = 8 + math.sin(self.tick * 0.05 + i) * 3
            draw_star(surf, sx, sy, int(ssz), RAINBOW_COLORS[i % len(RAINBOW_COLORS)])
        # Bear (blinking)
        blink = (self.blink % 120) < 8
        expr = 'super_happy' if blink else 'happy'
        draw_bear(surf, 400, 320 + math.sin(self.tick * 0.08) * 5, 35, expr)
        # Instructions
        y = 400
        for line in ["Click LEFT side -> Top pad",
                     "Click RIGHT side -> Bottom pad",
                     "(Arrow keys work too!)"]:
            t = font_small.render(line, True, (100, 100, 140))
            surf.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, y)))
            y += 30
        # Flashing start prompt
        if (self.tick // 30) % 2 == 0:
            t = font_medium.render("Press SPACE to start!", True, RED)
            surf.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, 520)))
        # Rainbows
        draw_rainbow(surf, 100, 200, 35)
        draw_rainbow(surf, SCREEN_WIDTH - 100, 200, 35)

    def _draw_victory(self, surf):
        draw_rainbow(surf, SCREEN_WIDTH // 2, 120, 80)
        p = math.sin(self.victory_timer * 0.08) * 5
        t1 = font_large.render("You crossed the bridge!", True, GOLD)
        s1 = font_large.render("You crossed the bridge!", True, ORANGE)
        surf.blit(s1, s1.get_rect(center=(SCREEN_WIDTH // 2 + 2, 82 + p)))
        surf.blit(t1, t1.get_rect(center=(SCREEN_WIDTH // 2, 80 + p)))

        t2 = font_medium.render("So brave! Yay~ You're the best!", True, PURPLE)
        surf.blit(t2, t2.get_rect(center=(SCREEN_WIDTH // 2, 140)))

        t3 = font_small.render(f"Bridges crossed: {self.total_wins}  -  Best kid ever!",
                                True, (100, 80, 150))
        surf.blit(t3, t3.get_rect(center=(SCREEN_WIDTH // 2, 185)))

        if self.victory_timer > 60:
            t4 = font_medium.render("Press R to play again!", True, SAFE_GREEN)
            surf.blit(t4, t4.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)))
            t5 = font_small.render("Thanks for playing! You're the cutest adventurer!",
                                    True, (180, 130, 200))
            surf.blit(t5, t5.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 45)))

        for i in range(12):
            a = self.victory_timer * 0.03 + i * math.pi / 6
            sx = SCREEN_WIDTH // 2 + math.cos(a) * (150 + i * 15)
            sy = 130 + math.sin(a) * 60
            ssz = 10 + math.sin(self.victory_timer * 0.06 + i) * 4
            draw_star(surf, sx, sy, int(ssz), RAINBOW_COLORS[i % len(RAINBOW_COLORS)])

    def draw(self):
        buf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._draw_bg(buf)

        if self.state == self.ST_TITLE:
            self._draw_title(buf)
        else:
            self._draw_bridge(buf)
            for p in particles:
                p.draw(buf)
            self._draw_falling_fx(buf)
            draw_bear(buf, self.bear_x, self.bear_y, 30,
                      self.bear_expression, self.fall_rotation)
            self._draw_message(buf)
            self._draw_hud(buf)
            if self.state == self.ST_VICTORY:
                self._draw_victory(buf)

        screen.blit(buf, (self.shake_ox, self.shake_oy))

    # --------------------------------------------------------
    # Event handling
    # --------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if self.state == self.ST_TITLE:
                if event.key == pygame.K_SPACE:
                    self.reset()
            elif self.state == self.ST_PLAYING:
                if event.key == pygame.K_LEFT:
                    self.choose(True)
                elif event.key == pygame.K_RIGHT:
                    self.choose(False)
            if event.key == pygame.K_r and self.state != self.ST_TITLE:
                self.reset()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == self.ST_TITLE:
                self.reset()
            elif self.state == self.ST_PLAYING:
                if event.pos[0] < SCREEN_WIDTH // 2:
                    self.choose(True)
                else:
                    self.choose(False)
            elif self.state == self.ST_VICTORY and self.victory_timer > 60:
                self.reset()

        return True


# ============================================================
# Main Loop
# ============================================================
def main():
    game = Game()
    running = True
    while running:
        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False
        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
