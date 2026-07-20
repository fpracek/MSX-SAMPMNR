#!/usr/bin/env python3
"""
Sam.Pr Miner v2 - TRUE 2:1 isometric room pre-renderer.
The whole room (walls, diamond-grid floor, platforms, keys, door) is
rendered here at pixel level and stored in ROM as a ready-made
Screen 2 image (pattern + color tables). The Z80 just block-copies it.

Projection (world px -> screen px):
  sx = 120 + wx - wz
  sy = 64 + (wx + wz)//2 - h
Block = 16x16 world px footprint, vertical step 8px (slab surfaces at 8*(y+1)).

Outputs: src/bg_pattern.bin, src/bg_color.bin, src/leveldata.asm,
         src/sprites.asm, build/preview2.png
"""
import os
import re
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
# 1. Back walls (x=0 edge and z=0 edge), height 48, panelled
# ------------------------------------------------------------------
WALLH = 56

import math as _m

def _wtop(u):
    """rolling irregular cave-wall crest"""
    return int(46 + 7*_m.sin(u/11.0) + 4*_m.sin(u/4.7 + 1.3) + 2*_m.sin(u/2.3))

def _stone(u, v):
    """True on the dark joints between stacked irregular boulders"""
    band = (v + int(3*_m.sin(u/9.0))) // 11
    ju = (u + band*13 + int(3*_m.sin(v/5.0))) % 21
    jv = (v + int(2*_m.sin(u/6.0))) % 11
    return ju < 2 or jv < 2

def _wallpix(u, v, hh):
    if v < 2:
        return 8                    # lit crest
    if _stone(u, v):
        return 1                    # joints
    return 6                        # rock

def draw_walls():
    for wx in range(0, MAPW*16):
        sx, base = proj(wx, 0, 8)
        hh = _wtop(wx)
        top = base - hh
        for sy in range(top, base):
            put(sx, sy, _wallpix(wx, sy - top, hh))
    for wz in range(0, MAPD*16):
        sx, base = proj(0, wz, 8)
        hh = _wtop(MAPW*16 + wz*1.7)
        top = base - hh
        for sy in range(top, base):
            put(sx-1, sy, _wallpix(wz + 100, sy - top, hh))

# ------------------------------------------------------------------
# 2. Floor: diamond grid (dark blue lines on black), like the example
# ------------------------------------------------------------------

def draw_floor():
    """speckled cave dirt: sparse dark-red gravel on black"""
    for bz in range(MAPD):
        for bx in range(MAPW):
            wx0, wz0 = bx*16, bz*16
            for dz in range(16):
                for dx in range(16):
                    u, v = wx0+dx, wz0+dz
                    n = (u*u*29 + v*v*23 + u*v*13) & 255
                    if n < 64:
                        sx, sy = proj(u, v, 8)
                        put(sx, sy, 6)

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
              arrows=False, rocky=False, half=False, fancy=0):
    """slab surface at h=8*(y+1), 8px thick sides (4 when half).
    fancy=1/2: Manic-Miner-style exit cube (2 = flash phase)"""
    h = 8*(y+1)
    depth = 8
    if half:
        h -= 4
        depth = 4
    wx0, wz0 = bx*16, bz*16
    # top diamond filled
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
            else:
                c = top_edge if edge else top_fill
                if arrows and not edge:
                    # conveyor treads: stripes across the x axis
                    c = 7 if (wx % 8) < 3 else top_fill
            put(sx, sy, c)
    # SW face (front-left): along edge S->W: points (wx, wz0+16)
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
    # SE face (front-right): points (wx0+16, wz)
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
# 4. Key + door art
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

def draw_key(bx, bz, y):
    """floating key above surface h=8*(y)   (y = feet block)"""
    h = 8*y + 26
    sx, sy = proj(bx*16+8, bz*16+8, h)   # block center
    sx -= 7
    # 1px black contour hugging the key shape (pops on any background)
    pix = set()
    for r, row in enumerate(KEY_ART):
        for cidx, ch in enumerate(row):
            if ch != '.':
                pix.add((cidx, r))
    for cx, r in pix:
        for dx2 in (-1, 0, 1):
            for dy2 in (-1, 0, 1):
                if (cx+dx2, r+dy2) not in pix:
                    put(sx+cx+dx2, sy+r+dy2, 1)
    for r, row in enumerate(KEY_ART):
        for cidx, ch in enumerate(row):
            if ch != '.':
                put(sx+cidx, sy+r, 15)
    return sx, sy

