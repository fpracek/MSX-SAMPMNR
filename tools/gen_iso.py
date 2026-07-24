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

    # crumble variants (only rooms with crumb_units)
    CRUMB_UNITS = spec['crumb_units']
    base_pat, base_col = bytes(pattern), bytes(color)
    crumb_meta = []
    crumb_bin = bytearray()
    _sorted_slabs = sorted(slabs, key=lambda s: -(s[0]+s[1]))
    for gi, cells in enumerate(CRUMB_UNITS):
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
        idxs = []
        for (bx, bz, y) in cells:
            for i, s in enumerate(_sorted_slabs):
                if (s[0], s[1], s[2]) == (bx, bz, y):
                    idxs.append(i)
        while len(idxs) < 2:
            idxs.append(255)
        crumb_meta.append((c0, r0, w, hgt, rectsize, base_off, cells, idxs))

    img = base_img

    # exit blink variant
    _fimg = compose({}, flash=True)
    _fp, _fc, _ = encode_screen(_fimg)
    _erect = None
    for crow in range(24):
        for ccol in range(32):
            off = crow*256 + ccol*8
            if _fp[off:off+8] != base_pat[off:off+8] or _fc[off:off+8] != base_col[off:off+8]:
                if _erect is None:
                    _erect = [ccol, crow, ccol, crow]
                else:
                    _erect[0] = min(_erect[0], ccol); _erect[1] = min(_erect[1], crow)
                    _erect[2] = max(_erect[2], ccol); _erect[3] = max(_erect[3], crow)
    EXC0, EXR0, EXC1, EXR1 = _erect
    EXW = EXC1 - EXC0 + 1
    EXNROW = EXR1 - EXR0 + 1
    exit_gfx = []
    for pv, cv in ((base_pat, base_col), (_fp, _fc)):
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
        crumb_meta=crumb_meta, crumb_bin=crumb_bin,
        exit_gfx=exit_gfx, EXC0=EXC0, EXR0=EXR0, EXNROW=EXNROW, EXW=EXW,
        cover=cover, enemy_bytes=enemy_bytes, base_img=base_img,
        exit_bx=EXIT_BX, exit_bz=EXIT_BZ, exit_y=EXIT_Y,
        name=spec['name'], enxmin=spec['enxmin'], enxmax=spec['enxmax'],
        enz=spec['enz'], ensurf=spec['ensurf'], enemy_color=spec['enemy_color'],
        en_axis=spec.get('en_axis', 0), en_centerx=spec.get('en_centerx', 0),
        lift_wx=spec.get('lift_wx', 0xFF), lift_wz=spec.get('lift_wz', 0),
        lift_ymin=spec.get('lift_ymin', 0), lift_ymax=spec.get('lift_ymax', 0),
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
)

def _wtop_vat(u):
    """mostly-flat industrial tank rim, minimal variation - The Vat"""
    return 34 + (6 if (int(u) % 10) < 2 else 0)

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
    # floor2 and the exit platform are deliberately left OUT of the
    # crumbling set. floor2: tried it first, but each cell's crumble
    # variants (revealing the ground/void below once destroyed) are
    # much bigger than a single obstacle sprite, and floor1+step+floor2
    # together measured 26400 bytes of pre-rendered variants against
    # this ROM's 8192-byte-per-bank crumble budget - a hard ceiling,
    # not a preference; floor1+step alone already fills most of that
    # budget. The exit platform was excluded on purpose (not a budget
    # issue): it's the terminal "all keys collected, leave the room"
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
    # with this many crumbling cells even 2-cell pairs blew the crumble
    # bank's 8KB budget (26400 bytes needed - measured, not guessed).
    crumb_units=[
        [(1,3,2)], [(2,3,2)], [(3,3,2)], [(5,3,2)],   # floor1, skip (4,3)
        [(1,2,4)], [(3,2,4)], [(4,2,4)], [(5,2,4)],   # step, skip (2,2)
    ],
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

_write_room_bg(R1['label'], R1)
_write_room_bg(R2['label'], R2)
_write_room_bg(R3['label'], R3)
_write_room_bg(R4['label'], R4)
_write_room_bg(R5['label'], R5)
_write_room_bg(R6['label'], R6)
_write_room_bg(R7['label'], R7)
_write_room_bg(R8['label'], R8)
_write_room_bg(R9['label'], R9)

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

