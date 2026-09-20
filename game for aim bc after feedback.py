"""
AstroBlast: Space Explorer  –  Version 2
=========================================
Python / Pygame game for children aged 8-12.

Changes in V2 (from user feedback):
  • Jiya  (age 11) – Added background music generated via pygame synthesiser
  • Khrishi (age 10) – Added rocket skin selector (4 colour schemes) on menu

Controls : Arrow Keys  or  W A S D
Collect  : Stars (+10 / +20)   Gems (+30)
Avoid    : UFOs  – costs a life on collision
Power-up : Shield – 3 seconds of invincibility
Menu     : ◄ ► change difficulty   [ ] change rocket skin

Difficulty
  CADET  – 2 UFOs, 3 lives, 60 s, speed 1.4
  PILOT  – 4 UFOs, 2 lives, 45 s, speed 2.0
  ACE    – 6 UFOs, 1 life,  30 s, speed 2.8

Requirements:  pip install pygame
Run         :  python astroblast.py
"""

import pygame
import sys
import math
import random
import array
import struct

# ── Initialise Pygame ─────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

# ── Window / canvas size ──────────────────────────────────────────
W, H = 640, 480
FPS  = 60

screen = pygame.display.set_mode((W, H + 90))
pygame.display.set_caption("✦ AstroBlast – Space Explorer  v2")
clock  = pygame.time.Clock()

# ── Colours ───────────────────────────────────────────────────────
BG_DARK  = (  5,  10,  26)
PANEL    = ( 10,  21,  48)
WHITE    = (255, 255, 255)
CYAN     = (  0, 229, 255)
GOLD     = (255, 215,   0)
YELLOW   = (255, 232,  90)
RED      = (255,  61,  90)
GREEN    = ( 57, 255, 110)
PURPLE   = (191,  95, 255)
ORANGE   = (255, 140,   0)
BLUE_D   = ( 26,  58, 110)
BLUE_M   = ( 42,  90, 174)
BLUE_W   = ( 10,  64, 128)
MUTED    = (106, 138, 170)
GREY     = ( 80, 110, 140)

UFO_COLS = [RED, PURPLE, ORANGE, (255, 145, 0)]

# ── Fonts ─────────────────────────────────────────────────────────
F_BIG   = pygame.font.SysFont("Arial", 36, bold=True)
F_MED   = pygame.font.SysFont("Arial", 24, bold=True)
F_SMALL = pygame.font.SysFont("Arial", 17, bold=True)
F_TINY  = pygame.font.SysFont("Arial", 13)

# ── Difficulty configs ────────────────────────────────────────────
LEVELS = [
    {"name": "CADET", "ufos": 2, "lives": 3, "time": 60, "ufoSpeed": 1.4, "items": 8},
    {"name": "PILOT", "ufos": 4, "lives": 2, "time": 45, "ufoSpeed": 2.0, "items": 6},
    {"name": "ACE",   "ufos": 6, "lives": 1, "time": 30, "ufoSpeed": 2.8, "items": 5},
]

# ── Rocket skins (Khrishi feedback) ──────────────────────────────
# Each skin: (label, body_col, nose_col, wing_col, cockpit_col)
ROCKET_SKINS = [
    {"label": "BLUE",   "body": BLUE_M,         "nose": CYAN,
     "wing": BLUE_W,          "cockpit": CYAN},
    {"label": "RED",    "body": (160,  30,  50), "nose": (255, 120, 140),
     "wing": (120,  10,  30), "cockpit": (255, 180, 180)},
    {"label": "GREEN",  "body": ( 20, 120,  60), "nose": GREEN,
     "wing": ( 10,  80,  40), "cockpit": GREEN},
    {"label": "GOLD",   "body": (140, 100,   0), "nose": GOLD,
     "wing": (100,  70,   0), "cockpit": GOLD},
]

HUD_H  = 90
PLAY_Y = HUD_H

# ─────────────────────────────────────────────────────────────────
#  BACKGROUND MUSIC  (Jiya feedback)
#  Synthesised entirely with pygame – no audio files needed.
#  Generates a simple looping space ambient track using sine waves.
# ─────────────────────────────────────────────────────────────────
SAMPLE_RATE = 22050

def _sine_wave(freq, duration, volume=0.3, sample_rate=SAMPLE_RATE):
    """Generate a mono sine-wave as a pygame Sound."""
    n_samples = int(sample_rate * duration)
    buf = array.array('h')          # signed 16-bit
    for i in range(n_samples):
        t   = i / sample_rate
        val = int(32767 * volume * math.sin(2 * math.pi * freq * t))
        buf.append(val)
    sound = pygame.sndarray.make_sound(
        __import__('numpy').array(buf, dtype='int16').reshape(-1, 1)
        if False else                # numpy path (optional)
        pygame.sndarray.make_sound(
            pygame.sndarray.array(
                pygame.mixer.Sound(buffer=buf)
            )
        )
    )
    return sound