def draw_door(bx, bz):
    """arch on the z=0 wall behind block (bx,0)"""
    wx0 = bx*16
    for wx in range(16):
        sx, base = proj(wx0+wx, 0, 8)
        htop = 40
        for d in range(1, htop):
            sy = base - d
            c = None
            if wx < 2 or wx >= 14: c = 15
            elif d >= htop-2: c = 15
            elif d < htop-2: c = 7
            if c is not None:
                put(sx, sy, c)

# ------------------------------------------------------------------
# 4b. Slab silhouette + pre-computed mask windows (for sprite masking)
# All slabs share the same geometry: render one alone and window it.
# ------------------------------------------------------------------
def build_masks():
    """Per-pixel depth masks: for each of 8 relative-depth levels,
    64x40 sprite windows of the slab-cell silhouette restricted to
    pixels whose (rel x+z) depth is >= the level threshold."""
    # silhouette with per-pixel relative sum (0..32), cell at (2,2,y=0)
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
    ax, ay = 120, 88            # cell image anchor (N corner)
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
# 5. Level definition  grid[z][y][x]
# ------------------------------------------------------------------
T_EMPTY, T_STONE, T_CONV, T_CRUMB, T_KEY, T_DOORT, T_DOORB = range(7)
T_EXIT = 7          # exit cube (drawing style only; grid cell is T_STONE)
grid = [[[0]*MAPW for _ in range(MAPH)] for _ in range(MAPD)]

for z in range(MAPD):
    for x in range(MAPW):
        grid[z][0][x] = T_STONE          # floor

slabs = []   # (bx,bz,y,type)
for x in (2,3,4):
    t = T_CRUMB if x == 4 else T_STONE
    grid[4][2][x] = t; slabs.append((x,4,2,t))
for x in (3,4,5):
    grid[2][2][x] = T_CONV; slabs.append((x,2,2,T_CONV))
for x in (1,2):
    grid[0][3][x] = T_CRUMB; slabs.append((x,0,3,T_CRUMB))

# crumbling units (bx,bz,y): first pass -> half, second pass -> gone
CRUMB_UNITS = [
    [(1,0,3), (2,0,3)],      # the high shelf
    [(4,4,2)],               # grey block on the stone row
]

keys = [(3,4,3), (4,2,3), (1,0,4)]       # (bx,bz,feet-y)
for bx,bz,y in keys:
    grid[bz][y][bx] = T_KEY

# exit cube: half-height block on the floor; jump on top with all keys
EXIT_BX, EXIT_BZ, EXIT_Y = 6, 0, 1
grid[EXIT_BZ][EXIT_Y][EXIT_BX] = T_STONE          # solid for physics
slabs.append((EXIT_BX, EXIT_BZ, EXIT_Y, T_EXIT))

# spiky bushes (Manic Miner style): (bx, bz, surface_h) - deadly to touch
BUSHES = [
    (1, 2, 8),        # on the floor, on the path north from the spawn
    (5, 1, 8),        # on the floor, on the way to the exit cube
    (2, 4, 24),       # on top of the fixed part of the yellow platform
]

# ------------------------------------------------------------------
# 6. Compose scene (painter order)
# ------------------------------------------------------------------
def draw_shadow(bx, bz):
    """clean dark shadow patch under a floating slab"""
    for wz2 in range(16):
        for wx2 in range(16):
            sx, sy = proj(bx*16+wx2, bz*16+wz2, 8)
            put(sx, sy, 1)

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

