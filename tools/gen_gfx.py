#!/usr/bin/env python3
"""
Sam.Pr Miner - graphics + level generator
Generates: src/gfx.asm, src/level.asm, build/preview.png
MSX1 Screen 2 constraints: each 8x1 row of a char has max 2 colors (fg/bg).
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# TMS9918 palette (index -> RGB)
PAL = {
    0:  (0, 0, 0),        # transparent (render as black)
    1:  (0, 0, 0),        # black
    2:  (33, 200, 66),    # medium green
    3:  (94, 220, 120),   # light green
    4:  (84, 85, 237),    # dark blue
    5:  (125, 118, 252),  # light blue
    6:  (212, 82, 77),    # dark red
    7:  (66, 235, 245),   # cyan
    8:  (252, 85, 84),    # medium red
    9:  (255, 121, 120),  # light red
    10: (212, 193, 84),   # dark yellow
    11: (230, 206, 128),  # light yellow
    12: (33, 176, 59),    # dark green
    13: (201, 91, 186),   # magenta
    14: (204, 204, 204),  # gray
    15: (255, 255, 255),  # white
}

# ------------------------------------------------------------------
# Tile art: 16x16 arrays of palette indices. Tile = 2x2 chars.
# Convention: rows 0-7 = top face, rows 8-15 = front face.
# ------------------------------------------------------------------

def make_tile(rows):
    assert len(rows) == 16
    t = []
    for r in rows:
        assert len(r) == 16
        t.append(list(r))
    return t


def solid_rows(top_bg, top_fg, front_bg, front_fg, speckle_top, speckle_front):
    """Stone-like block. speckle_* : set of (x,y) fg pixels."""
    rows = []
    for y in range(16):
        row = []
        for x in range(16):
            if y < 8:
                c = top_fg if (x, y) in speckle_top else top_bg
            else:
                c = front_fg if (x, y - 8) in speckle_front else front_bg
            row.append(c)
        rows.append(row)
    return rows


# stone: light-yellow top with dark-yellow texture, dark-red front with black cracks
_stone_top = {(2,1),(3,1),(9,2),(10,2),(5,4),(6,4),(12,5),(13,5),(1,6),(2,6),(8,6),(14,3),(0,3)}
_stone_top |= {(x,0) for x in range(16)}          # top edge highlight line (fg=white row)
_stone_front = {(1,2),(2,2),(3,2),(8,4),(9,4),(10,4),(13,1),(4,6),(5,6),(12,6),(6,3),(11,5)}
_stone_front |= {(x,7) for x in range(16)}         # bottom shadow line

STONE = solid_rows(11, 10, 6, 1, _stone_top - {(x,0) for x in range(16)}, _stone_front)
# white highlight on row 0 (2 colors in row: white on light yellow)
for x in range(16):
    STONE[0][x] = 15 if x % 2 == 0 else 11

# crumbling platform: like stone but grey top with cracks
_cr_top = {(3,2),(4,3),(5,4),(10,2),(11,3),(12,4),(7,5),(8,6),(2,6),(13,6)}
CRUMB = solid_rows(14, 1, 6, 1, _cr_top, _stone_front)
for x in range(16):
    CRUMB[0][x] = 15 if x % 3 == 0 else 14

# conveyor: cyan arrows on dark blue top, dark blue front
CONV = []
for y in range(16):
    row = []
    for x in range(16):
        if y < 8:
            # arrows '>' pointing right, animated later
            fx = (x + y) % 8
            c = 7 if fx in (2, 3) else 4
        else:
            c = 4 if (y in (8, 15) or x in (0, 15)) else 1
        row.append(c)
    CONV.append(row)

# key item: light-yellow key on black
KEY_ART = [
    "................",
    "................",
    "....HHH.........",
    "...H...H........",
    "...H...H........",
    "....HHH.........",
    ".....H..........",
    ".....H..........",
    ".....H.HHHHHH...",
    ".....H.H..H.H...",
    ".....HHH..H.H...",
    "................",
    "................",
    "................",
    "................",
    "................",
]

def art_to_tile(art, mapping):
    rows = []
    for r in art:
        row = []
        for ch in r:
            row.append(mapping.get(ch, 1))
        rows.append(row)
    return rows

KEY = art_to_tile(KEY_ART, {'.': 1, 'H': 11})

# door: 16x32 (two tiles stacked). White arch, cyan interior.
DOOR_T_ART = [
    "WWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWWWWWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
]
DOOR_B_ART = [
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWCCCCCCCCCCCCWW",
    "WWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWWWWWW",
]
DOOR_T = art_to_tile(DOOR_T_ART, {'.': 1, 'W': 15, 'C': 7})
DOOR_B = art_to_tile(DOOR_B_ART, {'.': 1, 'W': 15, 'C': 7})

TILES = [None, STONE, CONV, CRUMB, KEY, DOOR_T, DOOR_B]
TILE_NAMES = ["EMPTY", "STONE", "CONV", "CRUMB", "KEY", "DOOR_T", "DOOR_B"]

# ------------------------------------------------------------------
# Validate + encode tiles to Screen2 pattern/color bytes
# char order per tile: TL, TR, BL, BR  -> char index = 1 + (tile-1)*4 + q
# ------------------------------------------------------------------

def encode_tile(tile, name):
    """returns list of 4 chars, each (8 pattern bytes, 8 color bytes)"""
    chars = []
    for q in range(4):
        ox, oy = (q % 2) * 8, (q // 2) * 8
        pat, col = [], []
        for y in range(8):
            row = [tile[oy + y][ox + x] for x in range(8)]
            cols = sorted(set(row))
            if len(cols) > 2:
                raise ValueError(f"{name} char{q} row{y}: >2 colors {cols}")
            if len(cols) == 1:
                bg = cols[0]
                fg = 15
            else:
                bg, fg = cols[0], cols[1]
            bits = 0
            for x in range(8):
                bits = (bits << 1) | (1 if row[x] == fg else 0)
            pat.append(bits)
            col.append((fg << 4) | bg)
        chars.append((pat, col))
    return chars

# ------------------------------------------------------------------
# Sam.Pr sprites: 16x16, two layers (colors), 2 walk frames per side
# Layer A = white (helmet lamp, face, hands, boots), Layer B = medium red suit
# ------------------------------------------------------------------

SAM_R1 = [  # facing right, frame 1   W=white layer, R=red layer
    "......WWWW......",
    ".....WWWWWW.....",
    ".....WWWWWW.....",
    "......WWWW*.....",
    "......WWWW......",
    ".....RRRRRR.....",
    "....RRRRRRRR....",
    "....RRWRRWRR....",
    "....RRRRRRRR....",
    ".....RRRRRR.....",
    "......RRRR......",
    "......R..R......",
    ".....RR..RR.....",
    ".....R....R.....",
    "....WW....WW....",
    "....WW....WW....",
]
SAM_R2 = [  # facing right, frame 2 (legs together)
    "......WWWW......",
    ".....WWWWWW.....",
    ".....WWWWWW.....",
    "......WWWW*.....",
    "......WWWW......",
    ".....RRRRRR.....",
    "....RRRRRRRR....",
    "....RRWRRWRR....",
    "....RRRRRRRR....",
    ".....RRRRRR.....",
    "......RRRR......",
    "......RRRR......",
    "......R..R......",
    "......R..R......",
    ".....WW..WW.....",
    ".....WW..WW.....",
]

def mirror(art):
    return ["".join(reversed(r)) for r in art]

SAM_L1 = mirror(SAM_R1)
SAM_L2 = mirror(SAM_R2)


def sprite_layer(art, chars_in):
    """16x16 -> 32 bytes (left col 16, right col 16), for given set of chars"""
    left, right = [], []
    for y in range(16):
        bits = 0
        for x in range(16):
            bits = (bits << 1) | (1 if art[y][x] in chars_in else 0)
        left.append((bits >> 8) & 0xFF)
        right.append(bits & 0xFF)
    return left + right


SPRITES = []  # list of (name, bytes)
for nm, art in [("R1", SAM_R1), ("R2", SAM_R2), ("L1", SAM_L1), ("L2", SAM_L2)]:
    SPRITES.append((f"SAM_{nm}_W", sprite_layer(art, {'W', '*'})))
    SPRITES.append((f"SAM_{nm}_R", sprite_layer(art, {'R'})))

# ------------------------------------------------------------------
# Level: Central Cavern remix.  grid[z][y][x], z=0 front, 13 wide, 8 high
# ------------------------------------------------------------------
MAPW, MAPH, MAPD = 13, 8, 3
T_EMPTY, T_STONE, T_CONV, T_CRUMB, T_KEY, T_DOOR_T, T_DOOR_B = range(7)

grid = [[[0] * MAPW for _ in range(MAPH)] for _ in range(MAPD)]

# ground floor: all lanes
for z in range(MAPD):
    for x in range(MAPW):
        grid[z][0][x] = T_STONE

# left stair up (lane 1)
grid[1][1][1] = T_STONE
grid[1][2][2] = T_STONE

# mid platform (lane 1), with crumbling section
for x in range(3, 7):
    grid[1][3][x] = T_STONE if x < 5 else T_CRUMB

# conveyor high on back lane
for x in range(5, 10):
    grid[2][5][x] = T_CONV

# high right platform front lane
for x in range(9, 12):
    grid[0][4][x] = T_STONE

# step to reach conveyor from mid platform
grid[2][4][4] = T_STONE

# keys (3): on mid platform, on conveyor level, on right platform
grid[1][4][3] = T_KEY
grid[2][6][7] = T_KEY
grid[0][5][10] = T_KEY

# door on floor, right side, lane 1
grid[1][1][12] = T_DOOR_B
grid[1][2][12] = T_DOOR_T

# ------------------------------------------------------------------
# Preview render
# ------------------------------------------------------------------
XBASE, YBASE = 24, 176

def render_preview(path):
    im = Image.new("RGB", (256, 192), PAL[1])
    px_ = im.load()
    for z in range(MAPD - 1, -1, -1):        # back to front
        for y in range(MAPH):
            for x in range(MAPW):
                t = grid[z][y][x]
                if not t:
                    continue
                tx = XBASE + 16 * x + 8 * z
                ty = YBASE - 8 * y - 8 * z
                tile = TILES[t]
                for yy in range(16):
                    for xx in range(16):
                        sx, sy = tx + xx, ty + yy
                        if 0 <= sx < 256 and 0 <= sy < 192:
                            px_[sx, sy] = PAL[tile[yy][xx]]
    # draw Sam at start pos (x=0 lane1 floor)
    swx, swz = 4, 1
    sx = XBASE + swx + 8 * swz
    sy = YBASE - 8 * swz + 8 - 16 - 8   # feet on floor top surface (h=8)
    for y in range(16):
        for xx in range(16):
            ch = SAM_R1[y][xx]
            if ch in ('W', '*'):
                px_[sx + xx, sy + y] = PAL[15]
            elif ch == 'R':
                px_[sx + xx, sy + y] = PAL[8]
    im.resize((512, 384), Image.NEAREST).save(path)

# ------------------------------------------------------------------
# Emit asm
# ------------------------------------------------------------------

def db_lines(bs, per=8):
    out = []
    for i in range(0, len(bs), per):
        out.append("        db " + ",".join(f"{b:03o}o" if False else f"0{b:02X}h" for b in bs[i:i + per]))
    return "\n".join(out)


def main():
    # encode tiles
    all_chars = []
    for t in range(1, len(TILES)):
        all_chars.extend(encode_tile(TILES[t], TILE_NAMES[t]))
    n_chars = 1 + len(all_chars)
    assert n_chars <= 256

    pat_bytes, col_bytes = [0] * 8, [0x11] * 8  # char 0 = empty/black
    for pat, col in all_chars:
        pat_bytes += pat
        col_bytes += col

    lines = ["; AUTOGENERATED by tools/gen_gfx.py - do not edit", ""]
    lines.append(f"GFX_NCHARS equ {n_chars}")
    lines.append("gfx_patterns:")
    lines.append(db_lines(pat_bytes))
    lines.append("gfx_colors:")
    lines.append(db_lines(col_bytes))
    lines.append("")
    lines.append("; sprite patterns: 8 x 32 bytes (R1W R1R R2W R2R L1W L1R L2W L2R)")
    lines.append("gfx_sprites:")
    for nm, bs in SPRITES:
        lines.append(f"; {nm}")
        lines.append(db_lines(bs))
    with open(os.path.join(ROOT, "src", "gfx.asm"), "w") as f:
        f.write("\n".join(lines) + "\n")

    # level
    lv = ["; AUTOGENERATED by tools/gen_gfx.py - do not edit", ""]
    lv.append(f"MAPW equ {MAPW}")
    lv.append(f"MAPH equ {MAPH}")
    lv.append(f"MAPD equ {MAPD}")
    lv.append("; grid bytes: z-major, then y, then x")
    lv.append("level1_map:")
    for z in range(MAPD):
        for y in range(MAPH):
            lv.append(db_lines(grid[z][y], per=MAPW) + f"  ; z={z} y={y}")
    with open(os.path.join(ROOT, "src", "level.asm"), "w") as f:
        f.write("\n".join(lv) + "\n")

    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    render_preview(os.path.join(ROOT, "build", "preview.png"))
    print(f"OK: {n_chars} chars, {len(SPRITES)} sprite patterns")


if __name__ == "__main__":
    main()