def _make_music_channel():
    """
    Build a simple looping space ambient track without numpy or audio files.
    Uses pygame.mixer.Sound from raw PCM bytes.
    Notes cycle through a pentatonic scale giving a futuristic feel.
    """
    sample_rate = SAMPLE_RATE
    # Pentatonic note frequencies (Hz) – space-like arpeggios
    notes = [130.81, 164.81, 196.00, 261.63, 329.63,
             261.63, 196.00, 164.81]
    note_dur   = 0.45    # seconds per note
    total_dur  = note_dur * len(notes)
    n_total    = int(sample_rate * total_dur)

    buf = array.array('h', [0] * n_total)

    for note_idx, freq in enumerate(notes):
        start = int(note_idx * note_dur * sample_rate)
        n_note = int(note_dur * sample_rate)
        for i in range(n_note):
            if start + i >= n_total:
                break
            t = i / sample_rate
            # Main tone
            val = 0.18 * math.sin(2 * math.pi * freq * t)
            # Octave harmonic (softer)
            val += 0.07 * math.sin(2 * math.pi * freq * 2 * t)
            # Sub-bass pulse
            val += 0.05 * math.sin(2 * math.pi * (freq / 2) * t)
            # Envelope: fade in/out per note
            env = min(i / (n_note * 0.15),
                      1.0,
                      (n_note - i) / (n_note * 0.2))
            buf[start + i] = int(32767 * val * env)

    # Convert array to bytes for pygame Sound
    raw_bytes = buf.tobytes()
    sound = pygame.mixer.Sound(buffer=raw_bytes)
    return sound

# Build the music sound object once at startup
try:
    _MUSIC = _make_music_channel()
    _MUSIC_OK = True
except Exception:
    _MUSIC_OK = False

def music_play():
    if _MUSIC_OK:
        _MUSIC.play(loops=-1)        # loop forever

def music_stop():
    if _MUSIC_OK:
        _MUSIC.stop()

def music_set_volume(v):
    if _MUSIC_OK:
        _MUSIC.set_volume(max(0.0, min(1.0, v)))

# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────
def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)

def blit_text(surf, text, font, colour, cx, cy):
    img = font.render(text, True, colour)
    surf.blit(img, img.get_rect(center=(cx, cy)))

def blit_text_left(surf, text, font, colour, x, y):
    img = font.render(text, True, colour)
    surf.blit(img, (x, y))

def lerp_angle(a, b, t):
    diff = (b - a + math.pi) % (2 * math.pi) - math.pi
    return a + diff * t

# ─────────────────────────────────────────────────────────────────
#  STAR FIELD
# ─────────────────────────────────────────────────────────────────
class BgStar:
    def __init__(self, randomise_x=True):
        self.reset(randomise_x)

    def reset(self, randomise_x=False):
        self.x     = random.uniform(0, W) if randomise_x else W
        self.y     = random.uniform(0, H)
        self.spd   = random.uniform(0.1, 0.5)
        self.r     = random.uniform(0.5, 1.8)
        self.phase = random.uniform(0, math.tau)

    def update(self):
        self.x -= self.spd
        if self.x < 0:
            self.reset()

    def draw(self, surf, t):
        bright = int(102 + 153 * abs(math.sin(t * 0.001 + self.phase)))
        pygame.draw.circle(surf, (bright, bright, bright),
                           (int(self.x), int(self.y) + PLAY_Y),
                           max(1, int(self.r)))

# ─────────────────────────────────────────────────────────────────
#  PARTICLE
# ─────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, colour, speed=None, life=None, angle=None):
        self.x        = x
        self.y        = y
        self.col      = colour
        a             = angle if angle is not None else random.uniform(0, math.tau)
        spd           = speed if speed is not None else random.uniform(2, 5)
        self.vx       = math.cos(a) * spd
        self.vy       = math.sin(a) * spd
        self.life     = life if life is not None else 1.0
        self.max_life = self.life
        self.r        = random.uniform(2, 4)

    def update(self, dt):
        self.x   += self.vx
        self.y   += self.vy
        self.vy  += 0.05 * 60 * dt
        self.life -= dt / 0.9
        return self.life > 0

    def draw(self, surf):
        alpha = max(0.0, self.life / self.max_life)
        r     = max(1, int(self.r * alpha))
        col   = tuple(min(255, int(c * alpha)) for c in self.col)
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), r)

def burst(particles, x, y, colour, n=14):
    for i in range(n):
        a   = (i / n) * math.tau + random.uniform(-0.15, 0.15)
        spd = random.uniform(2, 6)
        particles.append(Particle(x, y, colour, speed=spd, angle=a))