def draw_bush(bx, bz, surf):
    """spiky plant standing on a surface at height surf"""
    sx, sy = proj(bx*16+8, bz*16+8, surf)
    top = sy - len(BUSH_ART) + 1
    pix = set()
    for r, row in enumerate(BUSH_ART):
        for cidx, ch in enumerate(row):
            if ch != '.':
                pix.add((cidx, r))
    # 1px black contour so the plant pops on the speckled floor
    for cx, r in pix:
        for dx2 in (-1, 0, 1):
            for dy2 in (-1, 0, 1):
                if (cx+dx2, r+dy2) not in pix:
                    put(sx-6+cx+dx2, top+r+dy2, 1)
    for r, row in enumerate(BUSH_ART):
        for cidx, ch in enumerate(row):
            if ch != '.':
                put(sx-6+cidx, top+r, int(ch))

STYLE = {
    T_STONE: dict(top_fill=11, top_edge=15, face_l=6,  face_r=8, rocky=True),
    T_CRUMB: dict(top_fill=14, top_edge=15, face_l=6,  face_r=8, rocky=True),
    T_CONV:  dict(top_fill=4,  top_edge=5,  face_l=6,  face_r=8, arrows=True, rocky=True),
    T_EXIT:  dict(top_fill=7,  top_edge=15, face_l=4,  face_r=7, fancy=1),
}
STYLE_EXIT_FLASH = dict(top_fill=15, top_edge=7, face_l=7, face_r=15, fancy=2)

def compose(cellstates, flash=False):
    """full scene; cellstates maps (bx,bz,y) -> 0/1/2"""
    global img
    img = [[1]*W for _ in range(H)]
    draw_walls()
    draw_floor()
    for bx,bz,y,t in slabs:
        if cellstates.get((bx, bz, y), 0) < 2:
            draw_shadow(bx, bz)
    for bx,bz,y,t in sorted(slabs, key=lambda s: (s[0]+s[1], s[2])):
        st = cellstates.get((bx, bz, y), 0)
        if st == 2:
            continue
        style = STYLE_EXIT_FLASH if (flash and t == T_EXIT) else STYLE[t]
        draw_slab(bx, bz, y, half=(st == 1), **style)
    for bx,bz,surf in BUSHES:
        draw_bush(bx, bz, surf)
    return img

# base scene, tracking per-slab pixels for mask/cover data
import copy
img = [[1]*W for _ in range(H)]
draw_walls()
draw_floor()
for bx,bz,y,t in slabs:
    draw_shadow(bx, bz)
slab_surf = [[0]*W for _ in range(H)]   # surface height of slab pixels
for bx,bz,y,t in sorted(slabs, key=lambda s: (s[0]+s[1], s[2])):
    _before = copy.deepcopy(img)
    draw_slab(bx, bz, y, **STYLE[t])
    _s = 8*(y+1)
    for _yy in range(H):
        rb, ra = _before[_yy], img[_yy]
        for _xx in range(W):
            if ra[_xx] != rb[_xx]:
                slab_surf[_yy][_xx] = _s
for bx,bz,surf in BUSHES:
    draw_bush(bx, bz, surf)

# cover table: floor cells whose centre a slab image visually covers.
# core box = 8x12 around a sprite standing at the cell centre.
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
                if s >= 32 and s > mh:   # only head-height slabs cover
                    mh = s
        # own-footprint cells are handled by normal collision
        cover[bz][bx] = mh

# ------------------------------------------------------------------
# 7. Encode Screen2 pattern+color with 2-color-per-byte-row auto-fix
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

# background WITHOUT keys (so restoring it erases a picked-up key)
pattern, color, fixes = encode_screen(img)
open(os.path.join(ROOT,'src','bg_pattern.bin'),'wb').write(pattern)
open(os.path.join(ROOT,'src','bg_color.bin'),'wb').write(color)

# ---- crumble variants: every per-cell state combo, pre-rendered ----
base_pat, base_col = bytes(pattern), bytes(color)
base_img = img
crumb_meta = []
crumb_bin = bytearray()
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
    crumb_meta.append((c0, r0, w, hgt, rectsize, base_off))
assert len(crumb_bin) <= 8192, len(crumb_bin)
crumb_bin += bytes(8192 - len(crumb_bin))
open(os.path.join(ROOT,'src','crumb.bin'),'wb').write(crumb_bin)

# ---- exit cube blink variant: same scene, flash colours, diff rect ----
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

