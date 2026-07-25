#!/usr/bin/env python3
"""
Sam.Pr Miner v2 - TRUE 2:1 isometric room pre-renderer.
Each room (walls, diamond-grid floor, platforms, keys, door) is
rendered here at pixel level and stored in ROM as ready-made
Screen 2 images (pattern + color tables). The Z80 just block-copies
whichever one the current room selects. Two rooms are built from this
one script: Central Cavern (room 1, unchanged from the original
single-room version) and The Cold Room (room 2).

Outputs: src/bg_pattern.bin, src/bg_color.bin (room 1),
         src/bg_pattern2.bin, src/bg_color2.bin (room 2),
         src/leveldata.asm (both rooms' tables + room_tab),
         src/mask.bin, src/crumb.bin, build/preview2.png, build/preview3.png
"""
import os
import re
import math as _m
import copy
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X0, Y0 = 120, 64
MAPW, MAPH, MAPD = 8, 8, 6

PAL = {
    0: (0,0,0), 1: (0,0,0), 2: (33,200,66), 3: (94,220,120),
    4: (84,85,237), 5: (125,118,252), 6: (212,82,77), 7: (66,235,245),
    8: (252,85,84), 9: (255,121,120), 10: (212,193,84), 11: (230,206,128),
    12: (33,176,59), 13: (201,91,186), 14: (204,204,204), 15: (255,255,255),
}

W, H = 256, 192
img = [[1]*W for _ in range(H)]   # palette indices, 1 = black

def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img[y][x] = c

def proj(wx, wz, h=0):
    return X0 + wx - wz, Y0 + (wx + wz)//2 - h

# ------------------------------------------------------------------
# 1. Back walls (x=0 edge and z=0 edge), height ~56, panelled.
#    Colors and crest silhouette are parametrized per room.
# ------------------------------------------------------------------
def _wtop_cave(u):
    """rolling irregular cave-wall crest (Central Cavern)"""
    return int(46 + 7*_m.sin(u/11.0) + 4*_m.sin(u/4.7 + 1.3) + 2*_m.sin(u/2.3))

def _wtop_ice(u):
    """sharper, more jagged icicle-crest silhouette (The Cold Room)"""
    return int(44 + 6*abs(_m.sin(u/7.3)) + 5*abs(_m.sin(u/3.1 + 0.7)) + 3*_m.sin(u/2.0))

def _wtop_menagerie(u):
    """regular alternating tall/short posts - cage-bar silhouette
    (The Menagerie), deliberately regular instead of the other two
    rooms' organic/jagged crests"""
    return 38 + (12 if (int(u) % 12) < 6 else 4)

def _wtop_uranium(u):
    """sparse tall antenna/pylon spikes over a low, mostly-flat base -
    futuristic silhouette (Abandoned Uranium Workings)"""
    return 30 + (22 if (int(u) % 16) < 3 else 2)

def _wtop_kong(u):
    """dense, tall jungle canopy/vine crest (Kong Beast) - taller and
    more irregular than the cave crest, evoking overgrown vines rather
    than rock."""
    return int(50 + 10*abs(_m.sin(u/5.3)) + 6*abs(_m.sin(u/2.1 + 0.9)))

def _wtop_amoeba(u):
    """bubbly, rounded lab-wall silhouette (Wacky Amoebatrons) - soft
    repeating humps rather than jagged spikes, matching the room's
    cartoonish theme."""
    return int(36 + 8*abs(_m.sin(u/6.0)) + 3*abs(_m.sin(u/2.6)))

def _stone(u, v):
    """True on the dark joints between stacked irregular blocks"""
    band = (v + int(3*_m.sin(u/9.0))) // 11
    ju = (u + band*13 + int(3*_m.sin(v/5.0))) % 21
    jv = (v + int(2*_m.sin(u/6.0))) % 11
    return ju < 2 or jv < 2

def draw_walls(colors, crest_fn):
    lit, rock, joint = colors['lit'], colors['rock'], colors['joint']
    def wallpix(u, v):
        if v < 2:
            return lit
        if _stone(u, v):
            return joint
        return rock
    for wx in range(0, MAPW*16):
        sx, base = proj(wx, 0, 8)
        hh = crest_fn(wx)
        top = base - hh
        for sy in range(top, base):
            put(sx, sy, wallpix(wx, sy - top))
    for wz in range(0, MAPD*16):
        sx, base = proj(0, wz, 8)
        hh = crest_fn(MAPW*16 + wz*1.7)
        top = base - hh
        for sy in range(top, base):
            put(sx-1, sy, wallpix(wz + 100, sy - top))

# ------------------------------------------------------------------
# 2. Floor: sparse speckle over an optional base fill
# ------------------------------------------------------------------
def draw_floor(base, speckle, gaps=frozenset()):
    """base=None: leave black (cave dirt on bare black, original look).
    base=color: prefill the whole floor with it first (icy floor look).
    gaps: set of (bx,bz) map cells to leave undrawn (real pits - the
    physics grid has no floor tile there either, see render_room)."""
    for bz in range(MAPD):
        for bx in range(MAPW):
            if (bx, bz) in gaps:
                continue
            wx0, wz0 = bx*16, bz*16
            for dz in range(16):
                for dx in range(16):
                    u, v = wx0+dx, wz0+dz
                    sx, sy = proj(u, v, 8)
                    if base is not None:
                        put(sx, sy, base)
                    n = (u*u*29 + v*v*23 + u*v*13) & 255
                    if n < 64:
                        put(sx, sy, speckle)

def draw_floor_grid(base, line, gaps=frozenset()):
    """black tiles (one per map cell) divided by thin colored lines -
    a sci-fi floor grating look, used instead of the organic speckle."""
    for bz in range(MAPD):
        for bx in range(MAPW):
            if (bx, bz) in gaps:
                continue
            wx0, wz0 = bx*16, bz*16
            for dz in range(16):
                for dx in range(16):
                    u, v = wx0+dx, wz0+dz
                    sx, sy = proj(u, v, 8)
                    put(sx, sy, line if (dx < 1 or dz < 1) else base)