# crumb9.bin: room 9's own crumbling-cell variants (step pair + floor1
# east cell, added per Fausto's request once the climb/ambush skeleton
# was confirmed solid)
crumb_bin9 = bytearray(R9['crumb_bin'])
assert len(crumb_bin9) <= 8192, len(crumb_bin9)
crumb_bin9 += bytes(8192 - len(crumb_bin9))
open(os.path.join(ROOT,'src','crumb9.bin'),'wb').write(crumb_bin9)

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
CRUMBBANK = 84
CRUMBBANK2 = 87
CRUMBBANK3 = 90
CRUMBBANK9 = 104
# Rooms 4, 5, 6 and 7 have no crumbling platforms (room_nunits=0, cell_at
# returns "no match" immediately) so their crumb_bank field is never
# actually read - reuse CRUMBBANK as a harmless placeholder instead of
# allocating a whole new (empty) bank for either of them. Room 8 and
# Room 9 DO have crumbling platforms, so each gets its own real bank
# (CRUMBBANK4, CRUMBBANK9), same as rooms 1-3.

def emit_room(R, lines):
    lab = R['label']
    lines.append(f"level{lab or 1}_map:")
    flat = []
    for z in range(MAPD):
        for y in range(MAPH):
            flat += R['grid'][z][y]
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
def emit_crumb_tab(R, lines):
    lab = R['label']
    lines.append(f"; crumb_tab{lab} (18B): ncells, (bx,y,bz)x2 FF-pad, c0,r0,c1,r1,")
    lines.append(";   dw rectsize, dw dataaddr(8000h-based), per-cell slab idx x2")
    lines.append(f"crumb_tab{lab}:")
    for (c0, r0, w, hgt, rectsize, base_off, cells, idxs) in R['crumb_meta']:
        row = [len(cells)]
        for (bx, bz, y) in cells:
            row += [bx, y, bz]
        while len(row) < 7:
            row.append(255)
        row += [c0, r0, c0+w, r0+hgt]
        lines.append("        db " + ",".join(str(v) for v in row))
        lines.append(f"        dw {rectsize}, {0x8000+base_off}")
        lines.append("        db " + ",".join(str(v) for v in idxs[:2]))
    lines.append("")

emit_room(R1, lines)
emit_crumb_tab(R1, lines)
emit_room(R2, lines)
emit_crumb_tab(R2, lines)
emit_room(R3, lines)
emit_crumb_tab(R3, lines)
emit_room(R4, lines)
emit_crumb_tab(R4, lines)
emit_room(R5, lines)
emit_crumb_tab(R5, lines)
emit_room(R6, lines)
emit_crumb_tab(R6, lines)
emit_room(R7, lines)
emit_crumb_tab(R7, lines)
emit_room(R8, lines)
emit_crumb_tab(R8, lines)
emit_room(R9, lines)
emit_crumb_tab(R9, lines)

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
lines.append("")

ENEMY_GFX_LABEL = {'': 'enemy_gfx', '2': 'bear_gfx', '3': 'chicken_gfx', '4': 'rat_gfx', '5': 'eugene_gfx', '6': 'pacman_gfx', '7': 'guardian_gfx', '8': 'kong_gfx', '9': 'urchin_gfx'}
ROOM_NAME_LABEL = {'': 'room1_name', '2': 'room2_name', '3': 'room3_name', '4': 'room4_name', '5': 'room5_name', '6': 'room6_name', '7': 'room7_name', '8': 'room8_name', '9': 'room9_name'}

def room_row(R, bgbank, bgcolbank, crumbbank):
    exb16 = R['exit_bx']*16
    ezb16 = R['exit_bz']*16
    return [
        bgbank, bgcolbank,
        f"level{R['label'] or 1}_map", f"keys_tab{R['label']}", len(R['keys']),
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
    ]

lines.append("; room_tab: one row per room, read into room_state RAM struct")
lines.append("; via a single ldir at room_start. Field order/sizes MUST match")
lines.append("; the room_state RESB block in src/main.asm exactly.")
lines.append("ROOMROWLEN equ 46")
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
        (R9, ROOM9_BGBANK, ROOM9_BGCOLBANK, CRUMBBANK9)):
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

print(f"OK room1 color-fixes:{R1['fixes']} keys:{R1['key_rects']}")
print(f"OK room2 color-fixes:{R2['fixes']} keys:{R2['key_rects']}")
print(f"OK room3 color-fixes:{R3['fixes']} keys:{R3['key_rects']}")
print(f"OK room4 color-fixes:{R4['fixes']} keys:{R4['key_rects']}")
print(f"OK room5 color-fixes:{R5['fixes']} keys:{R5['key_rects']}")
print(f"OK room6 color-fixes:{R6['fixes']} keys:{R6['key_rects']}")
print(f"OK room7 color-fixes:{R7['fixes']} keys:{R7['key_rects']}")
print(f"OK room8 color-fixes:{R8['fixes']} keys:{R8['key_rects']}")
print(f"OK room9 color-fixes:{R9['fixes']} keys:{R9['key_rects']}")
