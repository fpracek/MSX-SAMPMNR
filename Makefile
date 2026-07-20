ROM = build/sampr.rom

all: $(ROM)

$(ROM): src/main.asm src/gfx.asm src/level.asm
	@mkdir -p build
	sjasmplus --msg=err src/main.asm

gfx:
	python3 tools/gen_gfx.py

test: $(ROM)
	SDL_VIDEODRIVER=dummy openmsx -machine C-BIOS_MSX1_EU \
	  -carta $(ROM) -romtype ascii8 -script test/boot.tcl

.PHONY: all gfx test