# ─────────────────────────────────────────────────────────────────
#  EXPLOSION RING
# ─────────────────────────────────────────────────────────────────
class Explosion:
    def __init__(self, x, y):
        self.x    = x
        self.y    = y
        self.r    = 0.0
        self.life = 1.0

    def update(self, dt):
        self.r    += 180 * dt
        self.life -= 0.06 * 60 * dt
        return self.life > 0

    def draw(self, surf):
        if self.r < 2:
            return
        alpha = max(0.0, self.life)
        col   = (min(255, int(255 * alpha)), min(255, int(120 * alpha)), 0)
        pygame.draw.circle(surf, col,
                           (int(self.x), int(self.y)),
                           int(self.r), max(1, int(4 * alpha)))

# ─────────────────────────────────────────────────────────────────
#  COLLECTIBLE ITEM
# ─────────────────────────────────────────────────────────────────
def _star_polygon(cx, cy, num_pts, outer, inner):
    pts = []
    for i in range(num_pts * 2):
        r = outer if i % 2 == 0 else inner
        a = math.pi * i / num_pts - math.pi / 2
        pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    return pts

class Item:
    def __init__(self, existing=None):
        existing = existing or []
        for _ in range(200):
            self.x = random.uniform(40, W - 40)
            self.y = random.uniform(40, H - 40)
            if all(dist(self.x, self.y, i.x, i.y) > 50 for i in existing):
                break
        self.kind = "gem" if random.random() < 0.35 else "star"
        self.val  = 30 if self.kind == "gem" else random.choice([10, 20])
        self.anim = random.uniform(0, math.tau)

    def update(self, dt):
        self.anim += dt * 1.2

    def draw(self, surf):
        bob = math.sin(self.anim) * 4
        px  = int(self.x)
        py  = int(self.y + bob) + PLAY_Y
        if self.kind == "star":
            self._draw_star(surf, px, py)
        else:
            self._draw_gem(surf, px, py)
        label = F_TINY.render("+" + str(self.val), True, WHITE)
        surf.blit(label, label.get_rect(center=(px, py + 22)))

    @staticmethod
    def _glow(surf, x, y, colour, radius):
        gs = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r, a in [(radius, 30), (int(radius * 0.7), 70), (int(radius * 0.4), 140)]:
            pygame.draw.circle(gs, (*colour, a), (radius, radius), r)
        surf.blit(gs, (x - radius, y - radius))

    def _draw_star(self, surf, x, y):
        Item._glow(surf, x, y, GOLD, 22)
        pygame.draw.polygon(surf, GOLD,   _star_polygon(x, y, 5, 13, 5))
        pygame.draw.polygon(surf, YELLOW, _star_polygon(x, y, 5,  8, 4))

    def _draw_gem(self, surf, x, y):
        Item._glow(surf, x, y, CYAN, 22)
        pts = [(x, y-13), (x+10, y-3), (x+6, y+13), (x-6, y+13), (x-10, y-3)]
        pygame.draw.polygon(surf, CYAN, pts)
        pygame.draw.polygon(surf, (200, 255, 255),
                            [(x, y-13), (x+10, y-3), (x, y-2)])
        pygame.draw.polygon(surf, (0, 150, 200), pts, 2)

# ─────────────────────────────────────────────────────────────────
#  SHIELD POWER-UP
# ─────────────────────────────────────────────────────────────────
class PowerUp:
    def __init__(self):
        self.x    = random.uniform(60, W - 60)
        self.y    = random.uniform(60, H - 60)
        self.anim = 0.0

    def update(self, dt):
        self.anim += dt * 1.5

    def draw(self, surf):
        bob = math.sin(self.anim) * 3
        px  = int(self.x)
        py  = int(self.y + bob) + PLAY_Y
        for i in range(8):
            a = self.anim + i * math.tau / 8
            pygame.draw.circle(surf, GREEN,
                               (int(px + math.cos(a) * 20),
                                int(py + math.sin(a) * 20)), 3)
        hex_pts = [
            (px + int(16 * math.cos(math.pi / 3 * i - math.pi / 6)),
             py + int(16 * math.sin(math.pi / 3 * i - math.pi / 6)))
            for i in range(6)
        ]
        hs = pygame.Surface((40, 40), pygame.SRCALPHA)
        shifted = [(x - px + 20, y - py + 20) for x, y in hex_pts]
        pygame.draw.polygon(hs, (*GREEN, 60), shifted)
        surf.blit(hs, (px - 20, py - 20))
        pygame.draw.polygon(surf, GREEN, hex_pts, 2)
        lbl = F_TINY.render("SHIELD", True, GREEN)
        surf.blit(lbl, lbl.get_rect(center=(px, py + 30)))