img = base_img          # restore the base scene for the key pass

# now draw keys on top and encode again: extract per-key char blocks
key_rects = []
for bx,bz,y in keys:
    sx, sy = draw_key(bx, bz, y)
    c0, r0 = sx//8, sy//8
    key_rects.append((bx, bz, y, c0, r0))

pattern2, color2, _ = encode_screen(img)
keys_gfx = []      # per key: 32 bytes patterns (4 chars) + 32 bytes colors
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

# ------------------------------------------------------------------
# 8. Sam.Pr sprites: official set from Fausto's MSX-C games.
# 12 poses (Front, FrontW1, FrontW2, Rear, RearW1, RearW2,
#           Left, LeftW1, LeftW2, Right, RightW1, RightW2)
# x 4 color layers (9, 11, 14, 15), 32 bytes each = 128 bytes/pose.
# ------------------------------------------------------------------
_c = open(os.path.join(ROOT,'tools','sam_sprites.c')).read()
sprites = [int(t,16) for t in re.findall(r'0x([0-9A-Fa-f]{2})', _c)]
assert len(sprites) == 12*128, len(sprites)

SAM_LAYER_COLORS = (14, 9, 4, 15)

def pose_pixels(pose):
    """render one pose to a 16x16 grid of palette indices (for preview)"""
    px = [[0]*16 for _ in range(16)]
    base = pose*128
    for l, col in enumerate(SAM_LAYER_COLORS):
        off = base + l*32
        for y in range(16):
            bits = (sprites[off+y] << 8) | sprites[off+16+y]
            for x in range(16):
                if bits & (0x8000 >> x):
                    px[y][x] = col
    return px

# ------------------------------------------------------------------
# 9. Emit asm data (level map, key table, sprites)
# ------------------------------------------------------------------
def db(bs, per=13):
    out = []
    for i in range(0, len(bs), per):
        out.append("        db " + ",".join(f"0{b:02X}h" for b in bs[i:i+per]))
    return "\n".join(out)

lines = ["; AUTOGENERATED by tools/gen_iso.py",""]
lines.append(f"MAPW equ {MAPW}")
lines.append(f"MAPH equ {MAPH}")
lines.append(f"MAPD equ {MAPD}")
lines.append(f"NKEYS equ {len(keys)}")
lines.append(f"EXIT_BX equ {EXIT_BX}")
lines.append(f"EXIT_BZ equ {EXIT_BZ}")
lines.append(f"EXSURF equ {8*(EXIT_Y+1)}")
lines.append(f"EXC0 equ {EXC0}")
lines.append(f"EXR0 equ {EXR0}")
lines.append(f"EXNROW equ {EXNROW}")
lines.append(f"EXROWLEN equ {EXW*8}")
lines.append("level1_map:")
flat = []
for z in range(MAPD):
    for y in range(MAPH):
        flat += grid[z][y]
lines.append(db(flat, MAPW))
lines.append("")
lines.append("; key table: bx, bz, y, char_col, char_row  (5 bytes each)")
lines.append("keys_tab:")
for bx,bz,y,c0,r0 in key_rects:
    lines.append(f"        db {bx},{bz},{y},{c0},{r0}")
lines.append("")
MASK_COLORS = {T_STONE: 11, T_CRUMB: 14, T_CONV: 4, T_EXIT: 7}
lines.append("; slab table for sprite masking: winx0, winy0, base_sum, surface, color")
lines.append(f"NSLABS equ {len(slabs)}")
lines.append("slab_tab:")
for bx,bz,y,t in sorted(slabs, key=lambda s: -(s[0]+s[1])):
    sxN = 120 + 16*(bx-bz)
    syN = 64 + 8*(bx+bz) - 8*(y+1)
    winx0 = (sxN + MASK_RELX) & 0xFF
    winy0 = (syN + MASK_RELY) & 0xFF
    base  = 16*(bx+bz)
    surf  = 8*(y+1)
    lines.append(f"        db {winx0},{winy0},{base},{surf},{MASK_COLORS[t]}")
