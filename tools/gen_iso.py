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
def draw_floor(base, speckle):
    """base=None: leave black (cave dirt on bare black, original look).
    base=color: prefill the whole floor with it first (icy floor look)."""
    for bz in range(MAPD):
        for bx in range(MAPW):
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

def draw_hazard(bx, bz, surf, art):
    """spiky plant/icicle standing on a surface at height surf.
    art chars: digit = literal palette index, 'F' = 15 (white)."""
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
                c = 15 if ch == 'F' else int(ch)
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

    grid = [[[0]*MAPW for _ in range(MAPH)] for _ in range(MAPD)]
    for z in range(MAPD):
        for x in range(MAPW):
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
        draw_floor(spec['floor_base'], spec['floor_speckle'])
        for bx,bz,y,t in slabs:
            if cellstates.get((bx, bz, y), 0) < 2:
                draw_shadow(bx, bz)
        for bx,bz,y,t in sorted(slabs, key=lambda s: (s[0]+s[1], s[2])):
            st = cellstates.get((bx, bz, y), 0)
            if st == 2:
                continue
            style = STYLE_EXIT_FLASH if (flash and t == T_EXIT) else STYLE[t]
            draw_slab(bx, bz, y, half=(st == 1), **style)
        for bx,bz,surf in spec['hazards']:
            draw_hazard(bx, bz, surf, spec['hazard_art'])
        return img

    img = [[1]*W for _ in range(H)]
    draw_walls(spec['wallcol'], spec['crest_fn'])
    draw_floor(spec['floor_base'], spec['floor_speckle'])
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
    for bx,bz,surf in spec['hazards']:
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
    enemy_bytes = []
    for fr in spec['enemy_frames']:
        left, right = [], []
        for r in fr:
            bits = 0
            for ch in r:
                bits = (bits << 1) | (1 if ch == 'X' else 0)
            left.append((bits >> 8) & 255)
            right.append(bits & 255)
        enemy_bytes += left + right

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
        hazards=spec['hazards'],
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

R1 = render_room(ROOM1)
R2 = render_room(ROOM2)

open(os.path.join(ROOT,'src','bg_pattern.bin'),'wb').write(R1['pattern'])
open(os.path.join(ROOT,'src','bg_color.bin'),'wb').write(R1['color'])
open(os.path.join(ROOT,'src','bg_pattern2.bin'),'wb').write(R2['pattern'])
open(os.path.join(ROOT,'src','bg_color2.bin'),'wb').write(R2['color'])

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

# ------------------------------------------------------------------
# ROM bank numbers (must match the equ's added in src/main.asm)
# ------------------------------------------------------------------
ROOM1_BGBANK, ROOM1_BGCOLBANK = 2, 3
ROOM2_BGBANK, ROOM2_BGCOLBANK = 85, 86
CRUMBBANK = 84
CRUMBBANK2 = 87

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
    lines.append(f"cover_tab{lab}:")
    for z in range(MAPD):
        lines.append(db(R['cover'][z], MAPW))
    lines.append("")
    lines.append(f"keys_gfx{lab}:")
    for blk in R['keys_gfx']:
        lines.append(db(list(blk), 16))
    lines.append("")
    lines.append(f"exit_gfx{lab}_0:")
    lines.append(db(list(R['exit_gfx'][0]), 16))
    lines.append(f"exit_gfx{lab}_1:")
    lines.append(db(list(R['exit_gfx'][1]), 16))
    lines.append("")
    lines.append(f"hazards_tab{lab}:")
    for bx,bz,surf in R['hazards']:
        lines.append(f"        db {bx},{bz},{surf+10}")
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

lines.append("; redefined font, 76 chars from '0' (8 bytes each)")
_f = open(os.path.join(ROOT,'tools','fonts.c')).read()
_fontbytes = [int(t,16) for t in re.findall(r'0x([0-9A-Fa-f]{2})', _f)]
assert len(_fontbytes) == 608, len(_fontbytes)
lines.append("fonts_tab:")
lines.append(db(_fontbytes, 16))
lines.append("")
lines.append("enemy_gfx:")
lines.append(db(R1['enemy_bytes'], 16))
lines.append("")
lines.append("bear_gfx:")
lines.append(db(R2['enemy_bytes'], 16))
lines.append("")

_c = open(os.path.join(ROOT,'tools','sam_sprites.c')).read()
sprites = [int(t,16) for t in re.findall(r'0x([0-9A-Fa-f]{2})', _c)]
assert len(sprites) == 12*128, len(sprites)

lines.append("; room name strings for the intro card: raw ASCII, draw_string-ready")
lines.append("room1_name:")
lines.append("        db " + ",".join(str(ord(c)) for c in R1['name']) + ",0")
lines.append("room2_name:")
lines.append("        db " + ",".join(str(ord(c)) for c in R2['name']) + ",0")
lines.append("")

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
        ("enemy_gfx" if R['label'] == '' else "bear_gfx"), R['enemy_color'],
        R['enxmin'], R['enxmax'], R['enz'], R['ensurf'],
        (f"room{1}_name" if R['label'] == '' else f"room2_name"),
    ]

lines.append("; room_tab: one row per room, read into room_state RAM struct")
lines.append("; via a single ldir at room_start. Field order/sizes MUST match")
lines.append("; the room_state RESB block in src/main.asm exactly.")
lines.append("ROOMROWLEN equ 39")
lines.append("room_tab:")
for R, bgbank, bgcolbank, crumbbank in (
        (R1, ROOM1_BGBANK, ROOM1_BGCOLBANK, CRUMBBANK),
        (R2, ROOM2_BGBANK, ROOM2_BGCOLBANK, CRUMBBANK2)):
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
    lines.append(f"        db {f[24]},{f[25]},{f[26]},{f[27]}")
    lines.append(f"        dw {f[28]}")
lines.append("")

lines.append("gfx_sprites:")
lines.append(db(sprites, 16))
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

print(f"OK room1 color-fixes:{R1['fixes']} keys:{R1['key_rects']}")
print(f"OK room2 color-fixes:{R2['fixes']} keys:{R2['key_rects']}")