# ─────────────────────────────────────────────────────────────────
#  UFO
# ─────────────────────────────────────────────────────────────────
class UFO:
    def __init__(self, cfg):
        spd  = cfg["ufoSpeed"] * random.uniform(0.8, 1.2)
        edge = random.randint(0, 3)
        if   edge == 0: self.x, self.y = random.uniform(0, W), -30
        elif edge == 1: self.x, self.y = W + 30, random.uniform(0, H)
        elif edge == 2: self.x, self.y = random.uniform(0, W), H + 30
        else:           self.x, self.y = -30, random.uniform(0, H)
        ang      = math.atan2(H/2 - self.y, W/2 - self.x)
        ang     += random.uniform(-0.6, 0.6)
        self.vx  = math.cos(ang) * spd
        self.vy  = math.sin(ang) * spd
        self.spd = spd
        self.r   = 22
        self.col = random.choice(UFO_COLS)
        self.anim = 0.0

    def update(self, dt, rx, ry):
        self.x    += self.vx
        self.y    += self.vy
        self.anim += dt * 3
        if random.random() < 0.025:
            a = math.atan2(ry - self.y, rx - self.x)
            a += random.uniform(-0.4, 0.4)
            self.vx = math.cos(a) * self.spd
            self.vy = math.sin(a) * self.spd
        if self.x < -60:  self.x = W + 60
        if self.x > W+60: self.x = -60
        if self.y < -60:  self.y = H + 60
        if self.y > H+60: self.y = -60

    def draw(self, surf):
        px, py, r = int(self.x), int(self.y) + PLAY_Y, self.r
        gs = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*self.col, 50), (r*2, r*2), r*2)
        surf.blit(gs, (px - r*2, py - r*2))
        bs = pygame.Surface((r*2, r), pygame.SRCALPHA)
        pygame.draw.ellipse(bs, (*self.col, 180), (0, 0, r*2, r))
        surf.blit(bs, (px - r, py - r//2))
        pygame.draw.ellipse(surf, self.col,
                            pygame.Rect(px-r, py-r//2, r*2, r), 2)
        ds = pygame.Surface((r, r//2), pygame.SRCALPHA)
        pygame.draw.ellipse(ds, (*self.col, 100), (0, 0, r, r//2))
        surf.blit(ds, (px - r//2, py - r//2 - r//3))
        for i in range(6):
            a  = self.anim + i * math.tau / 6
            lx = int(px + math.cos(a) * r * 0.7)
            ly = int(py + math.sin(a) * r * 0.25)
            pygame.draw.circle(surf, WHITE if i%2==0 else self.col, (lx, ly), 3)

# ─────────────────────────────────────────────────────────────────
#  ROCKET  –  now uses skin colours (Khrishi feedback)
# ─────────────────────────────────────────────────────────────────
def _rotate_pts(pts, angle):
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return [(int(px * cos_a - py * sin_a),
             int(px * sin_a + py * cos_a))
            for px, py in pts]

class Rocket:
    def __init__(self, skin_idx=0):
        self.x          = W / 2
        self.y          = H / 2
        self.spd        = 3.5
        self.angle      = 0.0
        self.invincible = 0.0
        self.w = self.h = 28
        self.skin       = ROCKET_SKINS[skin_idx]

    def update(self, dt, keys):
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1
        thrusting = dx != 0 or dy != 0
        if thrusting:
            self.angle = lerp_angle(self.angle, math.atan2(dy, dx), 0.18)
        self.x = max(self.w/2, min(W - self.w/2, self.x + dx * self.spd))
        self.y = max(self.h/2, min(H - self.h/2, self.y + dy * self.spd))
        if self.invincible > 0:
            self.invincible -= dt
        return thrusting

    def draw(self, surf, thrusting, t, particles):
        px = int(self.x)
        py = int(self.y) + PLAY_Y
        sk = self.skin

        # Flicker during invincibility
        if self.invincible > 0:
            if (pygame.time.get_ticks() // 80) % 2 == 0 and self.invincible > 0.5:
                return

        da = self.angle + math.pi / 2   # draw angle

        # Thrust flame
        if thrusting:
            flicker = random.uniform(0.6, 1.0)
            length  = 22 * flicker
            bx = px - int(math.cos(da) * 14)
            by = py - int(math.sin(da) * 14)
            ex = bx - int(math.cos(da) * length)
            ey = by - int(math.sin(da) * length)
            perp_x = -math.sin(da) * 7 * flicker
            perp_y =  math.cos(da) * 7 * flicker
            pygame.draw.polygon(surf, ORANGE, [
                (int(bx+perp_x), int(by+perp_y)),
                (int(bx-perp_x), int(by-perp_y)),
                (ex, ey)])
            pygame.draw.polygon(surf, GOLD, [
                (int(bx+perp_x*0.5), int(by+perp_y*0.5)),
                (int(bx-perp_x*0.5), int(by-perp_y*0.5)),
                (int(bx - math.cos(da)*length*0.6),
                 int(by - math.sin(da)*length*0.6))])

        # Body
        body_pts = [(px+rx, py+ry)
                    for rx,ry in _rotate_pts([(-10,10),(10,10),(0,-18)], da)]
        pygame.draw.polygon(surf, sk["body"], body_pts)
        pygame.draw.polygon(surf, sk["wing"], body_pts, 1)

        # Nose cone
        nose_pts = [(px+rx, py+ry)
                    for rx,ry in _rotate_pts([(-6,-4),(6,-4),(0,-18)], da)]
        pygame.draw.polygon(surf, sk["nose"], nose_pts)

        # Wings
        for wl in ([(-8,6),(-18,14),(-6,14)], [(8,6),(18,14),(6,14)]):
            wpts = [(px+rx, py+ry) for rx,ry in _rotate_pts(wl, da)]
            pygame.draw.polygon(surf, sk["wing"], wpts)

        # Cockpit window
        cx2 = int(px - (-6) * math.sin(da))
        cy2 = int(py + (-6) * math.cos(da))
        csurf = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(csurf, (*sk["cockpit"], 150), (6, 6), 5)
        surf.blit(csurf, (cx2 - 6, cy2 - 6))
        pygame.draw.circle(surf, sk["cockpit"], (cx2, cy2), 5, 1)

        # Shield ring
        if self.invincible > 0:
            col = GREEN if self.invincible > 1.0 else WHITE
            pygame.draw.circle(surf, col, (px, py), 26,
                               2 if self.invincible > 0.5 else 1)

        # Thrust trail
        if thrusting and random.random() < 0.6:
            tx = self.x - math.cos(da) * 14
            ty = self.y - math.sin(da) * 14
            particles.append(
                Particle(tx, ty + PLAY_Y, ORANGE,
                         speed=random.uniform(1, 3),
                         angle=random.uniform(0, math.tau),
                         life=0.4))

# ─────────────────────────────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────────────────────────────
def draw_hud(surf, score, lives, time_left, level_name, cfg):
    pygame.draw.rect(surf, PANEL, (0, 0, W, HUD_H))
    pygame.draw.line(surf, CYAN, (0, HUD_H-1), (W, HUD_H-1), 1)
    blit_text_left(surf, "SCORE",     F_TINY,  MUTED, 20, 12)
    blit_text_left(surf, str(score),  F_MED,   GOLD,  20, 30)
    hearts = "♥" * lives + "♡" * (cfg["lives"] - lives)
    blit_text_left(surf, "LIVES",     F_TINY,  MUTED, W//2-90, 12)
    blit_text_left(surf, hearts,      F_MED,   RED,   W//2-90, 30)
    t_col = RED if time_left <= 10 else GREEN
    blit_text_left(surf, "TIME",      F_TINY,  MUTED, W-200, 12)
    blit_text_left(surf, f"{int(math.ceil(max(0,time_left)))}s",
                   F_MED, t_col, W-200, 30)
    blit_text_left(surf, "LEVEL",     F_TINY,  MUTED,  W-90, 12)
    blit_text_left(surf, level_name,  F_SMALL, PURPLE, W-90, 32)

# ─────────────────────────────────────────────────────────────────
#  ROCKET SKIN PREVIEW  (small rocket drawn on menu)
# ─────────────────────────────────────────────────────────────────
def draw_skin_preview(surf, cx, cy, skin, selected):
    # Simple rocket icon
    da = -math.pi / 2   # nose up
    scale = 0.7
    body = [(cx+int(rx*scale), cy+int(ry*scale))
            for rx,ry in _rotate_pts([(-8,8),(8,8),(0,-14)], da)]
    nose = [(cx+int(rx*scale), cy+int(ry*scale))
            for rx,ry in _rotate_pts([(-5,-3),(5,-3),(0,-14)], da)]
    for wl in ([(-6,5),(-14,11),(-5,11)], [(6,5),(14,11),(5,11)]):
        wpts = [(cx+int(rx*scale), cy+int(ry*scale))
                for rx,ry in _rotate_pts(wl, da)]
        pygame.draw.polygon(surf, skin["wing"], wpts)
    pygame.draw.polygon(surf, skin["body"], body)
    pygame.draw.polygon(surf, skin["nose"], nose)
    pygame.draw.circle(surf, skin["cockpit"], (cx, cy-5), 3)
    # Selection ring
    if selected:
        pygame.draw.circle(surf, WHITE, (cx, cy), 22, 2)
    else:
        pygame.draw.circle(surf, GREY, (cx, cy), 22, 1)

# ─────────────────────────────────────────────────────────────────
#  MENU SCREEN  (updated with skin selector)
# ─────────────────────────────────────────────────────────────────
def draw_menu(surf, stars, chosen, best, t, skin_idx):
    surf.fill(BG_DARK)
    for s in stars:
        s.draw(surf, t)

    # Title glow
    for offset, alpha in [(5, 40), (3, 90), (1, 160)]:
        glow = F_BIG.render("ASTROBLAST", True, CYAN)
        glow.set_alpha(alpha)
        surf.blit(glow, glow.get_rect(center=(W//2 + offset, 80)))

    blit_text(surf, "ASTROBLAST",     F_BIG,  CYAN,          W//2, 80)
    blit_text(surf, "Space Explorer", F_MED,  (0,160,200),   W//2, 118)
    blit_text(surf, "Collect stars & gems  –  Dodge UFOs!",
              F_SMALL, GREY, W//2, 152)

    # ── Difficulty selector ───────────────────────────────────────
    blit_text(surf, "DIFFICULTY", F_TINY, GREY, W//2, 185)
    for i, lvl in enumerate(LEVELS):
        cx       = W//2 + (i-1) * 180
        selected = (i == chosen)
        pygame.draw.rect(surf,
                         CYAN if selected else (40,80,120),
                         pygame.Rect(cx-60, 198, 120, 34),
                         0 if selected else 2, border_radius=17)
        blit_text(surf, lvl["name"], F_SMALL,
                  BG_DARK if selected else GREY, cx, 215)

    cfg = LEVELS[chosen]
    blit_text(surf,
              f"UFOs: {cfg['ufos']}   Lives: {cfg['lives']}   "
              f"Time: {cfg['time']}s   Speed: {cfg['ufoSpeed']}",
              F_TINY, GREY, W//2, 244)

    # ── Rocket skin selector (Khrishi feedback) ───────────────────
    blit_text(surf, "ROCKET SKIN  ( Z and X keys  or  click to select )",
              F_TINY, GREY, W//2, 268)
    # 4 skins evenly spaced across the full width
    skin_positions = [W//2 - 145, W//2 - 48, W//2 + 48, W//2 + 145]
    for i, sk in enumerate(ROCKET_SKINS):
        cx = skin_positions[i]
        draw_skin_preview(surf, cx, 308, sk, i == skin_idx)
        blit_text(surf, sk["label"], F_TINY,
                  WHITE if i == skin_idx else GREY, cx, 335)

    # ── Launch prompt ─────────────────────────────────────────────
    if (pygame.time.get_ticks() // 500) % 2 == 0:
        blit_text(surf, "PRESS  ENTER  TO  LAUNCH", F_MED, GOLD, W//2, 370)

    blit_text(surf, "◄ ► difficulty   Z X or click = rocket skin",
              F_TINY, GREY, W//2, 400)
    blit_text(surf, "Arrow Keys / WASD to fly   |   ESC = menu",
              F_TINY, (60,90,110), W//2, 420)

    if best > 0:
        blit_text(surf, f"Best Score: {best}", F_SMALL, GOLD, W//2, 448)

    # Music note indicator
    blit_text(surf, "♪ Music ON", F_TINY, GREEN, W - 60, H + HUD_H - 20)

# ─────────────────────────────────────────────────────────────────
#  GAME OVER SCREEN
# ─────────────────────────────────────────────────────────────────
def draw_gameover(surf, stars, score, best, chosen, reason, t, skin_idx):
    surf.fill(BG_DARK)
    for s in stars:
        s.draw(surf, t)
    ov = pygame.Surface((W, H+HUD_H), pygame.SRCALPHA)
    pygame.draw.rect(ov, (2,6,20,200), (0,0,W,H+HUD_H))
    surf.blit(ov, (0,0))
    panel = pygame.Rect(W//2-240, 70, 480, 380)
    pygame.draw.rect(surf, (8,18,45), panel, border_radius=16)
    pygame.draw.rect(surf, CYAN, panel, 2, border_radius=16)
    title_col = RED if reason == "lives" else ORANGE
    blit_text(surf,
              "SHIP  DESTROYED!" if reason=="lives" else "TIME'S  UP!",
              F_BIG, title_col, W//2, 130)
    blit_text(surf, f"SCORE:  {score}", F_MED, GOLD, W//2, 185)
    blit_text(surf,
              "★  NEW BEST SCORE  ★" if score >= best else f"Best: {best}",
              F_SMALL, GOLD if score >= best else GREY, W//2, 220)
    if score >= 400:   rating = "GALACTIC LEGEND!"
    elif score >= 250: rating = "Outstanding Pilot!"
    elif score >= 120: rating = "Good Flying!"
    else:              rating = "Keep Training, Cadet!"
    blit_text(surf, rating, F_MED, CYAN, W//2, 258)

    # Skin selector on game over too
    blit_text(surf, "Change rocket skin:", F_TINY, GREY, W//2, 290)
    skin_positions = [W//2 - 145, W//2 - 48, W//2 + 48, W//2 + 145]
    for i, sk in enumerate(ROCKET_SKINS):
        cx = skin_positions[i]
        draw_skin_preview(surf, cx, 318, sk, i == skin_idx)

    for i, lvl in enumerate(LEVELS):
        cx = W//2 + (i-1)*150
        pygame.draw.rect(surf,
                         CYAN if i==chosen else (40,80,120),
                         pygame.Rect(cx-50,350,100,30),
                         0 if i==chosen else 2, border_radius=15)
        blit_text(surf, lvl["name"], F_TINY,
                  BG_DARK if i==chosen else GREY, cx, 365)

    if (pygame.time.get_ticks()//500)%2==0:
        blit_text(surf, "ENTER = Retry     M = Menu",
                  F_SMALL, GOLD, W//2, 395)
    blit_text(surf, "◄ ► difficulty   [ ] rocket skin",
              F_TINY, GREY, W//2, 420)

# ─────────────────────────────────────────────────────────────────
#  FLOATING MESSAGE
# ─────────────────────────────────────────────────────────────────
class FloatMsg:
    def __init__(self):
        self.text  = ""
        self.col   = WHITE
        self.timer = 0.0

    def show(self, text, col=WHITE, duration=1.4):
        self.text  = text
        self.col   = col
        self.timer = duration

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt

    def draw(self, surf):
        if self.timer <= 0 or not self.text:
            return
        img = F_MED.render(self.text, True, self.col)
        r   = img.get_rect(center=(W//2, HUD_H+28))
        bg  = pygame.Surface((r.width+28, r.height+10), pygame.SRCALPHA)
        pygame.draw.rect(bg, (*self.col, 30),
                         (0,0,bg.get_width(),bg.get_height()),
                         border_radius=20)
        surf.blit(bg, (r.x-14, r.y-5))
        surf.blit(img, r)

# ─────────────────────────────────────────────────────────────────
#  INIT GAME
# ─────────────────────────────────────────────────────────────────
def init_game(chosen, skin_idx):
    cfg   = LEVELS[chosen]
    rocket = Rocket(skin_idx)
    ufos   = [UFO(cfg) for _ in range(cfg["ufos"])]
    items  = []
    for _ in range(cfg["items"]):
        items.append(Item(items))
    power_up       = PowerUp() if random.random() < 0.35 else None
    power_up_timer = random.uniform(5, 12)
    return (rocket, ufos, items, power_up, power_up_timer,
            [], [], 0, cfg["lives"], float(cfg["time"]), 0.0)

# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    chosen    = 0
    skin_idx  = 0      # rocket skin (Khrishi feedback)
    best      = 0
    state     = "menu"
    reason    = ""

    bg_stars  = [BgStar(randomise_x=True) for _ in range(120)]
    msg       = FloatMsg()

    (rocket, ufos, items, power_up, power_up_timer,
     particles, explosions, score, lives,
     time_left, flash_timer) = init_game(chosen, skin_idx)

    thrusting = False

    # Start background music (Jiya feedback)
    music_play()
    music_set_volume(0.4)

    while True:
        dt = clock.tick(FPS) / 1000.0
        t  = pygame.time.get_ticks()

        # ── Events ────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                music_stop()
                pygame.quit(); sys.exit()

            # ── MOUSE CLICK – skin selector ───────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                skin_positions = [W//2 - 145, W//2 - 48,
                                  W//2 + 48,  W//2 + 145]
                if state in ("menu", "gameover"):
                    for i, cx in enumerate(skin_positions):
                        if abs(mx - cx) < 36 and abs(my - 308) < 36:
                            skin_idx = i
                        if abs(mx - cx) < 36 and abs(my - 318) < 36:
                            skin_idx = i

            if event.type == pygame.KEYDOWN:

                # Z / X  change rocket skin (easy to find on keyboard!)
                if event.key == pygame.K_z:
                    skin_idx = (skin_idx - 1) % len(ROCKET_SKINS)
                elif event.key == pygame.K_x:
                    skin_idx = (skin_idx + 1) % len(ROCKET_SKINS)
                elif event.key == pygame.K_LEFTBRACKET:
                    skin_idx = (skin_idx - 1) % len(ROCKET_SKINS)
                elif event.key == pygame.K_RIGHTBRACKET:
                    skin_idx = (skin_idx + 1) % len(ROCKET_SKINS)

                if state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        (rocket, ufos, items, power_up, power_up_timer,
                         particles, explosions, score, lives,
                         time_left, flash_timer) = init_game(chosen, skin_idx)
                        msg   = FloatMsg()
                        state = "playing"
                    elif event.key == pygame.K_LEFT:
                        chosen = (chosen-1) % len(LEVELS)
                    elif event.key == pygame.K_RIGHT:
                        chosen = (chosen+1) % len(LEVELS)

                elif state == "gameover":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        (rocket, ufos, items, power_up, power_up_timer,
                         particles, explosions, score, lives,
                         time_left, flash_timer) = init_game(chosen, skin_idx)
                        msg   = FloatMsg()
                        state = "playing"
                    elif event.key == pygame.K_m:
                        state = "menu"
                    elif event.key == pygame.K_LEFT:
                        chosen = (chosen-1) % len(LEVELS)
                    elif event.key == pygame.K_RIGHT:
                        chosen = (chosen+1) % len(LEVELS)

                elif state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"

        # ── UPDATE ────────────────────────────────────────────────
        for s in bg_stars:
            s.update()

        if state == "playing":
            cfg       = LEVELS[chosen]
            time_left -= dt
            if time_left <= 0:
                time_left = 0
                reason    = "time"
                if score > best: best = score
                state = "gameover"

            if state == "playing":
                keys      = pygame.key.get_pressed()
                thrusting = rocket.update(dt, keys)
                for u in ufos:
                    u.update(dt, rocket.x, rocket.y)
                for item in items:
                    item.update(dt)
                if power_up is None:
                    power_up_timer -= dt
                    if power_up_timer <= 0:
                        power_up       = PowerUp()
                        power_up_timer = random.uniform(12, 20)
                else:
                    power_up.update(dt)

                particles  = [p for p in particles  if p.update(dt)]
                explosions = [e for e in explosions  if e.update(dt)]
                if flash_timer > 0:
                    flash_timer -= dt

                # Collect items
                rx, ry    = rocket.x, rocket.y
                to_remove = []
                for i, item in enumerate(items):
                    if dist(rx, ry, item.x, item.y) < 24:
                        score += item.val
                        col    = GOLD if item.kind=="star" else CYAN
                        burst(particles, item.x, item.y+PLAY_Y, col)
                        msg.show(
                            f"+{item.val}  {'⭐' if item.kind=='star' else '💎'}",
                            col, 1.0)
                        to_remove.append(i)
                for i in reversed(to_remove):
                    items.pop(i)
                    items.append(Item(items))

                # Collect power-up
                if power_up and dist(rx, ry, power_up.x, power_up.y) < 28:
                    rocket.invincible = 3.0
                    burst(particles, power_up.x, power_up.y+PLAY_Y, GREEN, 18)
                    msg.show("SHIELD ACTIVE – 3 seconds!", GREEN, 2.0)
                    power_up       = None
                    power_up_timer = random.uniform(12, 20)

                # UFO collision
                if rocket.invincible <= 0:
                    for u in ufos:
                        if dist(rx, ry, u.x, u.y) < 30:
                            lives            -= 1
                            rocket.invincible = 2.3
                            flash_timer       = 0.4
                            explosions.append(Explosion(rx, ry+PLAY_Y))
                            burst(particles, rx, ry+PLAY_Y, RED, 22)
                            if lives <= 0:
                                reason = "lives"
                                if score > best: best = score
                                pygame.time.delay(500)
                                state = "gameover"
                            else:
                                msg.show("HIT! SHIELD RECHARGING!", RED, 1.6)
                            break

                msg.update(dt)

        # ── DRAW ──────────────────────────────────────────────────
        if state == "menu":
            draw_menu(screen, bg_stars, chosen, best, t, skin_idx)

        elif state == "gameover":
            draw_gameover(screen, bg_stars, score, best,
                          chosen, reason, t, skin_idx)

        elif state == "playing":
            cfg = LEVELS[chosen]
            screen.fill(BG_DARK)
            neb = pygame.Surface((W, H+HUD_H), pygame.SRCALPHA)
            pygame.draw.circle(neb, (80,0,160,12),
                               (int(W*0.2), int(H*0.3)+HUD_H), 180)
            pygame.draw.circle(neb, (0,60,160,12),
                               (int(W*0.8), int(H*0.7)+HUD_H), 150)
            screen.blit(neb, (0,0))
            for s in bg_stars:
                s.draw(screen, t)

            if flash_timer > 0:
                alpha = int(100 * flash_timer / 0.4)
                fl    = pygame.Surface((W, H+HUD_H), pygame.SRCALPHA)
                pygame.draw.rect(fl, (255,60,90,alpha), (0,0,W,H+HUD_H))
                screen.blit(fl, (0,0))

            if 0 < time_left <= 10:
                pulse_a = int(35*(math.sin(t*0.008)+1)/2)
                pl      = pygame.Surface((W, H+HUD_H), pygame.SRCALPHA)
                pygame.draw.rect(pl, (255,60,90,pulse_a), (0,0,W,H+HUD_H))
                screen.blit(pl, (0,0))

            for item in items:       item.draw(screen)
            if power_up:             power_up.draw(screen)
            for e in explosions:     e.draw(screen)
            for u in ufos:           u.draw(screen)
            rocket.draw(screen, thrusting, t/1000.0, particles)
            for p in particles:      p.draw(screen)
            draw_hud(screen, score, lives, time_left, cfg["name"], cfg)
            msg.draw(screen)

        pygame.display.flip()

if __name__ == "__main__":
    main()