lines.append("")
_sorted_slabs = sorted(slabs, key=lambda s: -(s[0]+s[1]))
lines.append(f"NUNITS equ {len(CRUMB_UNITS)}")
lines.append("CRUMBBANK equ 84")
lines.append("; crumb_tab (18B): ncells, (bx,y,bz)x2 FF-pad, c0,r0,c1,r1,")
lines.append(";   dw rectsize, dw dataaddr(8000h-based), per-cell slab idx x2")
lines.append("crumb_tab:")
for gi, cells in enumerate(CRUMB_UNITS):
    c0, r0, w, hgt, rectsize, base_off = crumb_meta[gi]
    row = [len(cells)]
    for (bx, bz, y) in cells:
        row += [bx, y, bz]
    while len(row) < 7:
        row.append(255)
    row += [c0, r0, c0+w, r0+hgt]
    lines.append("        db " + ",".join(str(v) for v in row))
    lines.append(f"        dw {rectsize}, {0x8000+base_off}")
    idxs = []
    for (bx, bz, y) in cells:
        for i, s in enumerate(_sorted_slabs):
            if (s[0], s[1], s[2]) == (bx, bz, y):
                idxs.append(i)
    while len(idxs) < 2:
        idxs.append(255)
    lines.append("        db " + ",".join(str(v) for v in idxs[:2]))
lines.append("")
lines.append("; cover table: min feet height to cross each floor cell (z-major)")
lines.append("cover_tab:")
for z in range(MAPD):
    lines.append(db(cover[z], MAPW))
lines.append("")
lines.append("; per-key char graphics: 32 bytes patterns + 32 bytes colors")
lines.append("keys_gfx:")
for blk in keys_gfx:
    lines.append(db(list(blk), 16))
lines.append("")
lines.append("; exit cube rect: row-major pattern bytes then colour bytes")
lines.append("exit_gfx0:")
lines.append(db(list(exit_gfx[0]), 16))
lines.append("exit_gfx1:")
lines.append(db(list(exit_gfx[1]), 16))
lines.append("")
lines.append("; deadly bushes: bx, bz, kill ceiling (surface+10)")
lines.append(f"NHAZ equ {len(BUSHES)}")
lines.append("hazards_tab:")
for bx,bz,surf in BUSHES:
    lines.append(f"        db {bx},{bz},{surf+10}")
lines.append("")
_f = open(os.path.join(ROOT,'tools','fonts.c')).read()
_fontbytes = [int(t,16) for t in re.findall(r'0x([0-9A-Fa-f]{2})', _f)]
assert len(_fontbytes) == 608, len(_fontbytes)
lines.append("; redefined font, 76 chars from '0' (8 bytes each)")
lines.append("fonts_tab:")
lines.append(db(_fontbytes, 16))
lines.append("")
ENEMY = [[
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
]]
enemy_bytes = []
for fr in ENEMY:
    left, right = [], []
    for r in fr:
        bits = 0
        for ch in r:
            bits = (bits << 1) | (1 if ch == 'X' else 0)
        left.append((bits >> 8) & 255)
        right.append(bits & 255)
    enemy_bytes += left + right
lines.append("enemy_gfx:")
lines.append(db(enemy_bytes, 16))
lines.append("")
lines.append("gfx_sprites:")
lines.append(db(sprites, 16))
open(os.path.join(ROOT,'src','leveldata.asm'),'w').write("\n".join(lines)+"\n")

# ------------------------------------------------------------------
# 10. Preview png (with Sam at start)
# ------------------------------------------------------------------
prev = Image.new('RGB', (W,H))
for y in range(H):
    for x in range(W):
        prev.putpixel((x,y), PAL[img[y][x]])
# Sam at start (wx=24, wz=72, h=8)
swx, swz, sh = 24, 72, 8
sx = X0 + swx - swz - 8
sy = Y0 + (swx+swz)//2 - sh - 16
_pp = pose_pixels(0)
for r in range(16):
    for c in range(16):
        if _pp[r][c]:
            prev.putpixel((sx+c, sy+r), PAL[_pp[r][c]])
prev.resize((512,384), Image.NEAREST).save(os.path.join(ROOT,'build','preview2.png'))
print(f"OK  color-fixes:{fixes}  keys:{key_rects}")