# ------------------------------------------------------------------
# 3. Iso cube/slab: diamond top + two visible faces (SE + SW)
# ------------------------------------------------------------------
def _facepix(u, d, col):
    """stone-face texture: sparse joints, short cracks, crisp base"""
    if d == 8:
        return 1                        # dark base line
    if (u + int(1.5*_m.sin(d*1.1))) % 9 == 0:
        return 1                        # sparse vertical joint
    if d == 4 and (u // 6) % 3 == 0:
        return 1                        # occasional short crack
    return col

def draw_slab(bx, bz, y, top_fill, top_edge, face_l, face_r,
              arrows=False, rocky=False, half=False, fancy=0, checker=False):
    """slab surface at h=8*(y+1), 8px thick sides (4 when half).
    fancy=1/2: Manic-Miner-style exit cube (2 = flash phase).
    checker: Processing Plant-style checkerboard top (alternating
    top_fill/top_edge in 4x4 blocks) instead of a solid fill."""
    h = 8*(y+1)
    depth = 8
    if half:
        h -= 4
        depth = 4
    wx0, wz0 = bx*16, bz*16
    for wz in range(17):
        for wx in range(17):
            sx, sy = proj(wx0+wx, wz0+wz, h)
            edge = wx in (0,16) or wz in (0,16)
            if fancy:
                ca, cb = (7, 15) if fancy == 1 else (15, 7)
                if edge:
                    c = cb
                else:
                    c = ca if ((wx0+wx)//4 + (wz0+wz)//4) % 2 == 0 else cb
            elif checker and not edge:
                c = top_fill if ((wx//4)+(wz//4)) % 2 == 0 else top_edge
            else:
                c = top_edge if edge else top_fill
                if arrows and not edge:
                    c = 7 if (wx % 8) < 3 else top_fill
            put(sx, sy, c)
    for wx in range(16):
        sx, sy = proj(wx0+wx, wz0+16, h)
        for d in range(1, depth+1):
            if fancy:
                put(sx, sy+d, 1 if d == depth else
                    (7 if ((wx0+wx+d)//2) % 2 == 0 else 4))
            elif rocky:
                c = _facepix(wx0+wx, 8 if d == depth else d, face_l)
                if c is not None:
                    put(sx, sy+d, c)
            else:
                put(sx, sy+d, face_l if wx % 4 else 1)
    for wz in range(17):
        sx, sy = proj(wx0+16, wz0+wz, h)
        for d in range(1, depth+1):
            if fancy:
                put(sx, sy+d, 1 if d == depth else
                    (4 if ((wz0+wz+d)//2) % 2 == 0 else 7))
            elif rocky:
                c = _facepix(wz0+wz+64, 8 if d == depth else d, face_r)
                if c is not None:
                    put(sx, sy+d, c)
            else:
                put(sx, sy+d, face_r if wz % 4 else 1)

# ------------------------------------------------------------------
# 4. Pickup art (key for room 1, ice-cream cone for room 2) + hazard
# art (spiky bush for room 1, ice-rock chunk for room 2)
# ------------------------------------------------------------------
KEY_ART = [
    "..WWWW.........",
    ".WW..HH........",
    ".W....H........",
    ".W....H........",
    ".WW..HH........",
    "..HHHH.........",
    "....HHHHHHHHHH.",
    "....HH...HH.HH.",
    ".........HH.HH.",
]

def _art_row(w, *segs):
    """helper: build a WxH-safe ascii-art row from (start,end,char)
    segments, '.' elsewhere - avoids hand-counting/misaligning columns."""
    row = ['.']*w
    for a, b, ch in segs:
        for i in range(a, b):
            row[i] = ch
    return ''.join(row)

# popsicle: a simple green ice block over a white stick - picked over
# an ice-cream cone as a cleaner shape at this size and a better fit
# for the room's ice theme
CONE_ART = [
    _art_row(16, (6,10,'V')),
    _art_row(16, (5,11,'V')),
    _art_row(16, (5,11,'V')),
    _art_row(16, (5,11,'V')),
    _art_row(16, (5,11,'V')),
    _art_row(16, (6,10,'V')),
    _art_row(16, (7,9,'R')),
    _art_row(16, (7,9,'R')),
    _art_row(16, (7,9,'R')),
]
CONE_COLORS = {'V': 2, 'R': 15}   # ice block, stick

# tiny red cube: a diamond top face over two trapezoid side faces, same
# 3-tone lit-from-above shading as the room's real iso slabs (just at
# pickup scale) - used in place of the gold key for Room5's "cubetti"
CUBE_ART = [
    _art_row(16, (6,10,'T')),
    _art_row(16, (4,12,'T')),
    _art_row(16, (2,14,'T')),
    _art_row(16, (2,8,'L'), (8,14,'S')),
    _art_row(16, (2,8,'L'), (8,14,'S')),
    _art_row(16, (2,8,'L'), (8,14,'S')),
    _art_row(16, (3,8,'L'), (8,13,'S')),
    _art_row(16, (4,8,'L'), (8,12,'S')),
    _art_row(16),
]
CUBE_COLORS = {'T': 8, 'L': 6, 'S': 9}   # top highlight, left face, right face

def draw_key(bx, bz, y, art=KEY_ART, color_of=lambda ch: 15, h_off=26):
    """floating pickup above surface h=8*(y) (y = feet block) - high
    enough that reaching it takes a jump, by design. h_off lets a
    specific pickup sit closer to/further from its platform's surface
    when the default 26px float reads as disconnected from it."""
    h = 8*y + h_off
    sx, sy = proj(bx*16+8, bz*16+8, h)
    sx -= 7
    pix = set()
    for r, row in enumerate(art):
        for cidx, ch in enumerate(row):
            if ch != '.':
                pix.add((cidx, r))
    for cx, r in pix:
        for dx2 in (-1, 0, 1):
            for dy2 in (-1, 0, 1):
                if (cx+dx2, r+dy2) not in pix:
                    put(sx+cx+dx2, sy+r+dy2, 1)
    for r, row in enumerate(art):
        for cidx, ch in enumerate(row):
            if ch != '.':
                put(sx+cidx, sy+r, color_of(ch))
    return sx, sy

BUSH_ART = [
    "..3...3..3...",
    ".3.2.3..2..3.",
    "..2.3.2.3.2..",
    ".8.23.2.32.8.",
    "..322232232..",
    "...232322....",
    "....2322.....",
    ".....22......",
    ".....22......",
    "....2222.....",
]
ICE_ROCK_ART = [
    "..7.......7..",
    ".775.....577.",
    "77555.....577",
    "7F55555555F77",
    "F5555F55555F7",
    "75555555555F7",
    ".7F5555555F7.",
    "..7F55555F7..",
    "...7FFFFF7...",
    "....77777....",
]

# poison puddle, replacing both the spiders and the bear-trap attempt
# (Fausto: neither one came out looking good) - a flat pool is much
# more forgiving at this size than a spider/trap's fine mechanical
# detail, since a puddle is naturally an irregular blob rather than
# something that needs to read as legs or teeth. Violet fill ('V' -
# draw_hazard's new letter for PAL index 13, the actual purple/magenta
# entry; digits 0-9 don't reach it) with a scattered lighter/white
# bubble speckle for a toxic, faintly rippling surface.
def _puddle_art():
    w, h = 16, 8
    cx, cy = (w-1)/2, (h-1)/2
    rx, ry = 7.3, 3.3
    grid = [['.']*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            dx, dy = (x-cx)/rx, (y-cy)/ry
            if dx*dx + dy*dy <= 1.0:
                n = (x*x*29 + y*y*23 + x*y*13) & 255
                grid[y][x] = 'F' if n < 55 else 'V'
    return [''.join(row) for row in grid]

PUDDLE_ART = _puddle_art()

# glowing green uranium bar/fuel rod (Abandoned Uranium Workings) -
# same "simple bold blob, not fine linework" lesson as the puddle: a
# rounded rectangle, bright-green fill with a scattered lighter/white
# speckle for a faint radioactive glow.
def _uranium_bar_art():
    w, h = 16, 6
    inset = [2, 1, 0, 0, 1, 2]   # per-row side inset -> rounded ends
    grid = [['.']*w for _ in range(h)]
    for y in range(h):
        for x in range(inset[y], w-inset[y]):
            n = (x*x*29 + y*y*23 + x*y*13) & 255
            grid[y][x] = 'F' if n < 45 else '2'
    return [''.join(row) for row in grid]

URANIUM_BAR_ART = _uranium_bar_art()

def draw_hazard(bx, bz, surf, art):
    """spiky plant/icicle standing on a surface at height surf.
    art chars: digit = literal palette index, 'F' = 15 (white),
    'V' = 13 (violet/magenta), 'Y' = 11 (light yellow) - PAL indices
    >9 without their own single-digit form."""
    sx, sy = proj(bx*16+8, bz*16+8, surf)
    top = sy - len(art) + 1
    pix = set()
    for r, row in enumerate(art):
        for cidx, ch in enumerate(row):
            if ch != '.':
                pix.add((cidx, r))
    for cx, r in pix:
        for dx2 in (-1, 0, 1):
            for dy2 in (-1, 0, 1):
                if (cx+dx2, r+dy2) not in pix:
                    put(sx-6+cx+dx2, top+r+dy2, 1)
    for r, row in enumerate(art):
        for cidx, ch in enumerate(row):
            if ch != '.':
                c = 15 if ch == 'F' else (13 if ch == 'V' else (11 if ch == 'Y' else int(ch)))
                put(sx-6+cidx, top+r, c)

# ------------------------------------------------------------------
# 4b. Slab silhouette + pre-computed mask windows (for sprite masking)
# Pure geometry - identical for every room, computed once.
# ------------------------------------------------------------------
def build_masks():
    sil = {}
    def rec(sx, sy, rs):
        k = (sx, sy)
        if sil.get(k, -1) < rs:
            sil[k] = rs
    for wz2 in range(17):
        for wx2 in range(17):
            sx, sy = proj(32+wx2, 32+wz2, 8)
            rec(sx, sy, wx2+wz2)
    for wx2 in range(16):
        sx, sy = proj(32+wx2, 48, 8)
        for d in range(1, 9):
            rec(sx, sy+d, wx2+16)
    for wz2 in range(17):
        sx, sy = proj(48, 32+wz2, 8)
        for d in range(1, 9):
            rec(sx, sy+d, 16+wz2)
    ax, ay = 120, 88
    wx0, wy0 = ax-16-15, ay-15
    out = bytearray()
    for level in range(8):
        thr = level*4
        for dy in range(40):
            for dx in range(64):
                sx0, sy0 = wx0+dx, wy0+dy
                left, right = [], []
                for r in range(16):
                    bits = 0
                    for cx in range(16):
                        rs = sil.get((sx0+cx, sy0+r), -1)
                        bits = (bits << 1) | (1 if rs >= thr else 0)
                    left.append((bits >> 8) & 255)
                    right.append(bits & 255)
                out += bytes(left) + bytes(right)
    open(os.path.join(ROOT,'src','mask.bin'),'wb').write(out)
    return wx0 - ax, wy0 - ay

MASK_RELX, MASK_RELY = build_masks()

# ------------------------------------------------------------------
# 5. Encode Screen2 pattern+color with 2-color-per-byte-row auto-fix
# ------------------------------------------------------------------
def encode_screen(image):
    pattern = bytearray(6144)
    color   = bytearray(6144)
    fixes = 0
    for crow in range(24):
        for ccol in range(32):
            for r in range(8):
                y = crow*8 + r
                px8 = image[y][ccol*8:(ccol+1)*8]
                cnt = {}
                for p in px8:
                    cnt[p] = cnt.get(p, 0) + 1
                cols = sorted(cnt, key=lambda k: -cnt[k])
                if len(cols) > 2:
                    fixes += 1
                    keep = cols[:2]
                    px8 = [p if p in keep else keep[0] for p in px8]
                    cols = keep
                if len(cols) == 1:
                    bg, fg = cols[0], 15
                else:
                    bg, fg = cols[0], cols[1]
                    if bg == 1 or fg == 1:
                        if fg == 1: fg, bg = bg, 1
                bits = 0
                for p in px8:
                    bits = (bits << 1) | (1 if p == fg else 0)
                off = crow*256 + ccol*8 + r
                pattern[off] = bits
                color[off]   = (fg << 4) | bg
    return pattern, color, fixes

def db(bs, per=13):
    out = []
    for i in range(0, len(bs), per):
        out.append("        db " + ",".join(f"0{b:02X}h" for b in bs[i:i+per]))
    return "\n".join(out)

# ==================================================================
# Room builder: everything below is per-room and driven by `spec`.
# ==================================================================
T_EMPTY, T_STONE, T_CONV, T_CRUMB, T_KEY, T_DOORT, T_DOORB = range(7)
T_EXIT = 7

def draw_lift_marker(bx, bz, color=11):
    """flat ring painted directly on the floor at the lift's boarding
    cell. The lift sprite itself is only visible at floor level for a
    fraction of its cycle (it spends most of its time up near the
    summit), so without a permanent floor cue a player has no way to
    know where to stand and wait for it - found via Fausto's own
    playtesting ("non capisco dove devo mettermi")."""
    cx, cz = bx*16+8, bz*16+8
    for dz in range(-7, 8):
        for dx in range(-7, 8):
            r2 = dx*dx + dz*dz
            if 28 <= r2 <= 50:
                sx, sy = proj(cx+dx, cz+dz, 8)
                put(sx, sy, color)

def _draw_room_floor(spec):
    gaps = spec.get('floor_gaps', frozenset())
    if spec.get('floor_style') == 'grid':
        draw_floor_grid(spec['floor_base'], spec['floor_speckle'], gaps)
    else:
        draw_floor(spec['floor_base'], spec['floor_speckle'], gaps)
    if spec.get('lift_wx', 0xFF) != 0xFF:
        draw_lift_marker(spec['lift_wx']//16, spec['lift_wz']//16)

def pack_sprite_frames(frames):
    """N x 16x16 ascii ('X'=set) -> N*32 bytes (16x16 MSX sprite pattern:
    left-half 16 rows then right-half 16 rows, per frame)."""
    out = []
    for fr in frames:
        left, right = [], []
        for r in fr:
            bits = 0
            for ch in r:
                bits = (bits << 1) | (1 if ch == 'X' else 0)
            left.append((bits >> 8) & 255)
            right.append(bits & 255)
        out += left + right
    return out

def render_room(spec):
    """spec keys: label (''/'2'), wallcol, crest_fn, floor_base,
    floor_speckle, slabs_def (bx,bz,y,type list), keys, hazards
    (list of (bx,bz,surf)), hazard_art, exit_bx, exit_bz, exit_y,
    style (dict tile->draw_slab kwargs), crumb_units (may be empty),
    enemy_frames (2x 16x16 ascii), name.
    Returns a dict of everything needed for emission + the pattern
    for the build/previewN.png sanity image."""
    global img
    label = spec['label']
    EXIT_BX, EXIT_BZ, EXIT_Y = spec['exit_bx'], spec['exit_bz'], spec['exit_y']

    gaps = spec.get('floor_gaps', frozenset())
    grid = [[[0]*MAPW for _ in range(MAPH)] for _ in range(MAPD)]
    for z in range(MAPD):
        for x in range(MAPW):
            if (x, z) not in gaps:
                grid[z][0][x] = T_STONE

    slabs = []
    for (bx, bz, y, t) in spec['slabs_def']:
        grid[bz][y][bx] = t
        slabs.append((bx, bz, y, t))
    grid[EXIT_BZ][EXIT_Y][EXIT_BX] = T_STONE
    slabs.append((EXIT_BX, EXIT_BZ, EXIT_Y, T_EXIT))

    keys = spec['keys']
    for k in keys:
        bx, bz, y = k[0], k[1], k[2]
        grid[bz][y][bx] = T_KEY

    STYLE = dict(spec['style'])
    STYLE[T_EXIT] = dict(top_fill=7, top_edge=15, face_l=4, face_r=7, fancy=1)
    STYLE_EXIT_FLASH = dict(top_fill=15, top_edge=7, face_l=7, face_r=15, fancy=2)

    def draw_shadow(bx, bz):
        for wz2 in range(16):
            for wx2 in range(16):
                sx, sy = proj(bx*16+wx2, bz*16+wz2, 8)
                put(sx, sy, 1)

    def compose(cellstates, flash=False):
        nonlocal_img = [[1]*W for _ in range(H)]
        global img
        img = nonlocal_img
        draw_walls(spec['wallcol'], spec['crest_fn'])
        _draw_room_floor(spec)
        for bx,bz,y,t in slabs:
            if cellstates.get((bx, bz, y), 0) < 2:
                draw_shadow(bx, bz)
        for bx,bz,y,t in sorted(slabs, key=lambda s: (s[0]+s[1], s[2])):
            st = cellstates.get((bx, bz, y), 0)
            if st == 2:
                continue
            style = STYLE_EXIT_FLASH if (flash and t == T_EXIT) else STYLE[t]
            draw_slab(bx, bz, y, half=(st == 1), **style)
        for bx,bz,surf,*_ in spec['hazards']:
            draw_hazard(bx, bz, surf, spec['hazard_art'])
        if spec.get('lever_switch'):
            _sw_bx, _sw_bz = spec['lever_switch']
            draw_hazard(_sw_bx, _sw_bz, spec['lever_switch_surf'], LEVER_ART)
        return img

    img = [[1]*W for _ in range(H)]
    draw_walls(spec['wallcol'], spec['crest_fn'])
    _draw_room_floor(spec)
    for bx,bz,y,t in slabs:
        draw_shadow(bx, bz)
    slab_surf = [[0]*W for _ in range(H)]
    for bx,bz,y,t in sorted(slabs, key=lambda s: (s[0]+s[1], s[2])):
        _before = copy.deepcopy(img)
        draw_slab(bx, bz, y, **STYLE[t])
        _s = 8*(y+1)
        for _yy in range(H):
            rb, ra = _before[_yy], img[_yy]
            for _xx in range(W):
                if ra[_xx] != rb[_xx]:
                    slab_surf[_yy][_xx] = _s
    for bx,bz,surf,*_ in spec['hazards']:
        draw_hazard(bx, bz, surf, spec['hazard_art'])
    # lever_switch: a purely decorative prop marking where to pull the
    # lever (Fausto: "non vedo la leva" - the switch had no visual at
    # all, only a collision check in main.asm's lever_check). Drawn
    # directly here (and in compose(), so lever_platform's before/after
    # diff-rect isn't thrown off by its presence) rather than folded
    # into spec['hazards'], since it must NOT be lethal like a real
    # hazard - it's keyed off room_lever_ptr/lever_check, not
    # hazards_tab/hazard_check.
    if spec.get('lever_switch'):
        _sw_bx, _sw_bz = spec['lever_switch']
        draw_hazard(_sw_bx, _sw_bz, spec['lever_switch_surf'], LEVER_ART)

    cover = [[0]*MAPW for _ in range(MAPD)]
    for bz in range(MAPD):
        for bx in range(MAPW):
            wx, wz = bx*16+8, bz*16+8
            sx = X0 + wx - wz
            feet = Y0 + (wx+wz)//2 - 8
            mh = 0
            for yy in range(max(0,feet-12), min(H,feet)):
                for xx in range(max(0,sx-4), min(W,sx+4)):
                    s = slab_surf[yy][xx]
                    if s >= 32 and s > mh:
                        mh = s
            cover[bz][bx] = mh

    base_img = img
    pattern, color, fixes = encode_screen(img)

    # crumble variants (only rooms with crumb_units). Most rooms keep
    # every group's rendered variants in ONE bank ('a', the common
    # case); a room can optionally supply crumb_unit_banks (same
    # length as crumb_units) to route some groups into a SEPARATE bank
    # instead - needed once a room has enough crumbling cells that all
    # of them together would blow the crumble bank's 8KB budget (see
    # the sampr-miner-project memory - Room9 hit this exactly).
    CRUMB_UNITS = spec['crumb_units']
    CRUMB_BANK_LABELS = spec.get('crumb_unit_banks', ['a'] * len(CRUMB_UNITS))
    base_pat, base_col = bytes(pattern), bytes(color)
    crumb_meta = []
    crumb_bins = {}
    _sorted_slabs = sorted(slabs, key=lambda s: -(s[0]+s[1]))
    for gi, cells in enumerate(CRUMB_UNITS):
        bank_label = CRUMB_BANK_LABELS[gi]
        crumb_bin = crumb_bins.setdefault(bank_label, bytearray())
        n = len(cells)
        combos = [(s0,) for s0 in range(3)] if n == 1 else \
                 [(s0, s1) for s0 in range(3) for s1 in range(3)]
        encs = []
        rect = None
        for combo in combos:
            cs = {cells[i]: combo[i] for i in range(n)}
            iv = compose(cs)
            pv, cv, _ = encode_screen(iv)
            encs.append((pv, cv))
            for crow in range(24):
                for ccol in range(32):
                    off = crow*256 + ccol*8
                    if pv[off:off+8] != base_pat[off:off+8] or cv[off:off+8] != base_col[off:off+8]:
                        if rect is None:
                            rect = [ccol, crow, ccol, crow]
                        else:
                            rect[0] = min(rect[0], ccol); rect[1] = min(rect[1], crow)
                            rect[2] = max(rect[2], ccol); rect[3] = max(rect[3], crow)
        c0, r0, c1, r1 = rect
        w, hgt = c1-c0+1, r1-r0+1
        rectsize = w*hgt*16
        base_off = len(crumb_bin)
        for pv, cv in encs:
            for rr in range(r0, r1+1):
                for cc in range(c0, c1+1):
                    off = rr*256 + cc*8
                    crumb_bin += pv[off:off+8]
            for rr in range(r0, r1+1):
                for cc in range(c0, c1+1):
                    off = rr*256 + cc*8
                    crumb_bin += cv[off:off+8]
        crumb_bins[bank_label] = crumb_bin
        idxs = []
        for (bx, bz, y) in cells:
            for i, s in enumerate(_sorted_slabs):
                if (s[0], s[1], s[2]) == (bx, bz, y):
                    idxs.append(i)
        while len(idxs) < 2:
            idxs.append(255)
        crumb_meta.append((c0, r0, w, hgt, rectsize, base_off, cells, idxs, bank_label))

    img = base_img

    # exit blink variant. If a lever_platform sits on TOP of the exit
    # cell (covering it - see the lever mechanic below), the exit's
    # own pixels are entirely hidden in the true base image (the
    # blocker's side face extends exactly far enough to butt against
    # the exit slab's top, one level below - real bug hit: the flash-
    # rect diff came back completely empty, since there was nothing
    # visible to flash). The win-flash can only ever actually play
    # AFTER the lever is pulled anyway (exit_check requires it), so
    # capture both the normal and flash exit_gfx variants against the
    # POST-LEVER image (blocker already removed) instead of the raw
    # base image in that case - matching what the player will really
    # see at that moment.
    lever_platform = spec.get('lever_platform')
    _exit_base_img = compose({lever_platform: 2}) if lever_platform else base_img
    _exit_base_pat, _exit_base_col, _ = encode_screen(_exit_base_img)
    _fimg = compose({lever_platform: 2} if lever_platform else {}, flash=True)
    _fp, _fc, _ = encode_screen(_fimg)
    _erect = None
    for crow in range(24):
        for ccol in range(32):
            off = crow*256 + ccol*8
            if _fp[off:off+8] != _exit_base_pat[off:off+8] or _fc[off:off+8] != _exit_base_col[off:off+8]:
                if _erect is None:
                    _erect = [ccol, crow, ccol, crow]
                else:
                    _erect[0] = min(_erect[0], ccol); _erect[1] = min(_erect[1], crow)
                    _erect[2] = max(_erect[2], ccol); _erect[3] = max(_erect[3], crow)
    EXC0, EXR0, EXC1, EXR1 = _erect
    EXW = EXC1 - EXC0 + 1
    EXNROW = EXR1 - EXR0 + 1
    exit_gfx = []
    for pv, cv in ((_exit_base_pat, _exit_base_col), (_fp, _fc)):
        blk = bytearray()
        for rr in range(EXR0, EXR1+1):
            for cc in range(EXC0, EXC1+1):
                off = rr*256 + cc*8
                blk += pv[off:off+8]
        for rr in range(EXR0, EXR1+1):
            for cc in range(EXC0, EXC1+1):
                off = rr*256 + cc*8
                blk += cv[off:off+8]
        exit_gfx.append(blk)

    img = base_img
    pickup_art = spec.get('pickup_art', KEY_ART)
    pickup_colors = spec.get('pickup_colors')
    color_of = (lambda ch: pickup_colors[ch]) if pickup_colors else (lambda ch: 15)
    key_rects = []
    for k in keys:
        bx, bz, y = k[0], k[1], k[2]
        h_off = k[3] if len(k) > 3 else 26
        sx, sy = draw_key(bx, bz, y, art=pickup_art, color_of=color_of, h_off=h_off)
        c0, r0 = sx//8, sy//8
        key_rects.append((bx, bz, y, c0, r0))
    pattern2, color2, _ = encode_screen(img)
    keys_gfx = []
    for bx,bz,y,c0,r0 in key_rects:
        blk = bytearray()
        for rr in (0,1):
            for cc in (0,1):
                off = (r0+rr)*256 + (c0+cc)*8
                blk += pattern2[off:off+8]
        for rr in (0,1):
            for cc in (0,1):
                off = (r0+rr)*256 + (c0+cc)*8
                blk += color2[off:off+8]
        keys_gfx.append(blk)

    # enemy sprite (2 frames, 16x16 silhouette)
    enemy_bytes = pack_sprite_frames(spec['enemy_frames'])

    # 2nd enemy (optional, mirrored-pair only - see room_enemy2_ptr in
    # main.asm): its own 2-frame sprite, packed the same way.
    enemy2_bytes = pack_sprite_frames(spec['enemy2_frames']) if spec.get('enemy2_frames') else None

    # falling debris (optional - see room_debris_ptr in main.asm)
    debris_bytes = pack_sprite_frames(spec['debris_frames']) if spec.get('debris_frames') else None

    # random platform-hopping enemy (optional - see room_hopper_ptr)
    hopper_bytes = pack_sprite_frames(spec['hopper_frames']) if spec.get('hopper_frames') else None

    # roller-conveyor packages, 2 independent slots (optional - see
    # room_pkg_ptr/room_pkg2_ptr)
    pkg_bytes = pack_sprite_frames(spec['pkg_frames']) if spec.get('pkg_frames') else None
    pkg2_bytes = pack_sprite_frames(spec['pkg2_frames']) if spec.get('pkg2_frames') else None

    # sun-ray screen divider (optional - see room_ray_ptr)
    ray_bytes = pack_sprite_frames(spec['ray_frames']) if spec.get('ray_frames') else None

    # lever: a switch cell that INSTANTLY removes one specific slab
    # (typically one covering the exit) when Sam touches it, gated on
    # exit_check separately from the key count. Deliberately NOT built
    # on the crumb_units/cell_at/degrade_cell machinery every other
    # room's crumbling uses - that system is scanned every frame by
    # position, so simply standing on the covered slab would silently
    # start degrading it via the ordinary touch-crumble path; the
    # lever needs the covered slab to stay rock-solid until the
    # switch itself is touched, deliberately, once. Reuses only the
    # LOW-LEVEL rendering primitive (compose() with the target cell
    # forced to state 2, i.e. "not drawn" - the exact same technique
    # crumb_units already uses for their own "gone" variant) to
    # capture a single before/after pixel diff, with its own separate
    # ROM fields and a dedicated lever_check/lever_pull routine pair
    # in main.asm - zero shared runtime code path with crumbling, so
    # zero risk of this new mechanic disturbing any proven room.
    lever_data = None
    lever_platform = spec.get('lever_platform')
    if lever_platform:
        lp_img = compose({lever_platform: 2})
        lp_pat, lp_col, _ = encode_screen(lp_img)
        rect = None
        for crow in range(24):
            for ccol in range(32):
                off = crow*256 + ccol*8
                if lp_pat[off:off+8] != base_pat[off:off+8] or lp_col[off:off+8] != base_col[off:off+8]:
                    if rect is None:
                        rect = [ccol, crow, ccol, crow]
                    else:
                        rect[0] = min(rect[0], ccol); rect[1] = min(rect[1], crow)
                        rect[2] = max(rect[2], ccol); rect[3] = max(rect[3], crow)
        c0, r0, c1, r1 = rect
        lever_bin = bytearray()
        for rr in range(r0, r1+1):
            for cc in range(c0, c1+1):
                off = rr*256 + cc*8
                lever_bin += lp_pat[off:off+8]
        for rr in range(r0, r1+1):
            for cc in range(c0, c1+1):
                off = rr*256 + cc*8
                lever_bin += lp_col[off:off+8]
        lp_bx, lp_bz, lp_y = lever_platform
        lp_slabidx = 0xFF
        for i, s in enumerate(_sorted_slabs):
            if (s[0], s[1], s[2]) == (lp_bx, lp_bz, lp_y):
                lp_slabidx = i
                break
        sw_bx, sw_bz = spec['lever_switch']
        lever_data = dict(
            switch_bx=sw_bx, switch_bz=sw_bz,
            map_bx=lp_bx, map_bz=lp_bz, map_y=lp_y, slabidx=lp_slabidx,
            c0=c0, r0=r0, c1=c1+1, r1=r1+1,   # +1: crumb_blit's own row/col bounds are EXCLUSIVE, matching emit_crumb_tab's c0+w convention
            data=lever_bin,
        )

    MASK_COLORS = {t: STYLE[t]['top_fill'] for t in STYLE if t != T_EXIT}
    MASK_COLORS[T_EXIT] = 7
    slab_lines = []
    for bx,bz,y,t in _sorted_slabs:
        sxN = 120 + 16*(bx-bz)
        syN = 64 + 8*(bx+bz) - 8*(y+1)
        winx0 = (sxN + MASK_RELX) & 0xFF
        winy0 = (syN + MASK_RELY) & 0xFF
        base  = 16*(bx+bz)
        surf  = 8*(y+1)
        slab_lines.append(f"        db {winx0},{winy0},{base},{surf},{MASK_COLORS[t]}")

    return dict(
        label=label, pattern=pattern, color=color, fixes=fixes,
        grid=grid, keys=keys, key_rects=key_rects, keys_gfx=keys_gfx,
        slabs_sorted=_sorted_slabs, slab_lines=slab_lines,
        crumb_meta=crumb_meta, crumb_bin=crumb_bins.get('a', bytearray()),
        crumb_bins=crumb_bins,
        exit_gfx=exit_gfx, EXC0=EXC0, EXR0=EXR0, EXNROW=EXNROW, EXW=EXW,
        cover=cover, enemy_bytes=enemy_bytes, base_img=base_img,
        lever_data=lever_data,
        enemy2_bytes=enemy2_bytes,
        en2xmin=spec.get('en2xmin', 0), en2xmax=spec.get('en2xmax', 0),
        en2z=spec.get('en2z', 0), en2surf=spec.get('en2surf', 0),
        en2_centerx=spec.get('en2_centerx', 0), enemy2_color=spec.get('enemy2_color', 0),
        debris_bytes=debris_bytes,
        debris_hstart=spec.get('debris_hstart', 0), debris_hend=spec.get('debris_hend', 0),
        debris_speed=spec.get('debris_speed', 0), debris_pause=spec.get('debris_pause', 0),
        debris_color=spec.get('debris_color', 0), debris_cols=spec.get('debris_cols', []),
        hopper_bytes=hopper_bytes,
        hop_speed=spec.get('hop_speed', 0), hop_pause=spec.get('hop_pause', 0),
        hop_bump=spec.get('hop_bump', 0), hop_color=spec.get('hop_color', 0),
        hop_cols=spec.get('hop_cols', []),
        pkg_bytes=pkg_bytes,
        pkg_speed=spec.get('pkg_speed', 0), pkg_pause=spec.get('pkg_pause', 0),
        pkg_color=spec.get('pkg_color', 0), pkg_start=spec.get('pkg_start'),
        pkg_slide=spec.get('pkg_slide', 0), pkg_fend=spec.get('pkg_fend', 0),
        pkg2_bytes=pkg2_bytes,
        pkg2_speed=spec.get('pkg2_speed', 0), pkg2_pause=spec.get('pkg2_pause', 0),
        pkg2_color=spec.get('pkg2_color', 0), pkg2_start=spec.get('pkg2_start'),
        pkg2_slide=spec.get('pkg2_slide', 0), pkg2_fend=spec.get('pkg2_fend', 0),
        ray_bytes=ray_bytes,
        ray_period=spec.get('ray_period', 0), ray_width=spec.get('ray_width', 0),
        ray_color=spec.get('ray_color', 0), ray_cols=spec.get('ray_cols', []),
        exit_bx=EXIT_BX, exit_bz=EXIT_BZ, exit_y=EXIT_Y,
        name=spec['name'], enxmin=spec['enxmin'], enxmax=spec['enxmax'],
        enz=spec['enz'], ensurf=spec['ensurf'], enemy_color=spec['enemy_color'],
        en_axis=spec.get('en_axis', 0), en_centerx=spec.get('en_centerx', 0),
        lift_wx=spec.get('lift_wx', 0xFF), lift_wz=spec.get('lift_wz', 0),
        lift_ymin=spec.get('lift_ymin', 0), lift_ymax=spec.get('lift_ymax', 0),
        map_label=spec.get('map_label'),
        hazards=spec['hazards'],
        crumb_continuous=spec.get('crumb_continuous', 0),
    )

# ------------------------------------------------------------------
# ROOM 1 SPEC: Central Cavern - values unchanged from the original
# single-room script, so its output bytes stay byte-identical.
# ------------------------------------------------------------------
room1_slabs = []
for x in (2,3,4):
    t = T_CRUMB if x == 4 else T_STONE
    room1_slabs.append((x,4,2,t))
for x in (3,4,5):
    room1_slabs.append((x,2,2,T_CONV))
for x in (1,2):
    room1_slabs.append((x,0,3,T_CRUMB))

ROOM1 = dict(
    label='',
    wallcol=dict(lit=8, rock=6, joint=1),
    crest_fn=_wtop_cave,
    floor_base=None, floor_speckle=6,
    slabs_def=room1_slabs,
    style={
        T_STONE: dict(top_fill=11, top_edge=15, face_l=6,  face_r=8, rocky=True),
        T_CRUMB: dict(top_fill=14, top_edge=15, face_l=6,  face_r=8, rocky=True),
        T_CONV:  dict(top_fill=4,  top_edge=5,  face_l=6,  face_r=8, arrows=True, rocky=True),
    },
    keys=[(3,4,3,14), (4,2,3,14), (1,0,4)],
    exit_bx=6, exit_bz=0, exit_y=1,
    hazards=[(1, 2, 8), (5, 1, 8), (2, 4, 24)],
    hazard_art=BUSH_ART,
    crumb_units=[[(1,0,3), (2,0,3)], [(4,4,2)]],
    enemy_frames=[[
        "................",
        "....XXXXXXXX....",
        "...XX.XXXX.XX...",
        "...X.X.XX.X.X...",
        "...XXXXXXXXXX...",
        "....XXXXXXXX....",
        "......XXXX......",
        "....XXXXXXXX....",
        "...XX.XXXX.XX...",
        "..XX..XXXX..XX..",
        ".....XX..XX.....",
        "....XX....XX....",
        "...XX......XX...",
        "..XXX......XXX..",
        "................",
        "................",
    ],[
        "................",
        "....XXXXXXXX....",
        "...XX.XXXX.XX...",
        "...X.X.XX.X.X...",
        "...XXXXXXXXXX...",
        "....XXXXXXXX....",
        "......XXXX......",
        "....XXXXXXXX....",
        "....X.XXXX.X....",
        "....X.XXXX.X....",
        ".....XX..XX.....",
        ".....XX..XX.....",
        ".....XX..XX.....",
        "....XXX..XXX....",
        "................",
        "................",
    ]],
    enxmin=52, enxmax=91, enz=40, ensurf=24, enemy_color=3,
    name="CENTRAL CAVERN",
)

# ------------------------------------------------------------------
# ROOM 2 SPEC: The Cold Room - ice palette, fixed (non-crumbling)
# platforms, icicle hazards, polar bear patrolling the final approach
# to the exit cube (must be timed past, like Central Cavern's guard).
# ------------------------------------------------------------------
room2_slabs_def = [
    (2, 2, 1, T_STONE),   # step 1, near spawn
    (4, 4, 2, T_STONE),   # step 2, mid-room
    (6, 3, 1, T_STONE),   # staging platform right before the exit
    (3, 2, 2, T_CRUMB),   # intermediate crumbling platform
    (4, 2, 3, T_CRUMB),   # high crumbling platform - a cone hides under it
]

def _bar(w, *ranges):
    """helper: a WxH-safe row of 'X' over the given (start,end) ranges,
    '.' elsewhere - avoids hand-counting characters in ascii art."""
    row = ['.']*w
    for a, b in ranges:
        for i in range(a, b):
            row[i] = 'X'
    return ''.join(row)

# polar bear, rearing up on its hind legs, swiping - round ears/head
# and a distinct chunky body/legs read more like an actual bear than
# the earlier abstract claw-diamond shape. The two frames swing the
# arms from fully flared out to pulled in tight against the body, so
# the ~0.3s alternation reads as a clear swipe/roar instead of a subtle
# wobble (the first attempt only shifted limbs by a pixel or two, which
# didn't read as animated at all at this size).
BEAR_A = [
    _bar(16, (3,5), (11,13)),   # ears
    _bar(16, (3,5), (11,13)),   # ears
    _bar(16, (4,12)),           # head
    _bar(16, (4,12)),           # head/snout
    _bar(16, (5,11)),           # neck
    _bar(16, (2,6), (10,14)),   # shoulders, arms starting to raise
    _bar(16, (1,5), (11,15)),   # paws swung out wide (swipe extended)
    _bar(16, (2,14)),           # torso (widest)
    _bar(16, (2,14)),           # torso
    _bar(16, (3,13)),           # torso taper
    _bar(16, (4,12)),           # waist
    _bar(16, (4,7), (9,12)),    # legs apart
    _bar(16, (4,7), (9,12)),    # legs
    _bar(16, (3,7), (9,13)),    # feet
    _bar(16),
    _bar(16),
]
BEAR_B = [
    _bar(16, (3,5), (11,13)),
    _bar(16, (3,5), (11,13)),
    _bar(16, (4,12)),
    _bar(16, (4,12)),
    _bar(16, (5,11)),
    _bar(16, (4,12)),           # arms pulled all the way in (swipe retracted)
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (3,6), (10,13)),   # legs shifted the other way
    _bar(16, (3,6), (10,13)),
    _bar(16, (4,8), (8,12)),
    _bar(16),
    _bar(16),
]

ROOM2 = dict(
    label='2',
    wallcol=dict(lit=15, rock=7, joint=1),
    crest_fn=_wtop_ice,
    floor_base=15, floor_speckle=5,
    slabs_def=room2_slabs_def,
    style={
        T_STONE: dict(top_fill=15, top_edge=7, face_l=5, face_r=4, rocky=True),
        T_CRUMB: dict(top_fill=7,  top_edge=15, face_l=5, face_r=4, rocky=True),
    },
    keys=[(2,2,2,14), (4,4,3,14), (4,2,2)],   # 3rd cone: under the high crumbler
    pickup_art=CONE_ART, pickup_colors=CONE_COLORS,
    exit_bx=7, exit_bz=3, exit_y=1,
    hazards=[(3, 5, 8), (5, 1, 8)],  # must avoid (1,4): the shared spawn cell
    hazard_art=ICE_ROCK_ART,
    crumb_units=[[(3,2,2)], [(4,2,3)]],
    enemy_frames=[BEAR_A, BEAR_B],
    enxmin=92, enxmax=124, enz=56, ensurf=16, enemy_color=14,
    name="THE COLD ROOM",
    # bank1 overflow ("Negative BLOCK?") from Room18's own data -
    # relocate this room's map too, same routine fix as every recent
    # room.
    map_label='level_map2',
)

# chicken, running back and forth along the crumbling platform row -
# same patrol/kill mechanic as the guard/bear, just reskinned. Frame A
# has legs together (mid-stride), frame B has them splayed wide, for
# a clearly-readable run cycle (a subtler leg shift didn't read as
# animated at all on the bear's first attempt).
CHICKEN_A = [
    _bar(16, (7,9)),            # comb
    _bar(16, (6,10)),           # head
    _bar(16, (5,11)),           # head/cheeks
    _bar(16, (6,10)),           # neck
    _bar(16, (4,12)),           # body top
    _bar(16, (3,13)),           # body
    _bar(16, (2,14)),           # body (widest)
    _bar(16, (2,14)),           # body
    _bar(16, (2,14)),           # body
    _bar(16, (3,13)),           # body taper
    _bar(16, (4,12)),           # lower body
    _bar(16, (5,8), (9,12)),    # legs together
    _bar(16, (5,8), (9,12)),    # legs
    _bar(16, (4,9), (8,13)),    # feet
    _bar(16),
    _bar(16),
]
CHICKEN_B = [
    _bar(16, (7,9)),
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (6,10)),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (3,6), (10,13)),   # legs splayed wide (running stride)
    _bar(16, (3,6), (10,13)),
    _bar(16, (2,7), (9,14)),
    _bar(16),
    _bar(16),
]

# mutant rat, patrolling the twin platforms in the Uranium Workings -
# pointed ears/snout and a trailing tail read as "rodent" even at this
# size; legs and tail swing dramatically between frames (same lesson
# as the bear/chicken: a 1px wobble doesn't read as animated).
RAT_A = [
    _bar(16, (4,6), (10,12)),      # ears
    _bar(16, (4,6), (10,12)),      # ears
    _bar(16, (5,11)),              # head
    _bar(16, (5,11), (12,14)),     # head + snout poking out
    _bar(16, (4,10), (11,15)),     # snout tip
    _bar(16, (5,11)),              # neck
    _bar(16, (3,13)),              # body top
    _bar(16, (2,14)),              # body
    _bar(16, (2,14)),              # body (widest)
    _bar(16, (3,13)),              # body taper
    _bar(16, (3,6), (10,13)),      # legs together (mid-stride)
    _bar(16, (2,5), (11,14)),      # feet
    _bar(16, (0,2), (4,7), (9,12)),# tail base + legs
    _bar(16, (0,3)),               # tail
    _bar(16, (1,4)),               # tail curl
    _bar(16),
]
RAT_B = [
    _bar(16, (4,6), (10,12)),
    _bar(16, (4,6), (10,12)),
    _bar(16, (5,11)),
    _bar(16, (5,11), (12,14)),
    _bar(16, (4,10), (11,15)),
    _bar(16, (5,11)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (2,5), (11,14)),      # legs splayed wide (running stride)
    _bar(16, (1,4), (12,15)),      # feet further out
    _bar(16, (0,3), (4,6), (10,12)),# tail shifted the other way + legs
    _bar(16, (1,4)),               # tail
    _bar(16, (0,3)),               # tail curl (opposite side)
    _bar(16),
]

room3_slabs_def = [
    (3, 2, 3, T_CRUMB),   # crumbling platform series (3 in a row)
    (4, 2, 3, T_CRUMB),   # - the chicken patrols this whole row
    (5, 2, 3, T_CRUMB),
    (6, 1, 1, T_STONE),   # fixed platform for the 3rd key
]

ROOM3 = dict(
    label='3',
    wallcol=dict(lit=11, rock=6, joint=1),
    crest_fn=_wtop_menagerie,
    floor_base=10, floor_speckle=6,
    slabs_def=room3_slabs_def,
    style={
        T_STONE: dict(top_fill=11, top_edge=15, face_l=6, face_r=10, rocky=True),
        T_CRUMB: dict(top_fill=10, top_edge=15, face_l=6, face_r=11, rocky=True),
    },
    keys=[(3,2,4,14), (5,2,4,14), (6,1,2,14)],   # 2 of the 3 sit above the crumbling row
    exit_bx=6, exit_bz=4, exit_y=1,
    hazards=[(2, 3, 8), (5, 4, 8)],   # poison puddles on open floor, away
                                       # from the platforms/keys and (1,4)'s spawn
    hazard_art=PUDDLE_ART,
    crumb_units=[[(3,2,3)], [(4,2,3)], [(5,2,3)]],
    enemy_frames=[CHICKEN_A, CHICKEN_B],
    enxmin=48, enxmax=96, enz=40, ensurf=32, enemy_color=15,
    name="THE MENAGERIE",
    # bank1 overflow ("Negative BLOCK?") from Room18's own data -
    # relocate this room's map too, same routine fix as every recent
    # room.
    map_label='level_map3',
)

# twin fixed platforms (bx=3 and bx=5, leaving bx=4 as an open gap to
# jump across) plus the usual 3rd-key fixed platform. No crumbling in
# this room - the challenge is the gap + the patrolling rat, not decay.
room4_slabs_def = [
    (3, 2, 3, T_STONE),   # twin platform A
    (5, 2, 3, T_STONE),   # twin platform B - bx=4 between them is a gap
    (6, 1, 1, T_STONE),   # fixed platform for the 3rd key
]

ROOM4 = dict(
    label='4',
    wallcol=dict(lit=13, rock=4, joint=1),
    crest_fn=_wtop_uranium,
    floor_base=1, floor_speckle=8,
    floor_style='grid',
    slabs_def=room4_slabs_def,
    style={
        T_STONE: dict(top_fill=13, top_edge=15, face_l=4, face_r=5, rocky=True),
    },
    keys=[(3,2,4,14), (5,2,4,14), (6,1,2,14)],   # 2 on the twin platforms
    exit_bx=6, exit_bz=4, exit_y=1,
    hazards=[(1, 2, 8), (3, 4, 8)],   # uranium bars, verified clear of every
                                       # slab/exit/spawn screen position first
    hazard_art=URANIUM_BAR_ART,
    crumb_units=[],
    enemy_frames=[RAT_A, RAT_B],
    enxmin=48, enxmax=96, enz=40, ensurf=32, enemy_color=13,
    name="ABANDONED URANIUM WORKINGS",
    # bank1 overflow ("Negative BLOCK?") from Room17's ROOMROWLEN
    # growth (54->58) - relocate this room's map too, same routine
    # fix as every recent room.
    map_label='level_map4',
)

# Eugene: a bouncing white ball/skull - monochrome silhouette (the sprite
# engine draws every enemy in one flat room_enemy_color, so his classic
# sunglasses can't be a separate colour; the bounce itself carries the
# character instead). Frame A is round and tall (mid-air), frame B is a
# squashed wide oval sitting lower in the frame (impact/apex of the
# bounce) - a strong silhouette-level shape change, same lesson as the
# bear/chicken/rat: a 1-2px wobble doesn't read as animated at this size.
EUGENE_A = [
    _bar(16, (6,10)),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (1,15)),
    _bar(16, (1,15)),
    _bar(16, (1,15)),
    _bar(16, (1,15)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (6,10)),
    _bar(16),
    _bar(16),
]
EUGENE_B = [
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16, (4,12)),
    _bar(16, (2,14)),
    _bar(16, (0,16)),
    _bar(16, (0,16)),
    _bar(16, (0,16)),
    _bar(16, (0,16)),
    _bar(16, (1,15)),
    _bar(16, (3,13)),
    _bar(16, (5,11)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]

# twin high platforms bridging a chasm (bz=0..2 is entirely a pit - see
# floor_gaps below), plus a low staging platform on the spawn side. The
# exit sits alone on the far side of the chasm: the only way there is
# floor -> low platform -> high A -> high B -> step off B's far edge and
# fall down onto the isolated exit island (jump deltas match Room4's
# already-validated hop1/hop2/hop3 template exactly, just re-aimed).
room5_slabs_def = [
    (6, 3, 1, T_STONE),   # low staging platform, reachable from spawn floor
    (5, 2, 3, T_STONE),   # high platform A - diagonal jump from the low one
    (3, 2, 3, T_STONE),   # high platform B - horizontal jump from A (bx=4 gap)
]

def _wtop_plant(u):
    """mostly-flat industrial rooftop with periodic silo/tank bumps -
    Processing Plant"""
    return 26 + (14 if (int(u) % 20) < 6 else 4)

# pacman: a classic chomping circle, monochrome (same engine constraint
# as Eugene - one flat room_enemy_color per sprite, so like his bounce
# the "personality" has to come from the shape/animation, not a second
# colour). Frame A has a wedge bitten out (mouth open, chomping toward
# the right), frame B is a full circle (mouth closed) - same silhouette-
# level contrast lesson as every other enemy in this project.
PACMAN_A = [
    _bar(16, (5,10)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (1,14)),
    _bar(16, (1,9)),
    _bar(16, (0,7)),
    _bar(16, (0,6)),
    _bar(16, (0,7)),
    _bar(16, (1,9)),
    _bar(16, (1,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (5,10)),
    _bar(16),
    _bar(16),
    _bar(16),
]
PACMAN_B = [
    _bar(16, (5,10)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (1,14)),
    _bar(16, (1,15)),
    _bar(16, (0,15)),
    _bar(16, (0,15)),
    _bar(16, (0,15)),
    _bar(16, (1,15)),
    _bar(16, (1,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (5,10)),
    _bar(16),
    _bar(16),
    _bar(16),
]

# conveyor (T_CONV) run leading to the catwalk - first reuse of this
# mechanic since Room1 - plus the checkerboard "processing plant"
# catwalk (bz=2,y=3) where the twin pacmen patrol, and two simple side
# platforms (3rd key, exit) clear of the pacmen's lane.
room6_slabs_def = [
    (5, 3, 1, T_CONV),    # conveyor belt
    (6, 3, 1, T_STONE),   # conveyor's solid arrival platform
    (1, 2, 3, T_STONE),   # catwalk (checkerboard) - pacman zone, lengthened
                           # on both ends for more room to maneuver
    (2, 2, 3, T_STONE),
    (3, 2, 3, T_STONE),
    (4, 2, 3, T_STONE),
    (5, 2, 3, T_STONE),   # diagonal-jump entry point from the conveyor
    (6, 2, 3, T_STONE),   # safe-refuge cell past the jump entry, clear of
                           # even the pacmen's widest reach
    (2, 5, 1, T_STONE),   # simple side platform, 3rd key
    (4, 5, 1, T_STONE),   # simple side platform, exit
]

ROOM6 = dict(
    label='6',
    wallcol=dict(lit=3, rock=12, joint=1),
    crest_fn=_wtop_plant,
    floor_base=1, floor_speckle=2,
    floor_style='grid',
    slabs_def=room6_slabs_def,
    style={
        T_STONE: dict(top_fill=3, top_edge=12, face_l=12, face_r=1, checker=True),
        T_CONV:  dict(top_fill=4, top_edge=5, face_l=6, face_r=8, arrows=True, rocky=True),
    },
    keys=[(6,3,2,14), (3,2,4,14), (2,5,2,14)],   # conveyor arrival, catwalk
                                                   # center (pacman-guarded),
                                                   # side platform
    exit_bx=4, exit_bz=5, exit_y=1,
    hazards=[],
    hazard_art=None,
    crumb_units=[],
    enemy_frames=[PACMAN_A, PACMAN_B],
    # Verified by exhaustive simulation (every starting phase x every
    # move/wait/retreat strategy - see the session notes), not just
    # playtesting: a range narrow enough to keep BOTH fixed points (key
    # at x=56, real measured landing spot at x=87) always >10px away
    # turned out to be PROVABLY uncrossable - the enemy is on Sam's own
    # walking line, so a narrow excursion just means it's always
    # loitering right where he needs to cross. A wide excursion (48px,
    # matching Room4's rat) is what actually opens real gaps: enxmin=16
    # keeps the key always safe (dx>=16), enxmax=52 keeps the pacman's
    # own reach within the platform's right end (pos2 max=108, inside
    # the bx=6 refuge cell) while giving it enough range to swing well
    # clear of the landing spot for a real crossing window. The
    # left-hand pacman (pos1=centerx-en_x) never actually reaches back
    # into the 56-87 corridor at this enxmin, so it can't interfere
    # with the crossing either.
    enxmin=16, enxmax=52, enz=40, ensurf=32, en_axis=2, en_centerx=56,
    enemy_color=10,
    name="PROCESSING PLANT",
    # bank1 overflow fix (see Room7's own comment) - relocated again.
    map_label='level_map6',
)

def _wtop_vat(u):
    """mostly-flat industrial tank rim, minimal variation - The Vat"""
    return 34 + (6 if (int(u) % 10) < 2 else 0)

def _wtop_forest(u):
    """dense leafy canopy with individual tree crowns poking up through
    it - The Endorian Forest. Deliberately distinct from Kong Beast's
    smoother, rounder vine-mound crest (_wtop_kong): a sharper, more
    frequent base jag (small leaf clusters) plus periodic TALL narrow
    crown spikes (individual treetops breaking through the canopy, one
    every 24px) rather than one continuous rolling silhouette."""
    canopy = 34 + 6*abs(_m.sin(u/4.1)) + 3*abs(_m.sin(u/1.7 + 0.4))
    crown = 18 if (int(u) % 24) < 5 else 0
    return int(canopy + crown)

# spark hazard: a bold 8-pointed star/burst - chunky segments (not thin
# lines) so it survives draw_hazard's 1px dilation pass without
# merging into a blob, same lesson as every other hazard in this
# project. Matches the reference's small yellow spark/star hazards
# scattered across the Vat's floor - white ('F') core against light
# yellow ('Y') rays for real contrast against the room's own tan floor
# (floor_base=10 would otherwise nearly match a plain yellow fill).
def _spark_art():
    return [
        _art_row(16, (7,9,'Y')),
        _art_row(16, (6,10,'Y')),
        _art_row(16, (2,4,'Y'), (6,10,'F'), (12,14,'Y')),
        _art_row(16, (4,6,'Y'), (6,10,'F'), (10,12,'Y')),
        _art_row(16, (5,11,'F')),
        _art_row(16, (4,6,'Y'), (6,10,'F'), (10,12,'Y')),
        _art_row(16, (2,4,'Y'), (6,10,'F'), (12,14,'Y')),
        _art_row(16, (6,10,'Y')),
        _art_row(16, (7,9,'Y')),
    ]
SPARK_ART = _spark_art()

# guardian: a hooded specter patrolling the Vat's floor - same vertical
# humanoid body plan as the bear/chicken/rat, legs together vs wide
# apart for a dramatic (not subtle) run-cycle contrast.
GUARDIAN_A = [
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (5,11)),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (4,12)),
    _bar(16, (5,8), (9,12)),
    _bar(16, (5,8), (9,12)),
    _bar(16, (4,9), (8,13)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]
GUARDIAN_B = [
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (5,11)),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (4,12)),
    _bar(16, (3,6), (10,13)),
    _bar(16, (3,6), (10,13)),
    _bar(16, (2,7), (9,14)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]

# The Vat: a dense checkerboard hazard field (bx=3-6,bz=1-6, hazard on
# every cell where (bx+bz) is even) with clear diagonal safe lanes on
# the odd cells - 2 of the 3 keys sit deep in the field, guarded by a
# specter patrolling the floor along the far exit side, combining
# precision weaving with enemy timing for a genuine difficulty step up.
room7_slabs_def = [
    (2, 2, 1, T_STONE),   # west corridor key platform, easy first key
]
# A strict checkerboard has NO orthogonal path through it at all: every
# safe (odd-parity) cell's 4 orthogonal neighbours are all hazard cells
# by construction, forcing precise diagonal corner-cuts to move between
# them - fine for a turn-based game, not for this engine's continuous
# pixel movement, where a natural straight-line walk toward a key clips
# through the "boxing-in" hazard cell next to it and kills on contact.
# Fixed by carving an explicit 1-cell-wide orthogonal corridor through
# the field (entry -> key2 -> key3 -> the clear bx=7 exit column) and
# only placing hazards on every OTHER field cell - still dense (more
# hazard cells than the original checkerboard, since the corridor is
# narrow), but now with a real, walkable path.
room7_path_cells = {(3,3), (4,3), (4,4), (5,4), (6,4)}
room7_hazard_cells = [(bx, bz) for bz in range(1, 6) for bx in range(3, 7)
                       if (bx, bz) not in room7_path_cells]
room7_hazards = [(bx, bz, 8) for (bx, bz) in room7_hazard_cells]

ROOM7 = dict(
    label='7',
    wallcol=dict(lit=10, rock=6, joint=1),
    crest_fn=_wtop_vat,
    floor_base=10, floor_speckle=1,
    floor_style='grid',
    slabs_def=room7_slabs_def,
    style={
        T_STONE: dict(top_fill=11, top_edge=15, face_l=6, face_r=10, rocky=True),
    },
    keys=[(2,2,2,14), (4,3,1), (5,4,1)],   # west platform, 2 deep in the field -
                                              # default gold KEY_ART, kept
                                              # distinct from the hazards'
                                              # yellow sparks on purpose
    exit_bx=7, exit_bz=5, exit_y=1,
    hazards=room7_hazards,
    hazard_art=SPARK_ART,
    crumb_units=[],
    enemy_frames=[GUARDIAN_A, GUARDIAN_B],
    enxmin=64, enxmax=112, enz=56, ensurf=8, enemy_color=13,
    name="THE VAT",
    # bank1 overflow ("Negative BLOCK?") from Room16's new hopper
    # enemy - relocated this room's map too (arbitrary choice).
    map_label='level_map7',
)

# Kong Beast: a big ape silhouette, broad shoulders and short bent
# legs (distinct body plan from the vertical-humanoid enemies used so
# far) - arms flared wide (frame A, roaring) vs pulled in tight against
# the chest (frame B), same "dramatic not subtle" contrast lesson as
# the bear's swipe animation.
KONG_A = [
    _bar(16, (5,11)),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (1,6), (10,15)),
    _bar(16, (0,5), (11,16)),   # arms flared fully out
    _bar(16, (1,15)),
    _bar(16, (1,15)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (3,7), (9,13)),
    _bar(16, (3,7), (9,13)),
    _bar(16, (2,7), (9,14)),
    _bar(16),
    _bar(16),
    _bar(16),
]
KONG_B = [
    _bar(16, (5,11)),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),           # arms tucked in tight
    _bar(16, (1,15)),
    _bar(16, (1,15)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (4,6), (10,12)),
    _bar(16, (4,6), (10,12)),
    _bar(16, (3,7), (9,13)),
    _bar(16),
    _bar(16),
    _bar(16),
]

# thrown dagger/bone hazard - a chunky diagonal bar (not a thin blade
# outline, which wouldn't survive draw_hazard's dilation pass intact -
# same "chunky, not fine linework" lesson as every other hazard here)
def _dagger_art():
    return [
        _art_row(16, (10,13,'V')),
        _art_row(16, (8,12,'V')),
        _art_row(16, (6,11,'V')),
        _art_row(16, (5,10,'V')),
        _art_row(16, (3,8,'V')),
        _art_row(16, (2,7,'V')),
        _art_row(16, (1,5,'V')),
        _art_row(16),
    ]
DAGGER_ART = _dagger_art()

# thorn bramble hazard - a knotted brown thicket core ('6', rust-brown)
# with sharp red-orange ('8') thorns poking out at several points, not
# just at the top - a spiky, irregular silhouette distinct from every
# other hazard shape in the game (the amoeba's round blob, the
# uranium bar's straight glow, the dagger's single diagonal edge).
def _thorn_art():
    return [
        _art_row(16, (7,9,'8')),
        _art_row(16, (3,5,'8'), (11,13,'8')),
        _art_row(16, (6,10,'6')),
        _art_row(16, (2,4,'8'), (5,11,'6'), (12,14,'8')),
        _art_row(16, (4,12,'6')),
        _art_row(16, (1,3,'8'), (5,11,'6'), (13,15,'8')),
        _art_row(16, (4,12,'6')),
        _art_row(16, (5,11,'6')),
        _art_row(16, (6,10,'6')),
        _art_row(16),
    ]
THORN_ART = _thorn_art()

# lift platform sprite: 2 side-by-side 16x16 halves forming a 32px-wide
# plank, with a couple of thin gap-rows for a wood-grain/grate look -
# drawn as real hardware sprites (not baked into the background) since
# its height changes every frame, same "dynamic sprite for a dynamic
# entity" approach as the enemies/pacmen.
LIFT_LEFT = [('X'*16 if r != 8 else '.'*16) for r in range(16)]
LIFT_RIGHT = LIFT_LEFT
LIFT_FRAMES = [LIFT_LEFT, LIFT_RIGHT]

# Kong Beast: a tall jungle-canopy climb - a rising/falling lift (new
# mechanic, see room_lift_* in src/main.asm) rides a fixed column from
# floor level up to a high summit ringed by 3 single-cell crumbling
# platforms (one key each), patrolled by the beast; a fixed platform
# beside the lift holds the exit so the way out never requires
# re-touching an already-visited crumbling cell. The lift itself also
# drags Sam sideways (the same conveyor push already used in Room1) -
# holding still while riding walks him off its narrow footprint and he
# falls back down, so climbing it demands continuous counter-steering.
room8_slabs_def = [
    (4, 4, 6, T_STONE),   # fixed exit platform, atop, beside the lift
    (3, 3, 6, T_CRUMB),   # 3 single-cell crumbling platforms ringing
    (4, 2, 6, T_CRUMB),   # the lift's summit position, one key each
    (5, 3, 6, T_CRUMB),
]
room8_crumb_units = [[(3, 3, 6)], [(4, 2, 6)], [(5, 3, 6)]]

ROOM8 = dict(
    label='8',
    wallcol=dict(lit=3, rock=12, joint=1),
    crest_fn=_wtop_kong,
    floor_base=1, floor_speckle=2,
    slabs_def=room8_slabs_def,
    style={
        T_STONE: dict(top_fill=3, top_edge=15, face_l=12, face_r=2, rocky=True),
        T_CRUMB: dict(top_fill=11, top_edge=15, face_l=6, face_r=8, rocky=True),
    },
    keys=[(3,3,7,14), (4,2,7,14), (5,3,7,14)],   # one per crumbling platform
    exit_bx=4, exit_bz=4, exit_y=6,
    hazards=[(6,1,8), (6,0,8)],
    hazard_art=DAGGER_ART,
    crumb_units=room8_crumb_units,
    enemy_frames=[KONG_A, KONG_B],
    # enz=40 (bz=2, key2's row) deliberately does NOT match the lift's
    # own row (lift_wz=56, bz=3) - the beast only ever threatens key2,
    # never the lift ride itself. An earlier draft used enz=56 (matching
    # both the lift AND key1/key3), which meant the beast could kill
    # Sam mid-ride (compounding the already-demanding forced-push climb
    # with enemy-dodging) - found via real playtesting (a "why did I
    # die instantly" investigation traced to a genuine kill-zone
    # overlap, not a bug), fixed by separating the two challenges.
    enxmin=40, enxmax=88, enz=40, ensurf=56, enemy_color=13,
    # lift_ymax=72 (16px ABOVE the summit platforms' surf=56), not 56
    # itself - stepping sideways onto a real platform only lands
    # safely if Sam is approaching from AT OR ABOVE its surface (the
    # normal falling-catch logic is tolerant: it lands the instant your
    # height drops to/below the target, however far above you started).
    # Stepping off while BELOW the target's height falls straight
    # through to the real ground far below instead - so with
    # ymax=56 exactly, the only safe instant to disembark onto the
    # platforms/exit was the single moment lift_h hit exactly 56, an
    # unrealistic timing window (found via Fausto's own playtesting -
    # collected all 3 keys through persistence, but could never reach
    # the exit). The extra 16px of headroom turns that instant into a
    # real ~25% wide window each cycle (lift_h from 56 up to 72) where
    # stepping off is always safe.
    lift_wx=72, lift_wz=56, lift_ymin=8, lift_ymax=72,
    name="KONG BEAST",
    # bank1 overflow ("Negative BLOCK?") from Room14's new falling-
    # debris code - relocated this room's map out to its own bank
    # tail too (same fix as Room8/9/10/11/12/13's own, arbitrary choice
    # of which room to pick).
    map_label='level_map8',
)

# urchin ("riccio"): a spiky ball, jagged silhouette on its widest rows
# so it survives as a ball and not a smooth circle - 2 frames pulse
# slightly bigger/smaller for a wobbling, alive look, reusing the
# vertical-patrol mechanic (room_en_axis=1) already proven by Eugene -
# here en_x bounces as height at a FIXED (room_enz, room_ensurf) world
# (x,z), guarding the one chokepoint climb to the top platform.
URCHIN_A = [
    _bar(16, (7,9)),
    _bar(16, (5,11)),
    _bar(16, (3,7), (9,13)),
    _bar(16, (2,14)),
    _bar(16, (1,15)),
    _bar(16, (0,16)),
    _bar(16, (0,16)),
    _bar(16, (1,15)),
    _bar(16, (2,14)),
    _bar(16, (3,7), (9,13)),
    _bar(16, (5,11)),
    _bar(16, (7,9)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]
URCHIN_B = [
    _bar(16),
    _bar(16, (7,9)),
    _bar(16, (5,11)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (1,15)),
    _bar(16, (1,15)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (5,11)),
    _bar(16, (7,9)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]

# amoeba hazard: a small spiky floating ball, decorative/blocking
# danger scattered in open air along the jump paths (matching the
# reference's floating spiky blobs) - chunky segments, not thin
# outlines, so draw_hazard's dilation pass doesn't merge it into a
# solid blob (same lesson as every hazard in this project).
def _amoeba_art():
    # solid filled body every row (never gaps 2+ consecutive rows at
    # the same columns, which would carve a real hole rather than a
    # jagged edge - caught via the rendered preview, not assumed) with
    # just single-row notches (row 3 and row 8) for a spiky silhouette.
    return [
        _art_row(16, (7,9,'2')),
        _art_row(16, (5,11,'2')),
        _art_row(16, (3,13,'2')),
        _art_row(16, (2,6,'2'), (10,14,'2')),
        _art_row(16, (1,15,'2')),
        _art_row(16, (1,15,'2')),
        _art_row(16, (2,6,'2'), (10,14,'2')),
        _art_row(16, (3,13,'2')),
        _art_row(16, (5,11,'2')),
        _art_row(16, (7,9,'2')),
    ]
AMOEBA_ART = _amoeba_art()

# Wacky Amoebatrons - 3rd, FINAL structural approach (Fausto, after
# the 2nd redesign STILL died at the last key: "DISASTRO... resetta
# completamente... rifallo totalmente da capo"). Everything about the
# CLIMB (floor1 -> step -> floor2, all wide/gap-free, straight height-
# only jumps) stayed - that part was never what was reported broken.
# What's gone for good is the idea of guarding a JUMP LANDING with the
# `en_axis=1` fixed-point enemy at all. Across two redesigns this
# session, every attempt at "jump near/onto a spot the enemy also
# threatens" ran into the same wall: the enemy's kill check is a
# 20x20px box (|dx|<10 AND |dz|<10 from a fixed point), and with the
# platforms this room can fit (edges away from the map's bx/bz clamp
# extremes), any gap small enough to actually jump (~17-24px) is also
# too small to keep BOTH the takeoff and landing platform fully clear
# of that box - proven by two rounds of real tests, each fix for one
# platform's edge breaking the other. Making the gap wide enough for a
# clean margin (33px+) made the JUMP ITSELF fail (Sam's height drops
# below the target before he travels far enough). There is no width
# that satisfies both at once with this room's dimensions.
# The actual fix: don't guard a JUMP at all - guard a WALK, the same
# proven, already-fair mechanic as Room3's chicken and Room5's Eugene
# (`en_axis=1` was ALWAYS meant for exactly this: a fixed ambush point
# you walk past and time, not a moving target you fly through). floor2
# (wide, no gap, height constant while walking) has key2 at its west
# end and key3 at its east end, with the urchin's fixed point sitting
# BETWEEN them on that same walkway (same z as the floor, so only
# HEIGHT timing matters, not position) - reaching key3 means walking
# past it, waiting for its bounce to clear Sam's own height, exactly
# like ducking under/past Eugene. The final exit jump (floor2 -> a
# small platform beyond) is a plain, unguarded, already-proven-safe
# straight hop with zero enemy interaction, since by that point all 3
# keys are already in hand and this is just "leave the room", not a
# challenge.
room9_slabs_def = [
    # floor 1 (y=2, surf=24), bz=3 - ONE continuous 5-wide platform,
    # no gap - reached by the same straight jump north from spawn
    # (1,4) already proven to work cleanly every single time tested
    (1,3,2,T_STONE), (2,3,2,T_STONE), (3,3,2,T_STONE),
    (4,3,2,T_STONE), (5,3,2,T_STONE),
    # stepping stone (y=4, surf=40), bz=2 - ALSO 5-wide, matching
    # floor1/floor2's width (a real test caught this: a 2-cell-wide
    # step at the west end only, with 5-wide floors either side, left
    # no landing spot for a straight north jump made from anywhere
    # else along floor1's width)
    (1,2,4,T_STONE), (2,2,4,T_STONE), (3,2,4,T_STONE),
    (4,2,4,T_STONE), (5,2,4,T_STONE),
    # floor 2 (y=5, surf=48), bz=1 - ONE continuous 5-wide platform,
    # no gap - reached from the stepping stone via a straight jump
    # north+up (same proven technique again). This is where the
    # urchin's walk-past ambush lives (see ROOM9 dict below) - key2 at
    # the west end, key3 at the east end, past the enemy.
    (1,1,5,T_STONE), (2,1,5,T_STONE), (3,1,5,T_STONE),
    (4,1,5,T_STONE), (5,1,5,T_STONE),
    # exit platform (y=6, surf=56) - a plain, unguarded straight jump,
    # now from the STEP's own row (bz=2) instead of floor2's far end -
    # a fresh, unused cell (bx=6 was never part of the 5-wide step),
    # only 1 row/16px from floor2 - the shortest, safest hop in the
    # room, with no enemy anywhere near it.
    (6,2,6,T_STONE), (6,1,6,T_STONE),
]

ROOM9 = dict(
    label='9',
    # Fausto: "non voglio piu' vedere la stessa videata" - reskinned
    # from the cool blue/green lab palette used every previous pass to
    # a warm amber/rust one, so this reads as visually distinct at a
    # glance, not just a shuffled version of the same screen.
    wallcol=dict(lit=10, rock=6, joint=1),
    crest_fn=_wtop_amoeba,
    floor_base=6, floor_speckle=8,
    slabs_def=room9_slabs_def,
    style={
        T_STONE: dict(top_fill=10, top_edge=11, face_l=6, face_r=8, rocky=True),
    },
    keys=[(2,3,3,14), (2,1,6,14), (5,1,6,14)],   # floor1, floor2 west,
                                                    # floor2 east (past
                                                    # the urchin) - key3's
                                                    # "y" is 6 (floor2's
                                                    # own y=5, +1 for the
                                                    # pickup-layer offset
                                                    # quirk), NOT 7 - a
                                                    # leftover from the
                                                    # old design where
                                                    # key3 sat on a
                                                    # y=6 platform. Real
                                                    # bug: standing right
                                                    # on floor2 at (5,1)
                                                    # never collected it
                                                    # (wrong map layer).
    exit_bx=6, exit_bz=1, exit_y=6,
    # Fausto (after confirming the redesign WORKS): "facciamo qualche
    # piattaforma che si distrugge al passaggio e disseminiamo quelle
    # fisse di ostacoli" - now that the climb/ambush skeleton is proven
    # solid, add real difficulty on top of it instead of to it: static
    # obstacles ON the two wide climbing floors (NOT floor2, which
    # already carries the urchin ambush - stacking two threats on one
    # platform would be unfair, not fun), placed on a single cell of
    # each 5-wide floor so the rest of the width stays clear to route
    # around (same proven pattern as Room1's (2,4,24) hazard: surf
    # matches the floor's OWN surf, so the kill ceiling sits ABOVE
    # Sam's standing height there - the hazard cell itself is always
    # lethal, adjacent cells on the same floor are untouched).
    # floor1 hazard at (4,3): avoids bx=1-2 (the proven spawn-jump
    # landing zone) and key1 at (2,3).
    # step hazard at (2,2): avoids the step's own width-matching role
    # and sits clear of every key/exit cell.
    # 4th field = explicit floor (see emit_room in this file for why):
    # without it, hazard_check's "anything below the ceiling dies"
    # formula makes the OPEN GROUND directly beneath each hazard cell
    # invisibly lethal too, since the check is column-only and doesn't
    # care which platform (if any) occupies that column - real bug
    # Fausto hit, walking on the ground nowhere near the visible
    # hazard sprite. floor==surf restricts the kill zone to just that
    # platform's own standing height.
    hazards=[(4, 3, 24, 24), (2, 2, 40, 40)],
    hazard_art=AMOEBA_ART,
    # Fausto, once the crumble+hazard addition above was confirmed
    # visible: "fai che tutte le piattaforme siano instabili (tranne
    # quelle che hanno gli ostacoli)... se sampr indugia su una
    # piattaforma la piattaforma deve continuare a distruggersi...
    # sampr non puo' fermarsi su una piattaforma senza che lei si
    # distrugga completamente" - every stone cell on floor1 and the
    # step now crumbles, EXCEPT the 2 cells that already carry a
    # hazard (4,3) and (2,2) - those stay solid landmarks (they're
    # already permanently lethal to stand on, so leaving them fixed
    # keeps them readable as "the thing to route around" rather than
    # doubling as a second, different kind of danger).
    # The exit platform is deliberately left OUT of the crumbling set
    # - it's the terminal "all keys collected, leave the room"
    # platform, not part of the puzzle, and destabilizing it risked an
    # edge-case interplay with the win-trigger.
    # This ALSO switches the degrade model for this room from
    # touch-based (the original mechanic, still used by rooms 1/3/8:
    # only a FRESH touch advances one stage, standing still is free)
    # to dwell-based (`crumb_continuous=1` below): standing on the
    # SAME still-intact cell keeps degrading it every CRUMB_DWELL
    # frames, so Sam can never just plant himself somewhere safe -
    # exactly what was asked ("non puo' fermarsi... senza che lei si
    # distrugga completamente"). Room has a normal solid ground floor
    # everywhere (no floor_gaps), so falling through a fully-crumbled
    # cell just drops Sam to ground level to re-climb - a lost life,
    # never a permanent stuck state.
    # Every cell is its OWN single-cell group (not paired) - a 2-cell
    # group needs 3^2=9 pre-rendered variants vs 3 for a solo cell, and
    # with this many crumbling cells even 2-cell pairs blew a single
    # crumble bank's 8KB budget (26400 bytes needed for all 13 cells
    # paired - measured, not guessed).
    # floor2 (Fausto: "prova a rendere friabili anche le piattaforme
    # piu' in alto... vediamo come va") went over budget even as solo
    # cells once floor1+step were already using most of one 8KB bank,
    # so its 5 cells are routed into a SECOND crumble bank via
    # crumb_unit_banks below (see CRUMBBANK9B in the ROM bank section)
    # instead of trimming scope again - each crumb_tab row now carries
    # its own bank byte (main.asm's degrade_cell switches to whichever
    # bank a cell's OWN row says, not one fixed room-wide bank).
    crumb_units=[
        [(1,3,2)], [(2,3,2)], [(3,3,2)], [(5,3,2)],   # floor1, skip (4,3)
        [(1,2,4)], [(3,2,4)], [(4,2,4)], [(5,2,4)],   # step, skip (2,2)
        [(1,1,5)], [(2,1,5)], [(3,1,5)], [(4,1,5)], [(5,1,5)],  # floor2
    ],
    crumb_unit_banks=['a']*8 + ['b']*5,
    crumb_continuous=1,
    enemy_frames=[URCHIN_A, URCHIN_B],
    # fixed world (x,z) = (64,24): x is floor2's own MIDPOINT (bx=4,
    # between key2 at the west end and key3 at the east end) - you
    # cannot reach key3 without passing this x column. z=24 is floor2's
    # OWN z-center (bz=1's middle) - since Sam WALKS along floor2 at a
    # constant height (never jumping through this point), dz=0 the
    # whole time he's on the platform, so position is never the
    # limiting factor here - ONLY the enemy's current height decides
    # if crossing x=64 is safe, exactly like Eugene/the chicken.
    # enxmin=16,enxmax=64 (48-unit range, matching the width already
    # proven fair in Rooms 4/6/7/8): Sam walks at h+1=49 the whole
    # time; the enemy's 16px hitbox [en_x,en_x+16) clears him (wholly
    # above or below) whenever en_x<=33 OR en_x>=49 - roughly 69% of
    # the cycle is genuinely, unconditionally safe to cross, with a
    # real ~31% danger band (en_x 34-48) to wait out - a fair, visible,
    # learnable "watch it, then dash" pattern, not a coin-flip trap.
    enxmin=16, enxmax=64, enz=64, ensurf=24, en_axis=1, enemy_color=2,
    name="WACKY AMOEBATRONS",
    # bank1 overflow fix (see Room8's own comment above) - same
    # relocation, applied here too since Room14 alone needed more than
    # one room's worth of freed space this time.
    map_label='level_map9',
)

ROOM5 = dict(
    label='5',
    wallcol=dict(lit=11, rock=10, joint=1),
    crest_fn=_wtop_cave,
    floor_base=10, floor_speckle=2,
    floor_gaps=frozenset((bx, bz) for bz in (0, 1, 2) for bx in range(MAPW)),
    slabs_def=room5_slabs_def,
    style={
        T_STONE: dict(top_fill=2, top_edge=3, face_l=4, face_r=5, rocky=True),
    },
    keys=[(6,3,2,14), (5,2,4,14), (3,2,4,14)],   # one per platform
    pickup_art=CUBE_ART, pickup_colors=CUBE_COLORS,
    exit_bx=2, exit_bz=2, exit_y=0,   # isolated island inside the chasm,
                                       # just past high platform B's west
                                       # edge - step off B and fall to it
    hazards=[],
    hazard_art=None,
    crumb_units=[],
    enemy_frames=[EUGENE_A, EUGENE_B],
    enxmin=8, enxmax=44, enz=40, ensurf=40, en_axis=1, enemy_color=15,
    name="EUGENE'S LAIR",
    # bank1 overflow ("Negative BLOCK?") from Room17's ROOMROWLEN
    # growth (54->58) - relocate this room's map too, same routine
    # fix as every recent room.
    map_label='level_map5',
)

# forest wisp: a floating will-o'-the-wisp spirit - a glowing round
# head/orb over a tapering wispy tail, monochrome silhouette (same
# engine constraint as every other enemy - one flat room_enemy_color).
# The tail sways from curling right (frame A) to curling left (frame
# B) - a clear side-to-side drift, not just a 1-2px wobble, matching
# the established "needs a real shape change to read as animated"
# lesson from the bear/chicken/rat.
WISP_A = [
    _bar(16, (7,9)),
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (5,11)),
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (4,12)),
    _bar(16, (4,12)),
    _bar(16, (5,11)),
    _bar(16, (5,10)),
    _bar(16, (6,10)),
    _bar(16, (7,11)),
    _bar(16, (8,12)),
    _bar(16, (9,13)),
    _bar(16, (10,13)),
    _bar(16),
]
WISP_B = [
    _bar(16, (7,9)),
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (5,11)),
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (4,12)),
    _bar(16, (4,12)),
    _bar(16, (5,11)),
    _bar(16, (6,11)),
    _bar(16, (6,10)),
    _bar(16, (5,9)),
    _bar(16, (4,8)),
    _bar(16, (3,7)),
    _bar(16, (3,6)),
    _bar(16),
]

# Fausto: reference image "THE ENDORIAN FOREST" - tree-trunk-bordered
# screens, vine/foliage draped over platform edges, ghostly wandering
# figures. First pass was 3 uniform T_STONE tiers - Fausto: "non voglio
# la stessa impostazione del livello precedente [Room9]... un po' piu'
# vario... come nel livello 1: alcune col rullo, sparse qui e la per
# lo schermo, ostacoli disseminati". Redesign adds a T_CONV (conveyor/
# "rullo") tier and scatters 3 hazards (he specifically liked those)
# across 2 different tiers plus a ground-level one, instead of just 2
# ground-level ones.
# All 3 climbing tiers still share the SAME bx=2-5 (4-wide) footprint
# - this is deliberate, not laziness: Room9's redesign saga proved
# that varying a tier's width relative to the one below/above it
# creates positions where a straight jump misses entirely. "Variety"
# here comes from platform TYPE (stone/conveyor), hazard placement,
# and the enemy - not from gambling on mismatched jump geometry with
# no way to live-test it this session.
room10_slabs_def = [
    (2,3,2,T_STONE), (3,3,2,T_STONE), (4,3,2,T_STONE), (5,3,2,T_STONE),      # tier A
    (2,2,2,T_CONV), (3,2,2,T_CONV), (4,2,2,T_CONV), (5,2,2,T_CONV),          # tier B: the "rullo" - SAME height as A (a sideways scatter, not a climb), drags +x
    # tier C: Fausto circled the middle 2 cells on a screenshot and
    # asked to remove them ("vediamo se diventa piu' difficile") - was
    # a solid 4-wide row matching tier B's width; now just the 2 end
    # cells survive, split by a 2-cell (32px) gap. This makes the
    # climb-up jump from tier B require AIMING at bx=2 or bx=5
    # specifically (bx=3/4 now fall straight through), instead of
    # landing anywhere along the row - real added precision, not just
    # a wider gap. The hazard cell (bx=2) is no longer on the
    # mandatory path either: aiming the climb at bx=5 reaches the key
    # and exit directly, skipping bx=2 and the horizontal gap
    # entirely - bx=2/its hazard become an optional side-visit, not
    # something every run has to cross.
    (2,1,4,T_STONE), (5,1,4,T_STONE),
    (6,1,5,T_STONE),   # exit platform, short hop east from tier C
]

ROOM10 = dict(
    label='10',
    # rock=2 (medium green) is the DOMINANT wall colour (draw_walls
    # uses 'rock' for the whole wall body, 'lit' only for a thin top
    # strip) - a first attempt at this palette accidentally reused
    # rock=6/lit=11, nearly IDENTICAL to Room9's post-reskin amber
    # wallcol (lit=10,rock=6) since 6 is the same reddish-brown either
    # way - caught from the preview render looking like a copy of
    # Room9. This version is green-dominant instead, distinct from
    # both Room9 (red/amber-dominant) and Room8's Kong Beast jungle
    # (lit=3,rock=12 - a lighter, more saturated green pairing).
    wallcol=dict(lit=11, rock=2, joint=1),
    crest_fn=_wtop_forest,
    floor_base=1, floor_speckle=10,
    slabs_def=room10_slabs_def,
    style={
        # Fausto: "le piattaforme falle contornate da vegetazione sui
        # bordi" - top_edge=3 (bright green) rings every platform's
        # border, distinct from the brown wood-plank top_fill.
        T_STONE: dict(top_fill=6, top_edge=3, face_l=12, face_r=8, rocky=True),
        # conveyor: same wood/vine palette as T_STONE, arrows=True
        # draws the classic Manic-Miner-style directional chevrons
        # (always cyan, per draw_slab - not room-colour-dependent) -
        # matches the room's look instead of introducing a clashing
        # new colour just for the mechanic.
        T_CONV: dict(top_fill=6, top_edge=3, face_l=12, face_r=8, arrows=True, rocky=True),
    },
    # one key per tier - y+1 per the pickup-layer quirk (key field =
    # platform y+1). Placed at bx=2 (tier A/B) or bx=5 (tier C),
    # deliberately opposite ends from that tier's own hazard so
    # reaching the key never requires touching the hazard cell too.
    keys=[(2,3,3,14), (2,2,3,14), (5,1,5,14)],
    exit_bx=6, exit_bz=1, exit_y=5,
    # 3 thorn brambles scattered across 2 tiers + the ground (Fausto:
    # "gli ostacoli... mi piacciono molto... disseminati"), not just 2
    # ground-level ones like the first version. Platform-top ones use
    # an explicit floor==surf (see hazard_check's floor/ceiling fix -
    # sampr-miner-project memory - a platform-top hazard without this
    # is ALSO lethal on the open ground far below it, a real bug hit
    # in Room9). tier A's hazard sits at bx=5 (key is at bx=2, so
    # reaching it never requires crossing the hazard cell); tier C's
    # at bx=2 (key at bx=5, same reasoning, mirrored). The conveyor
    # tier (B) deliberately carries NO hazard of its own - the belt +
    # the patrolling wisp already make it a 2-threat tier, matching
    # the established "don't stack 3 threats on one platform" lesson
    # from Room9's redesign saga.
    hazards=[(5, 3, 24, 24), (2, 1, 40, 40), (6, 4, 8)],
    hazard_art=THORN_ART,
    crumb_units=[],
    enemy_frames=[WISP_A, WISP_B],
    # patrol along tier B's own row (bz=2, z-center=40) at tier B's
    # own height (surf=24) - walking the conveyor means simultaneously
    # fighting the belt's drag AND timing the wisp's patrol, real
    # difficulty without stacking a 3rd hazard on the same tier.
    enxmin=32, enxmax=88, enz=40, ensurf=24, enemy_color=7,
    name="THE ENDORIAN FOREST",
    # bank1 overflow again ("Negative BLOCK?") - Room13's 2nd-enemy
    # pointer field grew ROOMROWLEN by 2 bytes x 13 rooms, enough to
    # tip bank1 over again. Same fix, applied to this room this time
    # (arbitrary choice - any one room's relocation covers it):
    # relocate its map out to its own bg_pattern bank tail.
    map_label='level_map10',
)

def _wtop_wires(u):
    """tight, regular coiled-cord loops (a phone cord viewed edge-on) -
    Mutant Telephones. Faster/tighter period than every other room's
    crest for a distinct, "coiled" silhouette rather than a rolling or
    jagged one."""
    return int(30 + 14*abs(_m.sin(u/3.2)))

# mutant telephone: a rotary phone body with a curved handset resting
# on top, tilting side to side between frames - the classic ringing/
# shaking-with-rage wobble, same "needs a real shape change" lesson as
# every other enemy sprite here. Body (rows 3-12) is identical between
# frames; only the handset (rows 0-2) actually moves.
PHONE_A = [
    _bar(16, (3,7)),
    _bar(16, (2,6), (9,13)),
    _bar(16, (8,12)),
    _bar(16, (5,11)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,5), (11,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (4,12)),
    _bar(16),
    _bar(16),
    _bar(16),
]
PHONE_B = [
    _bar(16, (9,13)),
    _bar(16, (3,7), (10,14)),
    _bar(16, (4,8)),
    _bar(16, (5,11)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,5), (11,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (4,12)),
    _bar(16),
    _bar(16),
    _bar(16),
]

# Fausto supplied a reference screenshot - Manic Miner's classic
# "Attack of the Mutant Telephones" (phones as enemies, hanging spark
# hazards, a central conveyor belt) - and asked for "uno schema
# divertente e complesso da superare" (a fun, complex layout).
# Reuses SPARK_ART verbatim (already built for The Vat, and a spark/
# electric motif fits a telephone room just as well) rather than
# inventing a near-duplicate hazard shape.
#
# Went through 2 more-conservative versions first, both rejected by
# Fausto as "too similar to Room10" / "three rows like big stairs" -
# a straight bx=2-5 staircase (even with every tier at its own height,
# fixing the earlier fusion bug) still reads as the same skeleton as
# every previous room. This version actually breaks that shape: 6
# small 2-wide clusters ZIGZAGGING left/right across x while climbing
# in z, with a real 1-cell gap between every horizontally-adjacent
# pair - visually scattered, not a staircase, while every individual
# jump is still one of exactly 3 already-proven types (no new,
# unverified jump geometry, since there's still no way to live-test
# this session):
#   - "climb": same bx range, adjacent bz, +1 level (used everywhere)
#   - "sideways": same bz, 1-cell bx gap, SAME height (Room1's own
#     conveyor-entry jump, just rotated 90 degrees - the engine
#     handles x/z movement symmetrically, so this is the same proven
#     distance in the other axis, not a new one)
#   - "exit hop": same bz, 1-cell bx gap, +1 level (the short hop
#     every room's own exit already uses, just with a 1-cell gap
#     instead of a direct adjacency)
# Entry(bx2-3,bz3,y2) -sideways-> Conveyor(bx5-6,bz3,y2) -climb->
# ClimbRight(bx5-6,bz2,y4) -sideways-> ShiftLeft(bx2-3,bz2,y4)
# -climb-> ClimbFinal(bx2-3,bz1,y6) [phone ambush lives here]
# -exit hop-> Refuge+Exit(bx5-6,bz1,y7).
room11_slabs_def = [
    (2,3,2,T_STONE), (3,3,2,T_STONE),      # Entry
    (5,3,2,T_CONV), (6,3,2,T_CONV),        # Conveyor (gap at bx=4, sideways jump from Entry)
    (5,2,4,T_STONE), (6,2,4,T_STONE),      # ClimbRight (climb from Conveyor)
    (2,2,4,T_STONE), (3,2,4,T_STONE),      # ShiftLeft (gap at bx=4, sideways jump from ClimbRight)
    (2,1,6,T_STONE), (3,1,6,T_STONE),      # ClimbFinal (climb from ShiftLeft) - phone ambush
    (5,1,7,T_STONE), (6,1,7,T_STONE),      # Refuge+Exit (gap at bx=4, exit-hop from ClimbFinal)
]

ROOM11 = dict(
    label='11',
    wallcol=dict(lit=14, rock=13, joint=1),
    crest_fn=_wtop_wires,
    floor_base=1, floor_speckle=5,
    slabs_def=room11_slabs_def,
    style={
        T_STONE: dict(top_fill=5, top_edge=15, face_l=4, face_r=13, rocky=True),
        T_CONV:  dict(top_fill=5, top_edge=15, face_l=4, face_r=13, arrows=True, rocky=True),
    },
    # one key per climbing cluster (not the refuge - a key field
    # there would need y+1=8, out of the map's 0-7 height-layer
    # range) - Entry, ShiftLeft, ClimbFinal, each at their west cell
    # (bx=2). y+1 per the pickup-layer quirk.
    keys=[(2,3,3,14), (2,2,5,14), (2,1,7,14)],
    exit_bx=6, exit_bz=1, exit_y=7,
    # 3 sparks scattered across 3 different clusters (Fausto liked
    # these from Room10) - Entry (bx=3, floor==surf so it's only
    # lethal AT that platform's own height - see the hazard_check
    # floor/ceiling fix), ClimbRight (bx=5), plus a ground-level one
    # far from the spawn column. No hazard on the conveyor (belt
    # drag is already a real threat) or ClimbFinal (already carries
    # the phone ambush) or the refuge/exit (kept simple on purpose).
    hazards=[(3, 3, 24, 24), (5, 2, 40, 40), (6, 4, 8)],
    hazard_art=SPARK_ART,
    crumb_units=[],
    enemy_frames=[PHONE_A, PHONE_B],
    # walk-past ambush on ClimbFinal: fixed point at that cluster's
    # own x-midpoint (bx=2-3 -> worldx 32-64 -> 48) and z-center
    # (bz=1 -> 24). en_x reinterpreted as HEIGHT bouncing enxmin-
    # enxmax (en_axis=1 convention, same as Room9's urchin). Sam
    # walks ClimbFinal at h+1=57 (surf=56+1); the enemy's 16px
    # hitbox [en_x,en_x+16) clears him whenever en_x<=41 OR en_x>=57 -
    # a real, learnable danger band to wait out before crossing from
    # key3 (west) to the exit-hop jump-off (east, bx=3).
    enxmin=16, enxmax=72, enz=48, ensurf=24, en_axis=1, enemy_color=15,
    name="MUTANT TELEPHONES",
    # bank1 overflow again ("Negative BLOCK?") - the new rectangular-
    # patrol code (enemy_update/enemy2_update/sam_draw) added enough
    # bytes to tip it over even without any new per-room data. Same
    # fix, applied here this time (arbitrary choice).
    map_label='level_map11',
)

def _wtop_refinery(u):
    """regular sawtooth pipe/smokestack silhouette (Ore Refinery) -
    narrow tall spikes evenly spaced over a low flat base, industrial
    rather than organic (same "deliberately regular" family as the
    menagerie's cage bars/uranium's pylons, just denser/narrower)."""
    return 26 + (28 if (int(u) % 10) < 2 else 6)

def _wtop_alien(u):
    """sharp, irregular crystalline peaks - an alien rock/crystal
    formation, distinct from every earlier crest (sharper and more
    randomly-spaced than the forest's canopy or the wires' regular
    coil)."""
    return int(32 + 10*abs(_m.sin(u/3.7)) + 8*abs(_m.sin(u/1.3 + 0.6)))

# alien beast: TALL and THIN (unlike Kong Beast's broad/short body
# plan) with two head antennae - a genuinely different silhouette
# from Room8's Kong, not just a recolour. Arms flared wide (frame A)
# vs pulled in (frame B), same dramatic-contrast lesson as every
# other enemy here.
ALIEN_A = [
    _bar(16, (6,8), (9,11)),    # antennae tips
    _bar(16, (6,8), (9,11)),    # antennae
    _bar(16, (6,10)),           # head
    _bar(16, (5,11)),           # head
    _bar(16, (0,4), (12,16)),   # arms flared fully out
    _bar(16, (0,3), (6,10), (13,16)),
    _bar(16, (6,10)),
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (5,11)),
    _bar(16, (6,10)),
    _bar(16, (6,10)),
    _bar(16, (5,7), (9,11)),
    _bar(16, (5,7), (9,11)),
    _bar(16),
    _bar(16),
]
ALIEN_B = [
    _bar(16, (6,8), (9,11)),
    _bar(16, (6,8), (9,11)),
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (4,12)),           # arms tucked in tight
    _bar(16, (5,11)),
    _bar(16, (6,10)),
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (5,11)),
    _bar(16, (6,10)),
    _bar(16, (6,10)),
    _bar(16, (5,7), (9,11)),
    _bar(16, (5,7), (9,11)),
    _bar(16),
    _bar(16),
]

# spore pod hazard - a round toxic pod ('2' dark green) with sharp
# purple ('V') spikes radiating out at odd angles (not a symmetric
# star like the Vat's spark) - a distinct silhouette for the alien
# theme.
def _pod_art():
    return [
        _art_row(16, (7,9,'V')),
        _art_row(16, (3,5,'V'), (10,13,'V')),
        _art_row(16, (6,10,'2')),
        _art_row(16, (1,3,'V'), (5,11,'2'), (13,15,'V')),
        _art_row(16, (4,12,'2')),
        _art_row(16, (2,4,'V'), (4,12,'2'), (12,14,'V')),
        _art_row(16, (5,11,'2')),
        _art_row(16, (6,10,'2')),
        _art_row(16),
    ]
POD_ART = _pod_art()

# lever/switch prop - a bold red handle (contiguous with its white
# base plate, no thin isolated gaps - see the "bear trap" dilation
# lesson) so it reads clearly as a switch, not a hazard.
LEVER_ART = [
    _art_row(16, (9,12,'8')),
    _art_row(16, (8,11,'8')),
    _art_row(16, (7,10,'8'), (3,7,'F')),
    _art_row(16, (6,9,'8'), (3,8,'F')),
    _art_row(16, (3,9,'F')),
    _art_row(16, (3,9,'F')),
]

# Fausto: new room "Alien KONG BEAST", asked for a lever mechanic -
# "al cambio della leva deve sparire la piattaforma che verra' messa
# sopra quella del portale che fa uscire dal livello... bisogna sia
# raccogliere le tre chiavi che girare la leva per poter accedere al
# portale d'uscita coperto da una piattaforma." Layout left to
# fantasy ("metti tu le piattaforme un po' a fantasia") - reuses the
# Room11 zigzag-clusters template (proven, and specifically requested
# generally as the "don't do 3 straight rows" style going forward),
# with a NEW lever mechanic layered in.
# The exit column carries TWO slabs: (6,1,y=6) is the real exit
# surface, (6,1,y=7) is a second, purely-blocking slab directly above
# it. floor_surface scans DOWNWARD from Sam's feet and returns the
# FIRST solid layer it finds - so while the blocker slab's map cell
# is still set, any approach to that column lands on IT (one level
# higher, no exit trigger there); once the lever clears the blocker's
# map cell, the exact same jump/approach now lands one level lower,
# on the real exit slab, matching exit_check's height/position test.
# No new jump geometry needed for this - the blocker is never itself
# a jump target, just an obstacle that happens to occupy the same
# column.
room12_slabs_def = [
    (2,3,2,T_STONE), (3,3,2,T_STONE),      # Entry
    (5,3,2,T_STONE), (6,3,2,T_STONE),      # Lever cluster (gap at bx=4) - switch at bx=5
    (5,2,4,T_STONE), (6,2,4,T_STONE),      # ClimbRight (climb from Lever cluster)
    (2,2,4,T_STONE), (3,2,4,T_STONE),      # ShiftLeft (gap at bx=4, sideways from ClimbRight)
    (2,1,6,T_STONE), (3,1,6,T_STONE),      # ClimbFinal (climb from ShiftLeft) - alien ambush
    (5,1,6,T_STONE),                       # stepping stone (gap at bx=4, sideways from ClimbFinal)
    # NOTE: (6,1,6) is NOT listed here - render_room auto-appends the
    # actual exit slab at (exit_bx,exit_bz,exit_y) as a T_EXIT tile
    # itself; adding it again here would create a duplicate entry at
    # the same cell and break the exit-flash rendering (hit this as a
    # real bug: "cannot unpack non-iterable NoneType" from the flash-
    # rect diff finding zero differing pixels, since the flash-tinted
    # T_EXIT tile got shadowed by this duplicate T_STONE one).
    (6,1,7,T_STONE),                       # Blocking slab, SAME column as the exit cell (6,1,6) - removed by the lever
]

# Fausto: next room "Ore Refinery" - "non mettiamo piattaforme ma solo
# tantissimi ostacoli in modo che sam debba passare senza toccarli per
# raccogliere le tre chiavi e uscire" (no platforms, just a huge number
# of obstacles Sam must weave through without touching to collect the
# 3 keys and exit). First room with NO elevated slabs at all - the
# whole 8x6 floor is solid ground (y=0 everywhere, no floor_gaps), and
# the "level" is entirely about which ground cells are safe to step on.
# Designed as a single winding, hand-verified path of 25 adjacent
# floor cells (spawn -> key1 -> key2 -> key3 -> exit, every step a
# plain +-1 move in bx or bz, no repeats - verified with a standalone
# adjacency/uniqueness check before committing to this layout) with
# EVERY one of the remaining 23 floor cells carrying a molten-ore
# hazard - "tantissimi ostacoli" taken literally, almost half the room.
room13_slabs_def = []

# molten ore chunk - a bold, contiguous orange/red mass with hot-yellow
# highlights, no thin isolated parts (the bear-trap dilation lesson:
# gaps <3px between separate blobs get swallowed into one shape by
# draw_hazard's outline pass - this hazard is drawn as ONE connected
# blob on purpose, not several).
ORE_ART = [
    _art_row(16, (7,9,'Y')),
    _art_row(16, (5,11,'8')),
    _art_row(16, (4,12,'8')),
    _art_row(16, (3,6,'Y'), (6,10,'8'), (10,13,'Y')),
    _art_row(16, (4,12,'8')),
    _art_row(16, (5,11,'8')),
    _art_row(16, (6,10,'8')),
    _art_row(16),
]

# ore cart: a small mining cart patrolling the back wall row (bz=0),
# which is entirely hazarded in this room's layout - the safe path
# never goes there, so the cart is pure ambient danger/flavour, never
# an actual threat, matching Fausto's "solo ostacoli" framing (the
# hazard field itself is the whole challenge, not another enemy to
# dodge on top of it). 2 frames: beacon light + wheel bounce, same
# dramatic-contrast lesson as every other enemy here.
CART_A = [
    _bar(16, (7,9)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (4,12)),
    _bar(16, (2,6), (10,14)),
    _bar(16, (2,6), (10,14)),
    _bar(16, (2,6), (10,14)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]
CART_B = [
    _bar(16, (6,10)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (4,12)),
    _bar(16),
    _bar(16, (2,6), (10,14)),
    _bar(16, (2,6), (10,14)),
    _bar(16, (2,6), (10,14)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]

# The winding safe path (spawn -> key1 -> key2 -> key3 -> exit), kept
# here as an explicit list so the hazard cell list below is derived
# from it (every floor cell NOT on this path), not hand-typed - avoids
# the risk of hand-placing 23 hazards and accidentally overlapping the
# one route through them.
# Fausto: the corner-cut safety fix (below) removed 6 hazard cells and
# made the room "troppo facile" (too easy) - shortened/straightened
# this path (25->21 cells, 6->5 turns) so the same fix leaves MORE
# open floor for hazards (17->22, close to the original 23) instead of
# less: fewer turns means fewer mandatory corner-safety cells, and a
# more direct route leaves more of the 48-cell grid free to hazard.
# Same keys/exit endpoints as before, so nothing else needed to change.
_room13_path = [
    (1,4),(1,3),(1,2),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(7,1),
    (7,2),(7,3),(7,4),(6,4),(5,4),(5,5),(4,5),(3,5),(2,5),(1,5),(0,5),
]
# Fausto played it and reported dying "for no reason" sometimes - real
# bug, root-caused via main.asm's dxtab/dztab: 4 of the 8 stick
# directions (the diagonals) move dx AND dz in the SAME frame, so a
# player can walk in a genuine 45-degree line, not just axis-aligned
# steps. Every turn in a purely-orthogonal path like this one has a
# "corner" cell that a diagonal input cuts straight through - e.g. the
# turn (3,1)->(3,2)->(3,3) then (4,3) has corner cell (4,2), which a
# diagonal nudge reaches directly from (3,2)/(3,3) without ever
# visiting (3,3) first. All 6 turns in this path had exactly this cell
# hazarded, so a player following the intended route with a perfectly
# normal diagonal-ish input could die on what looks like the safe
# path. Fixed generally (not per-turn by hand): compute every turn's
# corner cell and exclude it from hazards, for any future path too.
def _corner_cut_cells(path):
    corners = set()
    for i in range(1, len(path)-1):
        a, b, c = path[i-1], path[i], path[i+1]
        if a[0] == b[0] and b[1] == c[1] and a[1] != b[1] and b[0] != c[0]:
            corners.add((c[0], a[1]))
        elif a[1] == b[1] and b[0] == c[0] and a[0] != b[0] and b[1] != c[1]:
            corners.add((a[0], c[1]))
    return corners
_room13_safe_cells = set(_room13_path) | _corner_cut_cells(_room13_path)
_room13_hazard_cells = [(bx,bz) for bz in range(MAPD) for bx in range(MAPW)
                         if (bx,bz) not in _room13_safe_cells]

ROOM12 = dict(
    label='12',
    wallcol=dict(lit=7, rock=4, joint=1),
    crest_fn=_wtop_alien,
    floor_base=1, floor_speckle=7,
    slabs_def=room12_slabs_def,
    style={
        T_STONE: dict(top_fill=5, top_edge=7, face_l=4, face_r=13, rocky=True),
    },
    # one key per climbing cluster (Entry, ShiftLeft, ClimbFinal),
    # west cell each, y+1 per the pickup-layer quirk.
    keys=[(2,3,3,14), (2,2,5,14), (2,1,7,14)],
    exit_bx=6, exit_bz=1, exit_y=6,
    # spore pods on ClimbRight and the Lever cluster - Fausto liked
    # the scattered hazards from the last 2 rooms, so kept that
    # pattern here too. None on ClimbFinal (already carries the alien
    # ambush) or the exit column (kept simple, plus it already
    # carries the lever-gated blocker).
    hazards=[(6, 3, 24, 24), (5, 2, 40, 40)],
    hazard_art=POD_ART,
    crumb_units=[],
    enemy_frames=[ALIEN_A, ALIEN_B],
    # walk-past ambush on ClimbFinal (bx=2-3,bz=1 -> x-mid 48, z 24) -
    # same en_axis=1 pattern as Room9/11, same enxmin/enxmax as
    # Room11 (identical surf=56 -> h+1=57 at this cluster).
    enxmin=16, enxmax=72, enz=48, ensurf=24, en_axis=1, enemy_color=3,
    # lever: switch at the Lever cluster's WEST cell (bx=5,bz=3) -
    # reached right after Entry, well before the exit is even in
    # sight, so the player has to remember to have pulled it. Removes
    # the blocking slab (6,1,y=7) sitting over the exit surface
    # (6,1,y=6).
    # NOTE: the east cell (bx=6,bz=3) carries the first spore-pod
    # hazard (see hazards above) - real bug hit: the switch was
    # originally placed AT (6,3) too, the same cell as that hazard,
    # making it lethal/impossible to reach. West cell is clear.
    lever_switch=(5,3), lever_switch_surf=24, lever_platform=(6,1,7),
    name="ALIEN KONG BEAST",
    # bank1 ("Negative BLOCK?") was 14 bytes over budget with this
    # room's data added - map_label reroutes room_row's map pointer to
    # a label living in this room's own bg_pattern bank tail instead
    # (see emit_room's map_out param and main.asm's level_map12).
    map_label='level_map12',
)

ROOM13 = dict(
    label='13',
    wallcol=dict(lit=14, rock=6, joint=1),
    crest_fn=_wtop_refinery,
    floor_base=1, floor_speckle=14,
    slabs_def=room13_slabs_def,
    style={},
    # keys sit directly on the floor (y=0), so their tuple's 3rd field
    # is 0+1=1 per the pickup-layer y+1 quirk. h_off tuned low since
    # there's no platform underneath to visually anchor them to -
    # verify/re-tune against build/preview14.png like every past room.
    keys=[(2,1,1,10), (5,1,1,10), (6,4,1,10)],
    exit_bx=0, exit_bz=5, exit_y=0,
    # every floor cell off the safe path gets a hazard - see
    # _room13_hazard_cells above (derived from the path, not hand-typed)
    hazards=[(bx,bz,8) for (bx,bz) in _room13_hazard_cells],
    hazard_art=ORE_ART,
    crumb_units=[],
    enemy_frames=[CART_A, CART_B],
    # Fausto: back to exactly 2 enemies (not 4), but make them actually
    # turn/patrol a circuit instead of just bouncing back and forth on
    # one line ("falli girare e non fargli fare solo avanti indietro").
    # This needed a genuinely new mechanic (en_axis=3, rectangular
    # patrol - see enemy_update's .rect in main.asm): the cart walks
    # all 4 sides of a box instead of oscillating on 1 axis. Kept
    # entirely within the back wall row (bz=0, world z 0-16) - the
    # ONLY row that's fully hazarded with no safe/path cell anywhere
    # in it (every other row has some safe cells the path uses) - so
    # the box is wide (x) but thin (z, 2-14), still a real rectangle
    # (turns all 4 corners) without ever risking a safe-path cell.
    enxmin=8, enxmax=120, enz=2, ensurf=8, en_axis=3, en_centerx=14, enemy_color=5,
    name="ORE REFINERY",
    # bank1 overflow again ("Negative BLOCK?") - this room's 23-entry
    # hazards_tab (4B each) plus its inline level map together pushed
    # it back over budget, same as Room12. Same fix: relocate the
    # 384-byte map out to this room's own bg_pattern bank tail.
    map_label='level_map13',
    # 2nd cart, on its own smaller rectangle in the same back wall row
    # (see the 2nd-enemy-slot mechanic in main.asm - always runs the
    # rectangular patrol now, no axis field needed) - a different size
    # and different color (11, light yellow) so the 2 carts stay
    # visually distinguishable and don't just move in lockstep.
    enemy2_frames=[CART_A, CART_B],
    en2xmin=16, en2xmax=64, en2z=2, en2surf=8, en2_centerx=14, enemy2_color=11,
)

def _wtop_skylab(u):
    """evenly-spaced tall antenna/solar-panel spikes over a low base -
    a space station silhouette (Skylab Landing Bay), same "deliberately
    regular" family as the menagerie/uranium/refinery crests, wider
    spacing and taller spikes than the refinery's dense smokestacks."""
    return 34 + (20 if (int(u) % 14) < 3 else 4)

# falling meteor/debris chunk - a round tumbling blob (2 frames, body
# rotated slightly between them) rather than a walking-cycle silhouette
# like every patrol enemy so far, since it only ever falls straight
# down. Single colour, same rendering technique as CART_A/B.
DEBRIS_A = [
    _bar(16, (6,10)),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (6,10)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]
DEBRIS_B = [
    _bar(16, (5,9)),
    _bar(16, (3,11)),
    _bar(16, (2,12)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16, (5,10)),
    _bar(16, (7,9)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]

# Fausto: "SKYLAB LANDING BAY" - "metti piattaforme su piu' livelli e
# fai cadere dal soffitto a caso dei nemici con una frequenza in grado
# di complicare il completamento del livello" (platforms on multiple
# levels, and randomly drop enemies from the ceiling often enough to
# meaningfully complicate finishing the level). 4 climbing tiers
# (y=2,4,6,7 - one more than any previous room) in the same proven
# zigzag-clusters template (climb/sideways/exit-hop primitives only),
# PLUS a brand new falling-debris mechanic (see debris_update/rnd8 in
# main.asm) instead of a patrol enemy - the debris IS this room's
# danger, so no separate hazards/enemy are needed on top of it.
room14_slabs_def = [
    (1,3,2,T_STONE), (2,3,2,T_STONE),      # Entry
    (5,3,2,T_STONE), (6,3,2,T_STONE),      # ShiftRight (gap bx=3-4, sideways from Entry)
    (5,2,4,T_STONE), (6,2,4,T_STONE),      # ClimbA (climb from ShiftRight)
    (1,2,4,T_STONE), (2,2,4,T_STONE),      # ShiftLeft (gap bx=3-4, sideways from ClimbA)
    (1,1,6,T_STONE), (2,1,6,T_STONE),      # ClimbB (climb from ShiftLeft)
    (5,1,6,T_STONE), (6,1,6,T_STONE),      # ShiftRight2 (gap bx=3-4, sideways from ClimbB)
    (5,0,7,T_STONE), (6,0,7,T_STONE),      # ClimbTop (climb from ShiftRight2, +1 only - matches
                                             # the established "final step can be easier" precedent)
    # exit auto-appended at (3,0,7) by render_room - sideways hop from
    # ClimbTop (gap at bx=4, SAME height y=7, the proven "sideways"
    # jump primitive, not a climb - there's no y=8 to climb to).
]

ROOM14 = dict(
    label='14',
    wallcol=dict(lit=15, rock=4, joint=1),
    crest_fn=_wtop_skylab,
    floor_base=1, floor_speckle=7,
    slabs_def=room14_slabs_def,
    style={
        T_STONE: dict(top_fill=7, top_edge=15, face_l=4, face_r=5, rocky=True),
    },
    # one key per major cluster (Entry, ShiftLeft, ShiftRight2), west
    # cell each, y+1 per the pickup-layer quirk. None on ClimbTop
    # (y=7, would need y+1=8 - out of the map's 0-7 height range).
    keys=[(1,3,3,14), (1,2,5,14), (5,1,7,14)],
    exit_bx=3, exit_bz=0, exit_y=7,
    hazards=[],
    hazard_art=None,
    crumb_units=[],
    # required fields, but this room's real danger is the falling
    # debris below - kept an inert placeholder patrol (zero range,
    # parked off the play area, black so it's not even visible) rather
    # than stacking a 2nd real threat on top of the debris mechanic.
    enemy_frames=[CART_A, CART_B],
    enxmin=0, enxmax=0, enz=0, ensurf=200, en_axis=0, enemy_color=1,
    name="SKYLAB LANDING BAY",
    # falling debris: 6 columns spread across every cluster except the
    # final ClimbTop/exit approach (a deliberate breather near the end,
    # same idea as Room9/10's "don't stack every threat everywhere").
    # hstart=120 is above even ClimbTop's own surf (64), so it visibly
    # falls from above the highest platform down past every tier;
    # hend=8 is ground level. speed=2px/frame (every frame, no "and 1"
    # gate) reads faster/more urgent than the patrol enemies' 0.5px/
    # frame bounce. pause=60 frames between landing and the next spawn.
    debris_frames=[DEBRIS_A, DEBRIS_B],
    debris_hstart=120, debris_hend=8, debris_speed=2, debris_pause=60,
    debris_color=8,
    debris_cols=[(2,3), (6,3), (2,2), (6,2), (2,1), (6,1)],
    # bank1 overflow fix, needed again once Room15 was added - relocate
    # this room's map too (there's spare room in its own bank tail).
    map_label='level_map14',
)

def _wtop_bank(u):
    """evenly-spaced wide classical pillars over a low base - a bank
    facade silhouette, same "deliberately regular" family as the
    menagerie/uranium/refinery/skylab crests, wider and flatter-topped
    than any of them (columns, not spikes/antennae)."""
    return 36 + (16 if (int(u) % 16) < 8 else 4)

# falling banknote - a fluttering rectangle (2 frames: flat/wide vs
# edge-on/narrow, simulating a tumbling flip) rather than a round
# blob like Room14's meteor, since paper flutters, it doesn't tumble
# like a rock. Reuses debris_update/the 2nd falling-object mechanic
# verbatim - only the sprite art and per-room tuning differ.
BANKNOTE_A = [
    _bar(16),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]
BANKNOTE_B = [
    _bar(16),
    _bar(16),
    _bar(16, (6,10)),
    _bar(16, (6,10)),
    _bar(16, (6,10)),
    _bar(16, (6,10)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]

# security alarm light - a bold red beacon on a black stand, static
# hazard art (contiguous, no thin isolated parts - the bear-trap
# dilation lesson).
SECURITY_ART = [
    _art_row(16, (7,9,'8')),
    _art_row(16, (6,10,'8')),
    _art_row(16, (5,7,'F'), (7,9,'8'), (9,11,'F')),
    _art_row(16, (4,12,'8')),
    _art_row(16, (5,11,'8')),
    _art_row(16, (6,10,'F')),
    _art_row(16, (7,9,'1')),
    _art_row(16),
]

# Fausto: "THE BANK" - "fai cadere dall'alto delle banconote, metti
# degli ostacoli e rendi molte piattaforme disgregabili" (drop
# banknotes from above, add obstacles, and make many platforms
# crumbling). All 3 asks reuse already-proven mechanics (Room14's
# falling-object system reskinned as banknotes, the standard static
# hazard system, and the touch-based crumble system) rather than new
# engine work - this room needed zero main.asm changes, only content.
# Same zigzag-clusters skeleton as Room14 (kept for safety - no new
# jump geometry to verify without live testing), but the middle 5
# tiers (everything except Entry and the final approach) all crumble
# now - "molte piattaforme disgregabili" taken literally.
room15_slabs_def = [
    (1,3,2,T_STONE), (2,3,2,T_STONE),      # Entry (fixed - stable landing from spawn)
    (5,3,2,T_STONE), (6,3,2,T_STONE),      # Crumble1 (sideways from Entry, gap bx=3-4)
    (5,2,4,T_STONE), (6,2,4,T_STONE),      # Crumble2 (climb from Crumble1)
    (1,2,4,T_STONE), (2,2,4,T_STONE),      # Crumble3 (sideways from Crumble2, gap bx=3-4)
    (1,1,6,T_STONE), (2,1,6,T_STONE),      # Crumble4 (climb from Crumble3)
    (5,1,6,T_STONE), (6,1,6,T_STONE),      # Crumble5 (sideways from Crumble4, gap bx=3-4)
    (5,0,7,T_STONE), (6,0,7,T_STONE),      # Final tier (fixed, climb from Crumble5, +1 only)
    # exit auto-appended at (3,0,7) - sideways from the final tier.
]

ROOM15 = dict(
    label='15',
    wallcol=dict(lit=11, rock=10, joint=1),
    crest_fn=_wtop_bank,
    floor_base=1, floor_speckle=11,
    slabs_def=room15_slabs_def,
    style={
        T_STONE: dict(top_fill=11, top_edge=15, face_l=10, face_r=6, rocky=True),
    },
    # key1 on the fixed Entry (safe); key2/key3 on crumbling tiers -
    # both reachable on the first pass through, same as every prior
    # room's "grab it as you go" crumble+key interaction.
    keys=[(1,3,3,14), (1,2,5,14), (5,1,7,14)],
    exit_bx=3, exit_bz=0, exit_y=7,
    # 2 security-alarm obstacles on cells that carry no key, spread
    # across an early and a late crumbling tier.
    hazards=[(6,3,24,24), (2,1,56,56)],
    hazard_art=SECURITY_ART,
    # 1 crumbling cell per tier (5 groups total) - "molte piattaforme
    # disgregabili" (many crumbling platforms). Real bug caught before
    # shipping: a first attempt made BOTH cells of every 2-wide tier
    # crumble (2-cell groups, 9 baked variants each vs 3 for a 1-cell
    # group) - measured sizes varied 5040-9072 bytes/group depending on
    # position, and 2 of the 5 groups alone already exceeded a single
    # 8KB bank, before even trying to pack more than one group per
    # bank. Switched to 1 crumbling cell per tier (the OTHER cell of
    # each pair stays solid, so every tier keeps some footing even
    # once its crumbling half is gone) - shrinks each group to ~1/3 the
    # combos and comfortably fits 2-3 groups per bank.
    crumb_units=[
        [(5,3,2)],
        [(5,2,4)],
        [(2,2,4)],
        [(1,1,6)],
        [(6,1,6)],
    ],
    crumb_unit_banks=['a','a','a','b','b'],
    enemy_frames=[CART_A, CART_B],
    # required fields, but this room's dangers are the crumbling floor
    # + falling banknotes + static hazards - same inert placeholder
    # patrol as Room14, parked off the play area.
    enxmin=0, enxmax=0, enz=0, ensurf=200, en_axis=0, enemy_color=1,
    name="THE BANK",
    debris_frames=[BANKNOTE_A, BANKNOTE_B],
    debris_hstart=120, debris_hend=8, debris_speed=2, debris_pause=60,
    debris_color=3,
    # one column per crumbling tier - falling money crashes through
    # the same unstable floor tiles you're trying to cross.
    debris_cols=[(6,3), (5,2), (2,2), (2,1), (6,1)],
    # bank1 overflow ("Negative BLOCK?") from this room's own data
    # (crumb_tab's 5 groups + inline map) - same fix as every recent
    # room, relocate the map to this room's own bank tail.
    map_label='level_map15',
)

# Fausto: "passiamo alla caverna 16 'THE SIXTEENTH CAVERN'... crea una
# stanza con piattaforme 1x1 sparse un po' ovunque e alcune che si
# disintegrano (2 o 3)" - first room where every platform is a single
# isolated cell (every prior room used 2-wide clusters) rather than a
# genuinely new mechanic: the SAME proven jump primitives (climb:
# same bx, adjacent bz, +2y; sideways: same bz, 1-cell bx gap, same
# y) still apply unchanged, since their physics only ever cared about
# the (bx,bz,y) landing cell, never platform width - a 2-wide cluster
# was always just "somewhere safe to land inside," and a 1-cell
# target is exactly the landing point those same jumps already
# proved out. A deliberate callback to Room1's own cave theme
# (crest_fn/floor reused directly) for "the sixteenth cavern".
# 2 of the 8 platforms use T_CRUMB (Room1's own crumbling tile type,
# a distinct top colour) instead of T_STONE - gives players a visual
# cue for which ones will break, on top of the usual touch-crumble
# behaviour.
room16_slabs_def = [
    (1,3,2,T_STONE),   # Entry - climb from spawn's floor
    (3,3,2,T_CRUMB),   # sideways +2 from Entry (gap bx=2) - crumbles
    (3,2,4,T_STONE),   # climb from the crumbling cell
    (1,2,4,T_STONE),   # sideways -2 (gap bx=2)
    (1,1,6,T_CRUMB),   # climb - crumbles
    (3,1,6,T_STONE),   # sideways +2 (gap bx=2)
    (3,0,7,T_STONE),   # climb, +1y only (final tier)
    # exit auto-appended at (5,0,7) - sideways +2 from the final tier (gap bx=4)
]

# random platform-hopping enemy (Fausto, after seeing the room: "un
# nemico che salta da piattaforma a piattaforma a caso" - a frog-like
# hopper, legs tucked vs splayed wide, matching the rise/glide/descend
# animation in hopper_update).
HOP_A = [
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (4,7), (9,12)),
    _bar(16, (3,6), (10,13)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]
HOP_B = [
    _bar(16, (6,10)),
    _bar(16, (5,11)),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (1,5), (11,15)),
    _bar(16, (0,4), (12,16)),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16),
]

ROOM16 = dict(
    label='16',
    wallcol=dict(lit=6, rock=8, joint=1),
    crest_fn=_wtop_cave,
    floor_base=None, floor_speckle=6,
    slabs_def=room16_slabs_def,
    style={
        T_STONE: dict(top_fill=11, top_edge=15, face_l=1, face_r=4, rocky=True),
        T_CRUMB: dict(top_fill=6, top_edge=15, face_l=1, face_r=4, rocky=True),
    },
    # key1 on Entry (fixed); key2/key3 on the 2 stable mid-path cells -
    # none on either crumbling cell, kept simple.
    keys=[(1,3,3,14), (1,2,5,14), (3,1,7,14)],
    exit_bx=5, exit_bz=0, exit_y=7,
    hazards=[],
    hazard_art=None,
    crumb_units=[
        [(3,3,2)],
        [(1,1,6)],
    ],
    crumb_unit_banks=['a','a'],
    # required fields, but this room's only danger is the 1-cell
    # platform precision + the 2 crumbling cells - same inert
    # placeholder patrol as Room14/15.
    enemy_frames=[CART_A, CART_B],
    enxmin=0, enxmax=0, enz=0, ensurf=200, en_axis=0, enemy_color=1,
    name="THE SIXTEENTH CAVERN",
    # Fausto, after seeing the room: "un nemico che salta da
    # piattaforma a piattaforma a caso... rendi l'impresa piu'
    # difficile" - reuses all 7 of the room's own platforms as hop
    # targets (see hopper_update in main.asm: rise/glide/descend, not
    # a straight 3D slide). speed=2 (snappy, matches debris' fall
    # speed), pause=30 (~0.5s between hops - lively, always something
    # moving), bump=20 (arc height above the higher endpoint).
    hopper_frames=[HOP_A, HOP_B],
    hop_speed=2, hop_pause=30, hop_bump=20, hop_color=3,
    hop_cols=[(1,3,2), (3,3,2), (3,2,4), (1,2,4), (1,1,6), (3,1,6), (3,0,7)],
    # bank1 overflow ("Negative BLOCK?") from this room's own data -
    # same fix as every recent room, relocate the map.
    map_label='level_map16',
)

room17_slabs_def = [
    (1,3,2,T_STONE),   # Entry - climb from spawn's floor
    (3,3,2,T_CONV), (4,3,2,T_CONV),   # Roller A - sideways +2 from Entry (gap bx=2); package A rides bx=3->4 then falls
    (4,2,4,T_STONE),   # climb from Roller A's far end
    (2,2,4,T_STONE),   # sideways -2 (gap bx=3)
    (2,1,6,T_STONE),   # climb
    (4,1,6,T_CONV), (5,1,6,T_CONV),   # Roller B - sideways +2 (gap bx=3); package B rides bx=4->5 then falls
    (5,0,7,T_STONE),   # climb, +1y only (final tier)
    # exit auto-appended at (7,0,7) - sideways +2 from the final tier (gap bx=6)
]

# roller-conveyor package - a crate riding a conveyor platform, same
# monochrome-silhouette convention as debris/hopper (single draw
# color from pkg_color, not multi-color art). 2 frames: a full-size
# box, then a 1px-inset "settled" box - purely a cosmetic pulse while
# it slides/falls, the same subtle-variant trick DEBRIS_A/B and
# HOP_A/B already use.
PACKAGE_A = [
    _bar(16),
    _bar(16),
    _bar(16, (3,13)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (2,14)),
    _bar(16, (3,13)),
    _bar(16),
    _bar(16),
]
PACKAGE_B = [
    _bar(16),
    _bar(16),
    _bar(16),
    _bar(16, (4,12)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (3,13)),
    _bar(16, (4,12)),
    _bar(16),
    _bar(16),
]

ROOM17 = dict(
    label='17',
    wallcol=dict(lit=11, rock=10, joint=1),
    crest_fn=_wtop_bank,
    floor_style='grid',
    floor_base=1, floor_speckle=14,
    slabs_def=room17_slabs_def,
    style={
        T_STONE: dict(top_fill=14, top_edge=15, face_l=1, face_r=8, rocky=True),
        T_CONV:  dict(top_fill=11, top_edge=15, face_l=10, face_r=1, arrows=True, rocky=True),
    },
    # y is platform_y+1 (NOT the platform's own y) - a key tile is
    # T_KEY in the physics grid, and floor_surface treats anything
    # >T_CRUMB as non-solid, so writing a key at the platform's own
    # (bx,bz,y) overwrites/replaces its solid tile, turning that exact
    # cell into a walk-through "phantom" platform. Every other room
    # places keys one grid layer above their platform for this reason.
    keys=[(1,3,3,14), (4,2,5,14), (2,1,7,14)],
    exit_bx=7, exit_bz=0, exit_y=7,
    hazards=[],
    hazard_art=None,
    crumb_units=[],
    # required fields, but this room's danger is the 2 roller
    # packages, not a patrolling enemy - same inert placeholder as
    # Room14/15/16.
    enemy_frames=[CART_A, CART_B],
    enxmin=0, enxmax=0, enz=0, ensurf=200, en_axis=0, enemy_color=1,
    name="THE WAREHOUSE",
    # Fausto: "un paio di piattaforme rullanti ognuna con un pacco che
    # va nella direzione del rullo e poi cade di sotto in attesa che
    # ne appaia un altro" - 2 independent roller platforms (T_CONV,
    # reused verbatim from Room10's conveyor - it already drags Sam
    # +x AND already has the arrow art, so a package sliding the same
    # +x direction matches what the platform itself visually implies)
    # each with its own package (pkg_update/pkg2_update in main.asm):
    # slides +x across the platform, falls off the far edge, waits
    # `pkg_pause` frames, repeats - no rnd8 needed, the path is fixed.
    pkg_frames=[PACKAGE_A, PACKAGE_B],
    pkg_speed=2, pkg_pause=40, pkg_color=8,
    pkg_start=(3,3,2), pkg_slide=16, pkg_fend=8,
    pkg2_frames=[PACKAGE_A, PACKAGE_B],
    pkg2_speed=2, pkg2_pause=40, pkg2_color=8,
    pkg2_start=(4,1,6), pkg2_slide=16, pkg2_fend=8,
    # bank1 overflow ("Negative BLOCK?") expected from ROOMROWLEN
    # growing again (54->58) - relocate this room's own map too, same
    # routine fix as every recent room.
    map_label='level_map17',
)

# one big flat platform (7 wide x 4 deep, all y=2 - a single climb up
# from spawn's floor, then fully walkable in every direction with no
# further jumping needed) scattered with static amoeba hazards and
# touch-crumbling cells, callback to Room9's "WACKY AMOEBATRONS".
# Fausto: "una piattaforma grande appoggiata sul pavimento che e'
# disseminata di ostacoli con sampr che deve aggirarsi per raccogliere
# le chiavi senza toccarli, ma alcune piattaforme si sgretolano al suo
# passaggio" - weave between static hazards to reach the keys, while
# some of the cells crumble underfoot as he crosses them.
# Widened once already, per Fausto's follow-up: the original 6x3
# (bx1-6,bz1-3) left a 1-cell gap of open ground floor between the
# platform and BOTH back walls (bx=0 column, bz=0 row) - since that
# ground floor is walkable and untouched by any hazard/crumble/enemy,
# Sam could just walk around the platform's outer edge on the floor
# and still be at the right (bx,bz) column to grab a key from below,
# skipping the whole puzzle. Extended to bx=0-6, bz=0-3 so the
# platform butts directly against both walls with zero gap - there is
# no more floor route around it, only through it.
# Raised again, per Fausto's 2nd follow-up: "alza tutta la piattaforma
# di un livello e mettine una bassa che permetta di salirci, cosi' se
# si frantuma un pezzo della piattaforma sampr cadra' di sotto e dovra'
# tornare sopra la piattaforma" - the whole platform moves from y=2 to
# y=4 (world surf 24->40), so falling through a crumbled cell now
# drops Sam all the way down to the y=0 ground floor (nothing else
# solid in between, no floor_gaps in this room) instead of the
# barely-there 24px drop the old y=2 platform gave - a real, punishing
# fall that forces a full re-climb, not a shrug-and-continue. A single
# jump can't cover the full 32px climb from ground to y=4 in one go
# (established jump-height limit, ~21px max without a stepping stone),
# so (1,3) - the room's existing Entry cell - stays at the LOW y=2
# ("mettine una bassa che permetta di salirci") as a fixed 2-step
# staircase landing, and (1,2) - the very next cell on the climb path
# - was promoted from crumbling to fixed too (T_CRUMB->T_STONE): it's
# now the sole gateway onto the raised platform, so it must never be
# the thing that strands Sam mid-climb.
room18_slabs_def = [
    (0,0,4,T_STONE),
    (1,0,4,T_CRUMB),
    (2,0,4,T_STONE),   # hazard
    (3,0,4,T_STONE),
    (4,0,4,T_STONE),   # hazard
    (5,0,4,T_CRUMB),
    (6,0,4,T_STONE),   # fixed safe corner (NE)
    (0,1,4,T_STONE),   # fixed safe corner (NW, next to entry's column)
    (1,1,4,T_STONE),   # key1
    (2,1,4,T_CRUMB),
    (3,1,4,T_STONE),   # hazard
    (4,1,4,T_CRUMB),
    (5,1,4,T_STONE),   # hazard
    (6,1,4,T_STONE),   # key2
    (0,2,4,T_STONE),
    (1,2,4,T_STONE),   # 2nd staircase step - fixed, sole gateway onto the platform
    (2,2,4,T_STONE),   # hazard
    (3,2,4,T_CRUMB),
    (4,2,4,T_STONE),
    (5,2,4,T_STONE),   # hazard
    (6,2,4,T_CRUMB),
    (0,3,4,T_STONE),   # hazard
    (1,3,2,T_STONE),   # Entry (LOW staircase step) - climb from spawn's floor
    (2,3,4,T_STONE),
    (3,3,4,T_STONE),   # key3
    (4,3,4,T_STONE),   # hazard
    (5,3,4,T_CRUMB),
    (6,3,4,T_STONE),
    # exit auto-appended at (7,1,4) - a plain adjacent walk off the
    # platform's own NE corner, no jump needed
]

ROOM18 = dict(
    label='18',
    wallcol=dict(lit=10, rock=6, joint=1),
    crest_fn=_wtop_amoeba,
    floor_base=6, floor_speckle=8,
    slabs_def=room18_slabs_def,
    style={
        T_STONE: dict(top_fill=10, top_edge=11, face_l=6, face_r=8, rocky=True),
        T_CRUMB: dict(top_fill=13, top_edge=11, face_l=6, face_r=8, rocky=True),
    },
    # y is platform_y+1 (NOT the platform's own y=4) - see Room17's
    # phantom-platform bug: a key tile overwrites the physics grid's
    # solid tile, so it must sit one layer above the platform, never
    # on it.
    keys=[(1,1,5,14), (6,1,5,14), (3,3,5,14)],
    exit_bx=7, exit_bz=1, exit_y=4,
    # 8 static amoeba hazards scattered through the widened platform,
    # none adjacent to the entry/key/exit cells - surf=floor=40
    # (8*(y+1) for the now-raised y=4) restricts the kill zone to just
    # this platform's own standing height, same explicit-floor fix
    # Room9 needed.
    hazards=[(2,0,40,40), (4,0,40,40), (3,1,40,40), (5,1,40,40),
             (2,2,40,40), (5,2,40,40), (0,3,40,40), (4,3,40,40)],
    hazard_art=AMOEBA_ART,
    # 7 single-cell touch-crumble groups (default crumb_continuous=0 -
    # Fausto said "si sgretolano al suo passaggio", a fresh touch
    # advances one stage, same as every room except Room9's dwell
    # variant) - entry/2nd step/keys/hazards stay fixed landmarks,
    # matching the established practice of never crumbling a cell with
    # a special role. Trimmed down from the pre-raise count (14 at
    # y=2): the SAME cells cost noticeably more per crumble variant at
    # y=4 (measured ~820B/cell here vs ~510B/cell at y=2 - the raised
    # position changes the affected screen rectangle), and this room's
    # crumb bank is the ROM's last bank (127) with zero fallback if it
    # overflows - had to cut count to fit, not just to taste.
    crumb_units=[
        [(1,0,4)], [(5,0,4)],
        [(2,1,4)], [(4,1,4)],
        [(3,2,4)], [(6,2,4)],
        [(5,3,4)],
    ],
    crumb_unit_banks=['a']*7,
    # Fausto, after seeing the room: "fai anche girare un nemico sulla
    # piattaforma per rendere piu' difficile il completamento" - the
    # urchin sprite (already reused for the room's theme) now actually
    # patrols instead of sitting inert. The platform is a flat
    # rectangle, not a single row, so a straight-line patrol
    # (en_axis=0/1) would only ever threaten one edge - reused the
    # rectangular-patrol mechanic instead (en_axis=3, proven in Room13:
    # the enemy walks all 4 sides of a box), tracing the exact outer
    # footprint of the (now-widened) platform itself (world x 8..104 =
    # bx 0..6, world z 8..56 = bz 0..3) at the platform's own standing
    # height (ensurf=40, the now-raised y=4) - so it's always somewhere
    # on the perimeter, forcing Sam to time crossings on top of
    # dodging the static hazards and outrunning the crumbling cells,
    # never all three threats trivially separable. Color 5 (light
    # blue) - the amoeba hazards are already green(2), and every
    # existing surface here is tan/magenta/dark-red, so light blue is
    # the one hue with nothing to camouflage against.
    enemy_frames=[URCHIN_A, URCHIN_B],
    enxmin=8, enxmax=104, enz=8, en_centerx=56, ensurf=40, en_axis=3, enemy_color=5,
    name="AMOEBATRONS' REVENGE",
    # bank1 overflow ("Negative BLOCK?") expected from this room's own
    # data (19 slabs + 9 crumb groups + 5 hazards) - relocate the map,
    # same routine fix as every recent room.
    map_label='level_map18',
)

# sun-ray screen divider (Solar Power Generator) - a solid vertical
# segment, repeated in a stack by ray_update/.drawray in main.asm (not
# a single moving sprite like every other mechanic). 2 frames: fully
# solid, then a diagonal 1px "glint" gap sweeping across the row
# range - a shimmer, not a real gap (the collision check never cares
# about this, it's purely decorative).
RAY_A = [_bar(16, (0,16)) for _ in range(16)]
RAY_B = [_bar(16, (0,i), (i+1,16)) for i in range(16)]

room19_slabs_def = [
    (1,3,2,T_STONE),   # Entry - climb from spawn's floor
    (3,3,2,T_STONE),   # sideways +2 from Entry (gap bx=2)
    (3,2,4,T_STONE),   # climb
    (1,2,4,T_STONE),   # sideways -2 (gap bx=2)
    (1,1,6,T_STONE),   # climb
    (3,1,6,T_STONE),   # sideways +2 (gap bx=2)
    (3,0,7,T_STONE),   # climb, +1y only (final tier)
    # exit auto-appended at (5,0,7) - sideways +2 from the final tier (gap bx=4)
]

ROOM19 = dict(
    label='19',
    wallcol=dict(lit=5, rock=4, joint=1),
    crest_fn=_wtop_plant,
    floor_style='grid',
    floor_base=1, floor_speckle=11,
    slabs_def=room19_slabs_def,
    style={
        T_STONE: dict(top_fill=14, top_edge=15, face_l=4, face_r=5, rocky=True),
    },
    # y is platform_y+1, same skeleton/deltas as Room16 (proven jump
    # physics, reused verbatim - a "typical" scattered 1x1 room per
    # Fausto's own wording, the new part is the ray, not the layout).
    keys=[(1,3,3,14), (1,2,5,14), (3,1,7,14)],
    exit_bx=5, exit_bz=0, exit_y=7,
    hazards=[],
    hazard_art=None,
    crumb_units=[],
    # required field, but this room's danger is the sun ray, not a
    # patrolling enemy - same inert placeholder pattern as Rooms
    # 14-18 (safe since the enemy_update enxmin=0 underflow fix).
    enemy_frames=[CART_A, CART_B],
    enxmin=0, enxmax=0, enz=0, ensurf=200, en_axis=0, enemy_color=1,
    name="SOLAR POWER GENERATOR",
    # Fausto: "c'e' un raggio del sole che a caso dividera' lo schermo
    # (come un muro) per qualche secondo impedendo di procedere oltre.
    # il raggio dura un secondo nella posizione e poi la cambia" - a
    # NEW mechanic (ray_update/.drawray in main.asm), and a genuinely
    # different kind of mechanic from everything else in the game: it
    # operates in SCREEN space, not world/room space. A fixed world
    # x or z would project as a DIAGONAL line in this isometric engine
    # (sx=X0+wx-wz depends on both axes), not a vertical wall "dividing
    # the screen" the way Fausto described - so both the ray's drawn
    # position and Sam's collision check use the same sx=PX0-8+wx-wz
    # formula every sprite-placement helper already uses, just
    # compared against a fixed screen column instead of a moving one.
    # 4 candidate columns spread across the room's actual screen-x
    # footprint (computed from this room's own platform positions,
    # not guessed) - picks one at random (rnd8) every `ray_period`
    # frames (60 = ~1s, matching "dura un secondo") and holds it;
    # width=10 gives a real, punishing kill band (not a graze).
    ray_frames=[RAY_A, RAY_B],
    ray_period=60, ray_width=10, ray_color=11,
    ray_cols=[70, 110, 150, 190],
    # bank1 overflow ("Negative BLOCK?") expected from ROOMROWLEN
    # growing again (58->60) - relocate this room's own map too, same
    # routine fix as every recent room.
    map_label='level_map19',
)

R1 = render_room(ROOM1)
R2 = render_room(ROOM2)
R3 = render_room(ROOM3)
R4 = render_room(ROOM4)
R5 = render_room(ROOM5)
R6 = render_room(ROOM6)
R7 = render_room(ROOM7)
R8 = render_room(ROOM8)
R9 = render_room(ROOM9)
R10 = render_room(ROOM10)
R11 = render_room(ROOM11)
R12 = render_room(ROOM12)
R13 = render_room(ROOM13)
R14 = render_room(ROOM14)
R15 = render_room(ROOM15)
R16 = render_room(ROOM16)
R17 = render_room(ROOM17)
R18 = render_room(ROOM18)
R19 = render_room(ROOM19)

# Each room's 2-frame enemy sprite table (64B) rides along in the spare
# tail of its own bg_pattern bank (6144 of 8192 bytes used, ~2KB free)
# instead of the shared bank1/leveldata.asm - bank1 is only 16KB total
# (BANK0R+BANK1R, the one permanently-mapped window) and was pushed over
# budget by Room7's tables. This is provably safe: room_start switches
# BANK2R to the room's own bg_bank *before* load_room's enemy-sprite
# copy runs (src/main.asm room_start/load_room), so the tail of that
# same bank is guaranteed to be mapped in at the exact moment it's read.
# Kept as its OWN file (not appended onto bg_patternN.bin) so the
# enemy_gfx label in main.asm - placed via a separate INCBIN right
# after the pattern's - lands exactly at the enemy data's start, not
# past it (an earlier concatenated-file version got this wrong: the
# label, placed after ONE INCBIN of the combined file, pointed past
# the enemy bytes into the 0xFF padding, rendering every enemy as a
# solid square - all-1-bits read as sprite pattern).
def _write_room_bg(lab, R):
    suffix = '' if lab == '' else lab
    open(os.path.join(ROOT,'src',f'bg_pattern{suffix}.bin'),'wb').write(bytes(R['pattern']))
    open(os.path.join(ROOT,'src',f'bg_color{suffix}.bin'),'wb').write(bytes(R['color']))
    open(os.path.join(ROOT,'src',f'enemy_gfx{suffix}.bin'),'wb').write(bytes(R['enemy_bytes']))
    # lever "after" pixel data (only rooms with a lever_platform have
    # this) rides in the same bg_pattern bank's spare tail, right
    # after enemy_gfx - plenty of room there (pattern+enemy_gfx is
    # only ~6.2KB of the bank's 8KB), and no BANK2R switch is needed
    # to blit it since it's the room's own already-mapped bank.
    if R.get('lever_data'):
        open(os.path.join(ROOT,'src',f'lever_gfx{suffix}.bin'),'wb').write(bytes(R['lever_data']['data']))
        # lever_tab{suffix}.asm: the switch/map/rect fields + a
        # pointer to lever_gfx{suffix} - INCLUDEd (not INCBIN'd, since
        # it references that label) into this SAME room's bg_pattern
        # bank section in main.asm, right next to lever_gfx. Kept out
        # of bank1/leveldata.asm on purpose (see room_row's comment) -
        # only room_state's 2-byte pointer to this table lives there.
        lv = R['lever_data']
        lt = [
            f"lever_tab{suffix}:",
            f"        db {lv['switch_bx']},{lv['switch_bz']},{lv['map_bx']},{lv['map_bz']},{lv['map_y']},{lv['slabidx']}",
            f"        db {lv['c0']},{lv['r0']},{lv['c1']},{lv['r1']}",
            f"        dw lever_gfx{suffix}",
        ]
        open(os.path.join(ROOT,'src',f'lever_tab{suffix}.asm'),'w').write("\n".join(lt)+"\n")
    # 2nd enemy (optional, mirrored-pair only): same "own bank tail +
    # single room_state pointer" trick as lever, since only one room
    # uses this so far and a flat per-room field set would cost every
    # room. Table is dw gfx_ptr + 6 config bytes (xmin,xmax,z,surf,
    # centerx,color) - room_start copies those 6 into fixed RAM fields
    # once per room load (see room_en2xmin etc. in main.asm).
    if R.get('enemy2_bytes'):
        open(os.path.join(ROOT,'src',f'enemy2_gfx{suffix}.bin'),'wb').write(bytes(R['enemy2_bytes']))
        e2t = [
            f"enemy2_tab{suffix}:",
            f"        dw enemy2_gfx{suffix}",
            f"        db {R['en2xmin']},{R['en2xmax']},{R['en2z']},{R['en2surf']},{R['en2_centerx']},{R['enemy2_color']}",
        ]
        open(os.path.join(ROOT,'src',f'enemy2_tab{suffix}.asm'),'w').write("\n".join(e2t)+"\n")
    # falling debris (optional): same own-bank-tail single-pointer
    # trick. Table is dw gfx_ptr + hstart,hend,speed,pause,color,ncols
    # + ncols*2 bytes of (bx,bz) map-cell column choices (converted to
    # world coords at spawn time in main.asm, not baked here).
    if R.get('debris_bytes'):
        open(os.path.join(ROOT,'src',f'debris_gfx{suffix}.bin'),'wb').write(bytes(R['debris_bytes']))
        cols = R['debris_cols']
        dt = [
            f"debris_tab{suffix}:",
            f"        dw debris_gfx{suffix}",
            f"        db {R['debris_hstart']},{R['debris_hend']},{R['debris_speed']},{R['debris_pause']},{R['debris_color']},{len(cols)}",
        ] + [f"        db {bx},{bz}" for (bx,bz) in cols]
        open(os.path.join(ROOT,'src',f'debris_tab{suffix}.asm'),'w').write("\n".join(dt)+"\n")
    # random platform-hopping enemy (optional): same own-bank-tail
    # single-pointer trick. Table is dw gfx_ptr + speed,pause,bump,
    # color,ncols + ncols*3 bytes of (bx,bz,y) platform choices
    # (converted to world coords at hop-start time in main.asm).
    if R.get('hopper_bytes'):
        open(os.path.join(ROOT,'src',f'hop_gfx{suffix}.bin'),'wb').write(bytes(R['hopper_bytes']))
        hcols = R['hop_cols']
        ht = [
            f"hop_tab{suffix}:",
            f"        dw hop_gfx{suffix}",
            f"        db {R['hop_speed']},{R['hop_pause']},{R['hop_bump']},{R['hop_color']},{len(hcols)}",
        ] + [f"        db {bx},{bz},{y}" for (bx,bz,y) in hcols]
        open(os.path.join(ROOT,'src',f'hop_tab{suffix}.asm'),'w').write("\n".join(ht)+"\n")
    # roller-conveyor packages, 2 independent slots (optional): same
    # own-bank-tail single-pointer trick. Table is dw gfx_ptr +
    # speed,pause,color,start_bx,start_bz,start_y,slide_dist,fend - no
    # rnd8/column list needed, the path is fixed (see pkg_update).
    if R.get('pkg_bytes'):
        open(os.path.join(ROOT,'src',f'pkg_gfx{suffix}.bin'),'wb').write(bytes(R['pkg_bytes']))
        pbx, pbz, py = R['pkg_start']
        pt = [
            f"pkg_tab{suffix}:",
            f"        dw pkg_gfx{suffix}",
            f"        db {R['pkg_speed']},{R['pkg_pause']},{R['pkg_color']},{pbx},{pbz},{py},{R['pkg_slide']},{R['pkg_fend']}",
        ]
        open(os.path.join(ROOT,'src',f'pkg_tab{suffix}.asm'),'w').write("\n".join(pt)+"\n")
    if R.get('pkg2_bytes'):
        open(os.path.join(ROOT,'src',f'pkg2_gfx{suffix}.bin'),'wb').write(bytes(R['pkg2_bytes']))
        pbx, pbz, py = R['pkg2_start']
        pt = [
            f"pkg2_tab{suffix}:",
            f"        dw pkg2_gfx{suffix}",
            f"        db {R['pkg2_speed']},{R['pkg2_pause']},{R['pkg2_color']},{pbx},{pbz},{py},{R['pkg2_slide']},{R['pkg2_fend']}",
        ]
        open(os.path.join(ROOT,'src',f'pkg2_tab{suffix}.asm'),'w').write("\n".join(pt)+"\n")
    # sun-ray screen divider (optional): same own-bank-tail
    # single-pointer trick. Table is dw gfx_ptr + period,width,color,
    # ncols + ncols*1 bytes of candidate SCREEN-x columns (not map
    # cells - this mechanic operates entirely in screen space, see
    # ray_update in main.asm).
    if R.get('ray_bytes'):
        open(os.path.join(ROOT,'src',f'ray_gfx{suffix}.bin'),'wb').write(bytes(R['ray_bytes']))
        rcols = R['ray_cols']
        rt = [
            f"ray_tab{suffix}:",
            f"        dw ray_gfx{suffix}",
            f"        db {R['ray_period']},{R['ray_width']},{R['ray_color']},{len(rcols)}",
        ] + [f"        db {x}" for x in rcols]
        open(os.path.join(ROOT,'src',f'ray_tab{suffix}.asm'),'w').write("\n".join(rt)+"\n")

_write_room_bg(R1['label'], R1)
_write_room_bg(R2['label'], R2)
_write_room_bg(R3['label'], R3)
_write_room_bg(R4['label'], R4)
_write_room_bg(R5['label'], R5)
_write_room_bg(R6['label'], R6)
_write_room_bg(R7['label'], R7)
_write_room_bg(R8['label'], R8)
_write_room_bg(R9['label'], R9)
_write_room_bg(R10['label'], R10)
_write_room_bg(R11['label'], R11)
_write_room_bg(R12['label'], R12)
_write_room_bg(R13['label'], R13)
_write_room_bg(R14['label'], R14)
_write_room_bg(R15['label'], R15)
_write_room_bg(R16['label'], R16)
_write_room_bg(R17['label'], R17)
_write_room_bg(R18['label'], R18)
_write_room_bg(R19['label'], R19)

# keys_gfx/exit_gfx (per-room graphics blobs, like enemy_gfx) ride in
# the spare tail of that room's own bg_COLOR bank - same rationale as
# enemy_gfx, just spread across the pattern vs color bank tail so
# neither one bank has to carry the whole per-room graphics load.
# exit_gfx's 2 frames are written as TWO separate files (not one
# concatenated file with a second label) for the exact reason
# documented above for enemy_gfx: a label placed after a single INCBIN
# of concatenated data lands past the data it's meant to point at.
def _write_room_extra_gfx(lab, R):
    suffix = '' if lab == '' else lab
    keys_blob = b''.join(bytes(blk) for blk in R['keys_gfx'])
    open(os.path.join(ROOT,'src',f'keys_gfx{suffix}.bin'),'wb').write(keys_blob)
    open(os.path.join(ROOT,'src',f'exit_gfx{suffix}_0.bin'),'wb').write(bytes(R['exit_gfx'][0]))
    open(os.path.join(ROOT,'src',f'exit_gfx{suffix}_1.bin'),'wb').write(bytes(R['exit_gfx'][1]))

_write_room_extra_gfx(R1['label'], R1)
_write_room_extra_gfx(R2['label'], R2)
_write_room_extra_gfx(R3['label'], R3)
_write_room_extra_gfx(R4['label'], R4)
_write_room_extra_gfx(R5['label'], R5)
_write_room_extra_gfx(R6['label'], R6)
_write_room_extra_gfx(R7['label'], R7)
_write_room_extra_gfx(R8['label'], R8)
_write_room_extra_gfx(R9['label'], R9)
_write_room_extra_gfx(R10['label'], R10)
_write_room_extra_gfx(R11['label'], R11)
_write_room_extra_gfx(R12['label'], R12)
_write_room_extra_gfx(R13['label'], R13)
_write_room_extra_gfx(R14['label'], R14)
_write_room_extra_gfx(R15['label'], R15)
_write_room_extra_gfx(R16['label'], R16)
_write_room_extra_gfx(R17['label'], R17)
_write_room_extra_gfx(R18['label'], R18)
_write_room_extra_gfx(R19['label'], R19)

# lift_gfx.bin: the rising/falling lift platform's sprite art (2
# halves, 64B) - a single fixed design shared by every room with a
# lift (only Room8 has one so far), not per-room data.
open(os.path.join(ROOT,'src','lift_gfx.bin'),'wb').write(bytes(pack_sprite_frames(LIFT_FRAMES)))

# crumb.bin: room 1's crumbling-cell variants, laid out exactly as before
crumb_bin = bytearray(R1['crumb_bin'])
assert len(crumb_bin) <= 8192, len(crumb_bin)
crumb_bin += bytes(8192 - len(crumb_bin))
open(os.path.join(ROOT,'src','crumb.bin'),'wb').write(crumb_bin)

# crumb2.bin: room 2's own crumbling-cell variants (separate bank - the
# pre-rendered half/gone images are baked against room 2's background)
crumb_bin2 = bytearray(R2['crumb_bin'])
assert len(crumb_bin2) <= 8192, len(crumb_bin2)
crumb_bin2 += bytes(8192 - len(crumb_bin2))
open(os.path.join(ROOT,'src','crumb2.bin'),'wb').write(crumb_bin2)

# crumb3.bin: room 3's own crumbling-cell variants (the 3-platform row)
crumb_bin3 = bytearray(R3['crumb_bin'])
assert len(crumb_bin3) <= 8192, len(crumb_bin3)
crumb_bin3 += bytes(8192 - len(crumb_bin3))
open(os.path.join(ROOT,'src','crumb3.bin'),'wb').write(crumb_bin3)

# crumb4.bin: room 8's own crumbling-cell variants (the 3 summit
# platforms ringing the lift)
crumb_bin4 = bytearray(R8['crumb_bin'])
assert len(crumb_bin4) <= 8192, len(crumb_bin4)
crumb_bin4 += bytes(8192 - len(crumb_bin4))
open(os.path.join(ROOT,'src','crumb4.bin'),'wb').write(crumb_bin4)

# crumb9.bin: room 9's own crumbling-cell variants, bank 'a' (floor1 +
# the step)
crumb_bin9 = bytearray(R9['crumb_bins'].get('a', bytearray()))
assert len(crumb_bin9) <= 8192, len(crumb_bin9)
crumb_bin9 += bytes(8192 - len(crumb_bin9))
open(os.path.join(ROOT,'src','crumb9.bin'),'wb').write(crumb_bin9)

# crumb9b.bin: room 9's SECOND crumble bank, bank 'b' (floor2) - added
# once floor1+step+floor2 together (26400 bytes as solo cells) proved
# too big for one 8KB bank; each crumb_tab row now carries its own
# bank byte (see CRUMBBANK9B below and degrade_cell in main.asm)
crumb_bin9b = bytearray(R9['crumb_bins'].get('b', bytearray()))
assert len(crumb_bin9b) <= 8192, len(crumb_bin9b)
crumb_bin9b += bytes(8192 - len(crumb_bin9b))
open(os.path.join(ROOT,'src','crumb9b.bin'),'wb').write(crumb_bin9b)

# crumb15.bin/crumb15b.bin: room 15's 5 crumbling groups split across
# 2 banks (3+2, see crumb_unit_banks in ROOM15) - same reason as
# Room9's split, found again independently: 5 groups' pre-rendered
# variants don't reliably fit one 8KB bank.
crumb_bin15 = bytearray(R15['crumb_bins'].get('a', bytearray()))
assert len(crumb_bin15) <= 8192, len(crumb_bin15)
crumb_bin15 += bytes(8192 - len(crumb_bin15))
open(os.path.join(ROOT,'src','crumb15.bin'),'wb').write(crumb_bin15)

crumb_bin15b = bytearray(R15['crumb_bins'].get('b', bytearray()))
assert len(crumb_bin15b) <= 8192, len(crumb_bin15b)
crumb_bin15b += bytes(8192 - len(crumb_bin15b))
open(os.path.join(ROOT,'src','crumb15b.bin'),'wb').write(crumb_bin15b)

# crumb16.bin: room 16's 2 crumbling cells (both 1-cell groups, cheap
# enough to share one bank - see the Room15 crumb-sizing lesson).
crumb_bin16 = bytearray(R16['crumb_bins'].get('a', bytearray()))
assert len(crumb_bin16) <= 8192, len(crumb_bin16)
crumb_bin16 += bytes(8192 - len(crumb_bin16))
open(os.path.join(ROOT,'src','crumb16.bin'),'wb').write(crumb_bin16)

# crumb18.bin: room 18's 9 touch-crumbling cells (all solo 1-cell
# groups, same cheap-per-cell shape as Room9's floor1+step 8 cells,
# which already fit one 8KB bank - this is only 1 more).
crumb_bin18 = bytearray(R18['crumb_bins'].get('a', bytearray()))
print(f"room18 crumb bin 'a' size: {len(crumb_bin18)}")
assert len(crumb_bin18) <= 8192, len(crumb_bin18)
crumb_bin18 += bytes(8192 - len(crumb_bin18))
open(os.path.join(ROOT,'src','crumb18.bin'),'wb').write(crumb_bin18)

# ------------------------------------------------------------------
# ROM bank numbers (must match the equ's added in src/main.asm)
# ------------------------------------------------------------------
ROOM1_BGBANK, ROOM1_BGCOLBANK = 2, 3
ROOM2_BGBANK, ROOM2_BGCOLBANK = 85, 86
ROOM3_BGBANK, ROOM3_BGCOLBANK = 88, 89
ROOM4_BGBANK, ROOM4_BGCOLBANK = 91, 92
ROOM5_BGBANK, ROOM5_BGCOLBANK = 93, 94
ROOM6_BGBANK, ROOM6_BGCOLBANK = 95, 96
ROOM7_BGBANK, ROOM7_BGCOLBANK = 97, 98
CRUMBBANK4 = 99
ROOM8_BGBANK, ROOM8_BGCOLBANK = 100, 101
ROOM9_BGBANK, ROOM9_BGCOLBANK = 102, 103
ROOM10_BGBANK, ROOM10_BGCOLBANK = 106, 107
ROOM11_BGBANK, ROOM11_BGCOLBANK = 108, 109
ROOM12_BGBANK, ROOM12_BGCOLBANK = 110, 111
ROOM13_BGBANK, ROOM13_BGCOLBANK = 112, 113
ROOM14_BGBANK, ROOM14_BGCOLBANK = 114, 115
ROOM15_BGBANK, ROOM15_BGCOLBANK = 116, 117
ROOM16_BGBANK, ROOM16_BGCOLBANK = 120, 121
ROOM17_BGBANK, ROOM17_BGCOLBANK = 123, 124
ROOM18_BGBANK, ROOM18_BGCOLBANK = 125, 126
# banks 128+ are only available because the ROM was expanded from 1MB
# (128 banks) to 2MB (256 banks) specifically to fit this room - see
# the "ROM IS NOW FULL" memory entry from Room18. Room19 is the first
# room to draw from that expanded space.
ROOM19_BGBANK, ROOM19_BGCOLBANK = 128, 129
CRUMBBANK = 84
CRUMBBANK2 = 87
CRUMBBANK3 = 90
CRUMBBANK9 = 104
CRUMBBANK9B = 105
CRUMBBANK15 = 118
CRUMBBANK15B = 119
CRUMBBANK16 = 122
CRUMBBANK18 = 127
# Rooms 4, 5, 6 and 7 have no crumbling platforms (room_nunits=0, cell_at
# returns "no match" immediately) so their crumb_bank field is never
# actually read - reuse CRUMBBANK as a harmless placeholder instead of
# allocating a whole new (empty) bank for either of them. Room 8 and
# Room 9 DO have crumbling platforms, so each gets its own real bank
# (CRUMBBANK4, CRUMBBANK9). Room 9 additionally has a SECOND crumble
# bank (CRUMBBANK9B, floor2) - each crumb_tab row now carries its own
# bank byte (see emit_crumb_tab's bank_map param and degrade_cell in
# main.asm), so a room's groups can be spread across more than one
# bank once they don't all fit in a single 8KB one.

def emit_room(R, lines, map_out=None):
    lab = R['label']
    flat = []
    for z in range(MAPD):
        for y in range(MAPH):
            flat += R['grid'][z][y]
    # map_out: Room12 pushed leveldata.asm/bank1 14 bytes over its 8KB
    # budget ("Negative BLOCK?") - rather than hunt for scraps to trim,
    # this moves the 384-byte map (the single biggest per-room table)
    # out to a standalone .bin, INCBIN'd into that room's OWN bg_pattern
    # bank tail instead (same precedent as enemy_gfx/keys_gfx/exit_gfx/
    # lever_gfx - room_map_ptr is read via LDIRVM in load_room with no
    # bank switch in between, so it just needs to live in the SAME
    # already-mapped page-2 window as those). Frees far more than 14
    # bytes, leaving real headroom for future rooms too.
    if map_out is not None:
        open(map_out, 'wb').write(bytes(flat))
    else:
        lines.append(f"level{lab or 1}_map:")
        lines.append(db(flat, MAPW))
        lines.append("")
    lines.append(f"keys_tab{lab}:")
    for bx,bz,y,c0,r0 in R['key_rects']:
        lines.append(f"        db {bx},{bz},{y},{c0},{r0}")
    lines.append("")
    lines.append(f"slab_tab{lab}:")
    lines.extend(R['slab_lines'])
    lines.append("")
    # keys_gfx/exit_gfx are NOT emitted here - both are pure per-room
    # graphics blobs (like enemy_gfx) that ride in the spare tail of
    # that room's own bg_COLOR bank instead (see _write_room_extra_gfx),
    # keeping them out of the tight, shared bank1/leveldata.asm window.
    # 4 bytes/hazard now: bx,bz,floor,ceiling - lethal only when
    # sam_h+1 is in [floor,ceiling), not "anything below ceiling".
    # Ground-level hazards (surf=8, the vast majority) keep floor=0 -
    # unchanged behaviour, nothing walkable exists below y=0 anyway.
    # Platform-TOP hazards (Room9's) pass an explicit floor==surf so
    # the invisible kill-zone doesn't extend all the way down through
    # the open ground below that same (bx,bz) column (real bug hit:
    # Fausto died walking on the ground under a hazard-marked platform
    # cell, nowhere near the hazard's own visible sprite).
    lines.append(f"hazards_tab{lab}:")
    for h in R['hazards']:
        bx, bz, surf = h[0], h[1], h[2]
        floor = h[3] if len(h) > 3 else 0
        lines.append(f"        db {bx},{bz},{floor},{surf+10}")
    lines.append("")

lines = ["; AUTOGENERATED by tools/gen_iso.py", ""]
lines.append(f"MAPW equ {MAPW}")
lines.append(f"MAPH equ {MAPH}")
lines.append(f"MAPD equ {MAPD}")
lines.append("")
def emit_crumb_tab(R, lines, bank_map=None):
    lab = R['label']
    lines.append(f"; crumb_tab{lab} (18B): ncells, (bx,y,bz)x2 FF-pad, c0,r0,c1,r1,")
    lines.append(";   dw rectsize, dw dataaddr(8000h-based), per-cell slab idx x2, bank")
    lines.append(f"crumb_tab{lab}:")
    for (c0, r0, w, hgt, rectsize, base_off, cells, idxs, bank_label) in R['crumb_meta']:
        row = [len(cells)]
        for (bx, bz, y) in cells:
            row += [bx, y, bz]
        while len(row) < 7:
            row.append(255)
        row += [c0, r0, c0+w, r0+hgt]
        lines.append("        db " + ",".join(str(v) for v in row))
        lines.append(f"        dw {rectsize}, {0x8000+base_off}")
        lines.append("        db " + ",".join(str(v) for v in idxs[:2]))
        lines.append(f"        db {(bank_map or {}).get(bank_label, 0)}")
    lines.append("")

emit_room(R1, lines)
emit_crumb_tab(R1, lines, bank_map={'a': CRUMBBANK})
emit_room(R2, lines, map_out=os.path.join(ROOT,'src','level_map2.bin'))
emit_crumb_tab(R2, lines, bank_map={'a': CRUMBBANK2})
emit_room(R3, lines, map_out=os.path.join(ROOT,'src','level_map3.bin'))
emit_crumb_tab(R3, lines, bank_map={'a': CRUMBBANK3})
emit_room(R4, lines, map_out=os.path.join(ROOT,'src','level_map4.bin'))
emit_crumb_tab(R4, lines, bank_map={'a': CRUMBBANK})
emit_room(R5, lines, map_out=os.path.join(ROOT,'src','level_map5.bin'))
emit_crumb_tab(R5, lines, bank_map={'a': CRUMBBANK})
emit_room(R6, lines, map_out=os.path.join(ROOT,'src','level_map6.bin'))
emit_crumb_tab(R6, lines, bank_map={'a': CRUMBBANK})
emit_room(R7, lines, map_out=os.path.join(ROOT,'src','level_map7.bin'))
emit_crumb_tab(R7, lines, bank_map={'a': CRUMBBANK})
emit_room(R8, lines, map_out=os.path.join(ROOT,'src','level_map8.bin'))
emit_crumb_tab(R8, lines, bank_map={'a': CRUMBBANK4})
emit_room(R9, lines, map_out=os.path.join(ROOT,'src','level_map9.bin'))
emit_crumb_tab(R9, lines, bank_map={'a': CRUMBBANK9, 'b': CRUMBBANK9B})
emit_room(R10, lines, map_out=os.path.join(ROOT,'src','level_map10.bin'))
emit_crumb_tab(R10, lines, bank_map={'a': CRUMBBANK})
emit_room(R11, lines, map_out=os.path.join(ROOT,'src','level_map11.bin'))
emit_crumb_tab(R11, lines, bank_map={'a': CRUMBBANK})
emit_room(R12, lines, map_out=os.path.join(ROOT,'src','level_map12.bin'))
emit_crumb_tab(R12, lines, bank_map={'a': CRUMBBANK})
emit_room(R13, lines, map_out=os.path.join(ROOT,'src','level_map13.bin'))
emit_crumb_tab(R13, lines, bank_map={'a': CRUMBBANK})
emit_room(R14, lines, map_out=os.path.join(ROOT,'src','level_map14.bin'))
emit_crumb_tab(R14, lines, bank_map={'a': CRUMBBANK})
emit_room(R15, lines, map_out=os.path.join(ROOT,'src','level_map15.bin'))
emit_crumb_tab(R15, lines, bank_map={'a': CRUMBBANK15, 'b': CRUMBBANK15B})
emit_room(R16, lines, map_out=os.path.join(ROOT,'src','level_map16.bin'))
emit_crumb_tab(R16, lines, bank_map={'a': CRUMBBANK16})
emit_room(R17, lines, map_out=os.path.join(ROOT,'src','level_map17.bin'))
emit_crumb_tab(R17, lines, bank_map={'a': CRUMBBANK})
emit_room(R18, lines, map_out=os.path.join(ROOT,'src','level_map18.bin'))
emit_crumb_tab(R18, lines, bank_map={'a': CRUMBBANK18})
emit_room(R19, lines, map_out=os.path.join(ROOT,'src','level_map19.bin'))
emit_crumb_tab(R19, lines, bank_map={'a': CRUMBBANK})

lines.append("; redefined font, 76 chars from '0' (8 bytes each)")
_f = open(os.path.join(ROOT,'tools','fonts.c')).read()
_fontbytes = [int(t,16) for t in re.findall(r'0x([0-9A-Fa-f]{2})', _f)]
assert len(_fontbytes) == 608, len(_fontbytes)
lines.append("fonts_tab:")
lines.append(db(_fontbytes, 16))
lines.append("")

# enemy_gfx/bear_gfx/chicken_gfx/rat_gfx/eugene_gfx/pacman_gfx/guardian_gfx
# are NOT emitted here - each room's 64-byte enemy sprite table now rides
# in the spare tail of that room's own bg_pattern bank (see
# _bg_pattern_bytes above), with the matching label defined in main.asm
# right after that room's INCBIN. Keeps them out of the tight, shared
# bank1/leveldata.asm window.

_c = open(os.path.join(ROOT,'tools','sam_sprites.c')).read()
sprites = [int(t,16) for t in re.findall(r'0x([0-9A-Fa-f]{2})', _c)]
assert len(sprites) == 12*128, len(sprites)

# draw_string-ready encoding: fonts_tab only covers ASCII 48-123
# ('0'-relative, see title_putc in main.asm), so punctuation below '0'
# has no glyph there and must map to one of draw_string's custom byte
# codes instead (1=dot, 2=apostrophe) rather than its raw ASCII value.
def _ds_encode(name):
    codes = {'.': 1, "'": 2}
    return ",".join(str(codes.get(c, ord(c))) for c in name)

lines.append("; room name strings for the intro card, draw_string-ready")
lines.append("room1_name:")
lines.append("        db " + _ds_encode(R1['name']) + ",0")
lines.append("room2_name:")
lines.append("        db " + _ds_encode(R2['name']) + ",0")
lines.append("room3_name:")
lines.append("        db " + _ds_encode(R3['name']) + ",0")
lines.append("room4_name:")
lines.append("        db " + _ds_encode(R4['name']) + ",0")
lines.append("room5_name:")
lines.append("        db " + _ds_encode(R5['name']) + ",0")
lines.append("room6_name:")
lines.append("        db " + _ds_encode(R6['name']) + ",0")
lines.append("room7_name:")
lines.append("        db " + _ds_encode(R7['name']) + ",0")
lines.append("room8_name:")
lines.append("        db " + _ds_encode(R8['name']) + ",0")
lines.append("room9_name:")
lines.append("        db " + _ds_encode(R9['name']) + ",0")
lines.append("room10_name:")
lines.append("        db " + _ds_encode(R10['name']) + ",0")
lines.append("room11_name:")
lines.append("        db " + _ds_encode(R11['name']) + ",0")
lines.append("room12_name:")
lines.append("        db " + _ds_encode(R12['name']) + ",0")
lines.append("room13_name:")
lines.append("        db " + _ds_encode(R13['name']) + ",0")
lines.append("room14_name:")
lines.append("        db " + _ds_encode(R14['name']) + ",0")
lines.append("room15_name:")
lines.append("        db " + _ds_encode(R15['name']) + ",0")
lines.append("room16_name:")
lines.append("        db " + _ds_encode(R16['name']) + ",0")
lines.append("room17_name:")
lines.append("        db " + _ds_encode(R17['name']) + ",0")
lines.append("room18_name:")
lines.append("        db " + _ds_encode(R18['name']) + ",0")
lines.append("room19_name:")
lines.append("        db " + _ds_encode(R19['name']) + ",0")
lines.append("")

ENEMY_GFX_LABEL = {'': 'enemy_gfx', '2': 'bear_gfx', '3': 'chicken_gfx', '4': 'rat_gfx', '5': 'eugene_gfx', '6': 'pacman_gfx', '7': 'guardian_gfx', '8': 'kong_gfx', '9': 'urchin_gfx', '10': 'wisp_gfx', '11': 'phone_gfx', '12': 'alien_gfx', '13': 'cart_gfx', '14': 'cart_gfx14', '15': 'cart_gfx15', '16': 'cart_gfx16', '17': 'cart_gfx17', '18': 'urchin_gfx18', '19': 'cart_gfx19'}
ROOM_NAME_LABEL = {'': 'room1_name', '2': 'room2_name', '3': 'room3_name', '4': 'room4_name', '5': 'room5_name', '6': 'room6_name', '7': 'room7_name', '8': 'room8_name', '9': 'room9_name', '10': 'room10_name', '11': 'room11_name', '12': 'room12_name', '13': 'room13_name', '14': 'room14_name', '15': 'room15_name', '16': 'room16_name', '17': 'room17_name', '18': 'room18_name', '19': 'room19_name'}

def room_row(R, bgbank, bgcolbank, crumbbank):
    exb16 = R['exit_bx']*16
    ezb16 = R['exit_bz']*16
    # lever: a SINGLE pointer field (0 = no lever in this room), not
    # the 10+ discrete fields inline in every room's own row - the
    # first version did that and blew bank1's 8KB budget by 132 bytes
    # ("Negative BLOCK?"), since 10+ bytes x 12 rooms in the FIXED,
    # uniform-stride room_tab adds up fast even for the 11 rooms that
    # will never use it. The actual lever table (switch/map/rect/
    # data_ptr) instead lives in lever_tab{label}, emitted into the
    # room's OWN bg_pattern bank spare tail (see main.asm) - a single
    # room_state field stays cheap no matter how many future rooms
    # add their own lever.
    lever = R.get('lever_data')
    lever_fields = [f"lever_tab{R['label']}" if lever else 0]
    # 2nd enemy (optional, mirrored-pair only): same single-pointer-
    # into-the-room's-own-bank-tail trick as lever, for the same reason
    # (only Room13 uses this so far - a flat per-room field set would
    # cost every other room too).
    enemy2_fields = [f"enemy2_tab{R['label']}" if R.get('enemy2_bytes') else 0]
    # falling debris (optional): same single-pointer-into-own-bank-tail
    # trick, for the same reason (only Room14 uses this so far).
    debris_fields = [f"debris_tab{R['label']}" if R.get('debris_bytes') else 0]
    # random platform-hopping enemy (optional): same single-pointer
    # trick, for the same reason (only Room16 uses this so far).
    hopper_fields = [f"hop_tab{R['label']}" if R.get('hopper_bytes') else 0]
    # roller-conveyor packages, 2 independent slots (optional): same
    # single-pointer trick, for the same reason (only Room17 uses
    # this so far).
    pkg_fields = [f"pkg_tab{R['label']}" if R.get('pkg_bytes') else 0]
    pkg2_fields = [f"pkg2_tab{R['label']}" if R.get('pkg2_bytes') else 0]
    # sun-ray screen divider (optional): same single-pointer trick,
    # for the same reason (only Room19 uses this so far).
    ray_fields = [f"ray_tab{R['label']}" if R.get('ray_bytes') else 0]
    return [
        bgbank, bgcolbank,
        R.get('map_label') or f"level{R['label'] or 1}_map", f"keys_tab{R['label']}", len(R['keys']),
        f"keys_gfx{R['label']}",
        f"slab_tab{R['label']}", len(R['slabs_sorted']), len(R['crumb_meta']),
        f"crumb_tab{R['label']}", crumbbank,
        f"hazards_tab{R['label']}", len(R['hazards']),
        exb16, ezb16, 8*(R['exit_y']+1),
        R['EXC0'], R['EXR0'], R['EXNROW'], R['EXW']*8,
        f"exit_gfx{R['label']}_0", f"exit_gfx{R['label']}_1",
        ENEMY_GFX_LABEL[R['label']], R['enemy_color'],
        R['enxmin'], R['enxmax'], R['enz'], R['ensurf'], R.get('en_axis', 0),
        R.get('en_centerx', 0),
        R.get('lift_wx', 0xFF), R.get('lift_wz', 0),
        R.get('lift_ymin', 0), R.get('lift_ymax', 0),
        ROOM_NAME_LABEL[R['label']],
        R.get('crumb_continuous', 0),
    ] + lever_fields + enemy2_fields + debris_fields + hopper_fields + pkg_fields + pkg2_fields + ray_fields

lines.append("; room_tab: one row per room, read into room_state RAM struct")
lines.append("; via a single ldir at room_start. Field order/sizes MUST match")
lines.append("; the room_state RESB block in src/main.asm exactly.")
lines.append("ROOMROWLEN equ 60")
lines.append("room_tab:")
for R, bgbank, bgcolbank, crumbbank in (
        (R1, ROOM1_BGBANK, ROOM1_BGCOLBANK, CRUMBBANK),
        (R2, ROOM2_BGBANK, ROOM2_BGCOLBANK, CRUMBBANK2),
        (R3, ROOM3_BGBANK, ROOM3_BGCOLBANK, CRUMBBANK3),
        (R4, ROOM4_BGBANK, ROOM4_BGCOLBANK, CRUMBBANK),
        (R5, ROOM5_BGBANK, ROOM5_BGCOLBANK, CRUMBBANK),
        (R6, ROOM6_BGBANK, ROOM6_BGCOLBANK, CRUMBBANK),
        (R7, ROOM7_BGBANK, ROOM7_BGCOLBANK, CRUMBBANK),
        (R8, ROOM8_BGBANK, ROOM8_BGCOLBANK, CRUMBBANK4),
        (R9, ROOM9_BGBANK, ROOM9_BGCOLBANK, CRUMBBANK9),
        (R10, ROOM10_BGBANK, ROOM10_BGCOLBANK, CRUMBBANK),
        (R11, ROOM11_BGBANK, ROOM11_BGCOLBANK, CRUMBBANK),
        (R12, ROOM12_BGBANK, ROOM12_BGCOLBANK, CRUMBBANK),
        (R13, ROOM13_BGBANK, ROOM13_BGCOLBANK, CRUMBBANK),
        (R14, ROOM14_BGBANK, ROOM14_BGCOLBANK, CRUMBBANK),
        (R15, ROOM15_BGBANK, ROOM15_BGCOLBANK, CRUMBBANK15),
        (R16, ROOM16_BGBANK, ROOM16_BGCOLBANK, CRUMBBANK16),
        (R17, ROOM17_BGBANK, ROOM17_BGCOLBANK, CRUMBBANK),
        (R18, ROOM18_BGBANK, ROOM18_BGCOLBANK, CRUMBBANK18),
        (R19, ROOM19_BGBANK, ROOM19_BGCOLBANK, CRUMBBANK)):
    f = room_row(R, bgbank, bgcolbank, crumbbank)
    lines.append(f"        db {f[0]},{f[1]}")
    lines.append(f"        dw {f[2]}")
    lines.append(f"        dw {f[3]}")
    lines.append(f"        db {f[4]}")
    lines.append(f"        dw {f[5]}")
    lines.append(f"        dw {f[6]}")
    lines.append(f"        db {f[7]}")
    lines.append(f"        db {f[8]}")
    lines.append(f"        dw {f[9]}")
    lines.append(f"        db {f[10]}")
    lines.append(f"        dw {f[11]}")
    lines.append(f"        db {f[12]}")
    lines.append(f"        db {f[13]},{f[14]},{f[15]}")
    lines.append(f"        db {f[16]},{f[17]},{f[18]},{f[19]}")
    lines.append(f"        dw {f[20]}")
    lines.append(f"        dw {f[21]}")
    lines.append(f"        dw {f[22]}")
    lines.append(f"        db {f[23]}")
    lines.append(f"        db {f[24]},{f[25]},{f[26]},{f[27]},{f[28]},{f[29]}")
    lines.append(f"        db {f[30]},{f[31]},{f[32]},{f[33]}")
    lines.append(f"        dw {f[34]}")
    lines.append(f"        db {f[35]}")
    lines.append(f"        dw {f[36]}")
    lines.append(f"        dw {f[37]}")
    lines.append(f"        dw {f[38]}")
    lines.append(f"        dw {f[39]}")
    lines.append(f"        dw {f[40]}")
    lines.append(f"        dw {f[41]}")
    lines.append(f"        dw {f[42]}")
lines.append("")

# gfx_sprites lives in bank0's own spare space (INCBIN'd directly in
# main.asm), NOT in leveldata.asm/bank1 - bank1 is only 8KB and is
# already tight with 6 rooms' worth of small per-room tables (adding
# Room6 pushed it ~576 bytes over budget, caught as a silent "Negative
# BLOCK?" assembler warning that corrupted addressing for every bank
# after it - see the sampr-miner-project memory for the full story).
open(os.path.join(ROOT,'src','sam_sprites.bin'),'wb').write(bytes(sprites))
open(os.path.join(ROOT,'src','leveldata.asm'),'w').write("\n".join(lines)+"\n")

# ------------------------------------------------------------------
# Preview PNGs
# ------------------------------------------------------------------
def save_preview(R, path, spawn_wx=24, spawn_wz=72, spawn_h=8):
    prev = Image.new('RGB', (W,H))
    for y in range(H):
        for x in range(W):
            prev.putpixel((x,y), PAL[R['base_img'][y][x]])
    sx = X0 + spawn_wx - spawn_wz - 8
    sy = Y0 + (spawn_wx+spawn_wz)//2 - spawn_h - 16
    base = 0
    for l, col in enumerate((14, 9, 4, 15)):
        off = base + l*32
        for yy in range(16):
            bits = (sprites[off+yy] << 8) | sprites[off+16+yy]
            for xx in range(16):
                if bits & (0x8000 >> xx):
                    prev.putpixel((sx+xx, sy+yy), PAL[col])
    prev.resize((512,384), Image.NEAREST).save(path)

save_preview(R1, os.path.join(ROOT,'build','preview2.png'))
save_preview(R2, os.path.join(ROOT,'build','preview3.png'), spawn_wx=24, spawn_wz=72)
save_preview(R3, os.path.join(ROOT,'build','preview4.png'), spawn_wx=24, spawn_wz=72)
save_preview(R4, os.path.join(ROOT,'build','preview5.png'), spawn_wx=24, spawn_wz=72)
save_preview(R5, os.path.join(ROOT,'build','preview6.png'), spawn_wx=24, spawn_wz=72)
save_preview(R6, os.path.join(ROOT,'build','preview7.png'), spawn_wx=24, spawn_wz=72)
save_preview(R7, os.path.join(ROOT,'build','preview8.png'), spawn_wx=24, spawn_wz=72)
save_preview(R8, os.path.join(ROOT,'build','preview9.png'), spawn_wx=24, spawn_wz=72)
save_preview(R9, os.path.join(ROOT,'build','preview10.png'), spawn_wx=24, spawn_wz=72)
save_preview(R10, os.path.join(ROOT,'build','preview11.png'), spawn_wx=24, spawn_wz=72)
save_preview(R11, os.path.join(ROOT,'build','preview12.png'), spawn_wx=24, spawn_wz=72)
save_preview(R12, os.path.join(ROOT,'build','preview13.png'), spawn_wx=24, spawn_wz=72)
save_preview(R13, os.path.join(ROOT,'build','preview14.png'), spawn_wx=24, spawn_wz=72)
save_preview(R14, os.path.join(ROOT,'build','preview15.png'), spawn_wx=24, spawn_wz=72)
save_preview(R15, os.path.join(ROOT,'build','preview16.png'), spawn_wx=24, spawn_wz=72)
save_preview(R16, os.path.join(ROOT,'build','preview17.png'), spawn_wx=24, spawn_wz=72)
save_preview(R17, os.path.join(ROOT,'build','preview18.png'), spawn_wx=24, spawn_wz=72)
save_preview(R18, os.path.join(ROOT,'build','preview19.png'), spawn_wx=24, spawn_wz=72)
save_preview(R19, os.path.join(ROOT,'build','preview20.png'), spawn_wx=24, spawn_wz=72)

print(f"OK room1 color-fixes:{R1['fixes']} keys:{R1['key_rects']}")
print(f"OK room2 color-fixes:{R2['fixes']} keys:{R2['key_rects']}")
print(f"OK room3 color-fixes:{R3['fixes']} keys:{R3['key_rects']}")
print(f"OK room4 color-fixes:{R4['fixes']} keys:{R4['key_rects']}")
print(f"OK room5 color-fixes:{R5['fixes']} keys:{R5['key_rects']}")
print(f"OK room6 color-fixes:{R6['fixes']} keys:{R6['key_rects']}")
print(f"OK room7 color-fixes:{R7['fixes']} keys:{R7['key_rects']}")
print(f"OK room8 color-fixes:{R8['fixes']} keys:{R8['key_rects']}")
print(f"OK room9 color-fixes:{R9['fixes']} keys:{R9['key_rects']}")
print(f"OK room10 color-fixes:{R10['fixes']} keys:{R10['key_rects']}")
print(f"OK room11 color-fixes:{R11['fixes']} keys:{R11['key_rects']}")
print(f"OK room12 color-fixes:{R12['fixes']} keys:{R12['key_rects']}")
print(f"OK room13 color-fixes:{R13['fixes']} keys:{R13['key_rects']}")
print(f"OK room14 color-fixes:{R14['fixes']} keys:{R14['key_rects']}")
print(f"OK room15 color-fixes:{R15['fixes']} keys:{R15['key_rects']}")
print(f"OK room16 color-fixes:{R16['fixes']} keys:{R16['key_rects']}")
print(f"OK room17 color-fixes:{R17['fixes']} keys:{R17['key_rects']}")
print(f"OK room18 color-fixes:{R18['fixes']} keys:{R18['key_rects']}")
print(f"OK room19 color-fixes:{R19['fixes']} keys:{R19['key_rects']}")
