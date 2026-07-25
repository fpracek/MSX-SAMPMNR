#!/usr/bin/env python3
# Generates the title-screen decoration above the piano keyboard: a mine
# cart brimming with gems, sitting on a short rail. Full-width (32 cols x
# 8px) x TDECO_ROWS (8px each) Screen2 pattern+color strip, blitted via
# LDIRVM into VR_PAT/VR_COL starting at row TDECO_ROW0 in main.asm's
# title_setup. Uses the same identity name-table addressing (row*256 +
# col*8 + y) every other full-width blit in this project relies on.
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COLS = 32
TDECO_ROWS = 6          # 6 tile-rows = 48px tall
W = COLS * 8            # 256px wide
H = TDECO_ROWS * 8      # 48px tall

BLACK = 1
GRAY = 14
WHITE = 15
RED = 9
BLUE = 5
GREEN = 3
YELLOW = 11

# per-pixel color index grid, BLACK = background/transparent
grid = [[BLACK] * W for _ in range(H)]

def diamond(cx, cy, r, color):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if 0 <= x < W and 0 <= y < H and abs(x - cx) + abs(y - cy) <= r:
                grid[y][x] = color

def rect(x0, y0, x1, y1, color):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if 0 <= x < W and 0 <= y < H:
                grid[y][x] = color

def trapezoid(x0top, x1top, x0bot, x1bot, y0, y1, color):
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, (y1 - y0))
        xl = int(x0top + (x0bot - x0top) * t)
        xr = int(x1top + (x1bot - x1top) * t)
        for x in range(xl, xr + 1):
            if 0 <= x < W and 0 <= y < H:
                grid[y][x] = color

CX = W // 2

# rail: 2 thin horizontal lines near the bottom
rect(CX - 56, 40, CX + 56, 40, GRAY)
rect(CX - 56, 42, CX + 56, 42, GRAY)
for wx in range(-48, 49, 12):
    rect(CX + wx, 41, CX + wx, 41, BLACK)  # sleeper gaps read as ties

# cart body: wide trapezoid tapering down, gray with a darker rim
trapezoid(CX - 40, CX + 40, CX - 32, CX + 32, 24, 38, GRAY)
rect(CX - 40, 23, CX + 40, 24, WHITE)      # top rim highlight

# 2 wheels
diamond(CX - 28, 40, 4, BLACK)
diamond(CX + 28, 40, 4, BLACK)
rect(CX - 31, 37, CX - 25, 43, GRAY)
rect(CX + 25, 37, CX + 31, 43, GRAY)

# gems spilling out the top, 4 colors, staggered heights
diamond(CX - 22, 16, 7, RED)
diamond(CX - 6, 10, 8, GREEN)
diamond(CX + 10, 14, 7, BLUE)
diamond(CX + 26, 18, 6, YELLOW)
# small sparkle highlights on the 2 biggest gems
grid[7][CX - 7] = WHITE
grid[7][CX - 6] = WHITE
grid[12][CX + 9] = WHITE

def pack_pattern():
    out = bytearray()
    for trow in range(TDECO_ROWS):
        for col in range(COLS):
            for y in range(8):
                py = trow * 8 + y
                b = 0
                for bit in range(8):
                    px = col * 8 + bit
                    if grid[py][px] != BLACK:
                        b |= (0x80 >> bit)
                out.append(b)
    return bytes(out)

def pack_color():
    out = bytearray()
    for trow in range(TDECO_ROWS):
        for col in range(COLS):
            for y in range(8):
                py = trow * 8 + y
                # single dominant fg color for this 8px line (screen2:
                # one fg/bg pair per line) - pick the most common non-black
                # pixel in this line's 8px span, default white if none
                counts = {}
                for bit in range(8):
                    px = col * 8 + bit
                    c = grid[py][px]
                    if c != BLACK:
                        counts[c] = counts.get(c, 0) + 1
                fg = max(counts, key=counts.get) if counts else WHITE
                out.append((fg << 4) | BLACK)
    return bytes(out)

pat = pack_pattern()
col = pack_color()
assert len(pat) == TDECO_ROWS * COLS * 8
assert len(col) == TDECO_ROWS * COLS * 8

with open(os.path.join(ROOT, 'src', 'title_deco_pat.bin'), 'wb') as f:
    f.write(pat)
with open(os.path.join(ROOT, 'src', 'title_deco_col.bin'), 'wb') as f:
    f.write(col)

print(f"OK title_deco: {len(pat)} pattern bytes, {len(col)} color bytes "
      f"({TDECO_ROWS} rows x {COLS} cols)")

# quick preview render for visual review before wiring into the ROM
try:
    from PIL import Image
    im = Image.new('RGB', (W, H))
    PALRGB = {
        BLACK: (0, 0, 0), GRAY: (180, 180, 180), WHITE: (255, 255, 255),
        RED: (220, 60, 60), BLUE: (80, 120, 240), GREEN: (60, 200, 90),
        YELLOW: (230, 210, 60),
    }
    for y in range(H):
        for x in range(W):
            im.putpixel((x, y), PALRGB.get(grid[y][x], (0, 0, 0)))
    im = im.resize((W * 3, H * 3), Image.NEAREST)
    im.save(os.path.join(ROOT, 'build', 'title_deco_preview.png'))
    print("wrote build/title_deco_preview.png")
except ImportError:
    pass
