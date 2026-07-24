; ============================================================
;  SAM.PR MINER v2 -  MSX1 (16KB RAM) + MegaROM ASCII8
;  Vera prospettiva isometrica 2:1, sfondo pre-renderizzato in ROM
;  Assembler: sjasmplus
; ============================================================

        OUTPUT "build/sampr.rom"

; ---------- BIOS ----------
WRTVDP  equ 0047h
WRTVRM  equ 004Dh
SETWRT  equ 0053h
FILVRM  equ 0056h
LDIRVM  equ 005Ch
CHGMOD  equ 005Fh
GTSTCK  equ 00D5h
GTTRIG  equ 00D8h
SNSMAT  equ 00141h     ; A=row(0-10) -> A=that row's 8 key bits (0=pressed)
WRTPSG  equ 0093h
ENASLT  equ 00024h
RSLREG  equ 00138h
EXPTBL  equ 0FCC1h

; ---------- VRAM (Screen 2) ----------
VR_PAT  equ 00000h
VR_NAME equ 01800h
VR_SPRA equ 01B00h
VR_COL  equ 02000h
VR_SPRP equ 03800h

; ---------- ASCII8 mapper ----------
BANK0R  equ 06000h
BANK1R  equ 06800h
BANK2R  equ 07000h
BANK3R  equ 07800h

; ---------- game constants ----------
; projection: sx = 120 + wx - wz ; sy = 56 + (wx+wz)/2 - h
PX0     equ 120
PY0     equ 64
T_STONE equ 1
T_CONV  equ 2
T_CRUMB equ 3
T_KEY   equ 4
T_DOORT equ 5
T_DOORB equ 6
GRAV    equ 32          ; 0.125 px/f^2 (8.8)
JUMPV   equ 0240h       ; 2.25 px/f (apex ~20px: one level per jump)
CRUMB_DWELL equ 45     ; frames Sam can DWELL on the same still-intact
                        ; crumbling cell before it degrades one more
                        ; stage (Room9: Fausto wanted standing still
                        ; to keep destroying the platform, not just a
                        ; fresh touch - "sampr non puo' fermarsi su
                        ; una piattaforma senza che lei si distrugga
                        ; completamente"). Only active when
                        ; room_crumb_continuous is set; other rooms
                        ; keep the original touch-only behaviour.
                        ; Was 18 (~0.3-0.36s) with an INSTANT crack on
                        ; the first touch, so total time-to-destroy
                        ; was ~0.3s - Fausto: "si sgretolano troppo
                        ; velocemente in una fase sola", barely time
                        ; to react. Now BOTH stages (crack, then
                        ; destroy) cost this same wait with no instant
                        ; first crack, so total time-to-destroy while
                        ; standing still is ~2x this, roughly 1.5-1.8s
                        ; at 50-60fps - a real, readable 2-phase
                        ; process instead of a near-instant collapse.
COYOTE_MAX equ 18       ; frames of post-edge jump forgiveness (~0.3-
                        ; 0.36s at 50-60fps). Was 6 (~0.1s) first, but
                        ; a real diagnostic test (walk toward a gap,
                        ; add fire only once already past the edge,
                        ; like a player reacting to seeing the gap
                        ; rather than anticipating it) showed the
                        ; actual keypress landing just 1-2 frames
                        ; PAST a 6-frame window - real human reaction
                        ; time to a visual cue is closer to 200-300ms,
                        ; not 100ms. Widened generously; still short
                        ; enough that a genuine long fall can't be
                        ; rescued (checked against every other room's
                        ; existing jump/fall timing, no regressions).
                        ; enemy patrol lane/surface: per-room, in room_state
MARG    equ 6           ; leading collision margin (symmetric)
MARGT   equ 4           ; transverse half-width
CLMIN   equ 8           ; sprite half-width clamp against room edges
MASKBANK0 equ 4         ; first ASCII8 bank of the mask windows
START_WX equ 24
START_WZ equ 72
LIVES0  equ 5           ; starting lives
AIRMAX  equ 160         ; air units = bar pixels
AIRRATE equ 40          ; frames per air unit (~1.8 min per level)
HUDPAT  equ 1700h       ; pattern VRAM addr of tile row 23
HUDCOL  equ 3700h       ; colour  VRAM addr of tile row 23
LIVCOL  equ 6           ; HUD column of the lives digit
BARCOL  equ 12          ; first HUD column of the AIR bar (20 tiles)

; ---------- title screen / PSG music ----------
TITLE_MIX equ 10111100b ; mixer: ch A+B tone on, ch C off, noise off
GAME_MIX  equ 10111000b ; mixer: ch A+B+C tone on (level music + SFX)
HOPFRAMES equ 8         ; frames per key-hop (one eighth note)
SAM_X   equ 120         ; Sam's fixed dance spot, centred over the keyboard
SAM_Y   equ 107         ; 20px higher than the keyboard-top spot

; PSG tone periods (AY-3-8910, MSX clock 3579545Hz/16), D-major scale
CLK     equ 3579545
P_G3    equ CLK/(16*196)
P_A3    equ CLK/(16*220)
P_B3    equ CLK/(16*247)
P_D3    equ CLK/(16*147)
P_CS4   equ CLK/(16*277)
P_D4    equ CLK/(16*294)
P_E4    equ CLK/(16*330)
P_FS4   equ CLK/(16*370)
P_G4    equ CLK/(16*392)
P_A4    equ CLK/(16*440)
P_B4    equ CLK/(16*494)
P_D5    equ CLK/(16*587)
P_E5    equ CLK/(16*659)
P_FS5   equ CLK/(16*740)
P_G5    equ CLK/(16*784)
P_A5    equ CLK/(16*880)
P_B5    equ CLK/(16*988)
P_D6    equ CLK/(16*1175)
P_GS4   equ CLK/(16*415)

; level (in-game) music note periods - "In the Hall of the Mountain
; King" is in B minor; whole excerpt shifted up one octave from the
; source so every period fits the PSG's 12-bit tone register
P_B1    equ CLK/(16*62)
P_D2    equ CLK/(16*73)
P_FS2   equ CLK/(16*93)
P_A2    equ CLK/(16*110)
P_C3    equ CLK/(16*131)
P_CS3   equ CLK/(16*139)
P_E3    equ CLK/(16*165)
P_F3    equ CLK/(16*175)
P_FS3   equ CLK/(16*185)
P_B2    equ CLK/(16*123)

; bg data (fixed-mapped banks)
BG_PAT  equ 08000h      ; bank 2: pattern 6144 bytes
BG_COL  equ 0A000h      ; bank 3: color   6144 bytes

; ---------- RAM ----------
        MACRO RESB n
        ORG $+n
        ENDM

        ORG 0C000h
ram_start:
frame:      RESB 1
stick:      RESB 1
trig:       RESB 1
trig_prev:  RESB 1
sam_wx:     RESB 1      ; feet center, world x (0..127)
sam_wz:     RESB 1      ; feet center, world z (0..95)
sam_h:      RESB 2      ; feet height 8.8 (floor surface = 8.0)
sam_vy:     RESB 2      ; 8.8 signed, + = up
sam_fl:     RESB 1      ; bit0=grounded bit1=facing left
sam_anim:   RESB 1
keys_got:   RESB 1
level_done: RESB 1
sfx_t:      RESB 1
sfx_freq:   RESB 2
ground_t:   RESB 1
moved:      RESB 1      ; nonzero if moved this frame (anim)
sam_dir:    RESB 1      ; 0=front 1=rear 2=left 3=right
mv_new:     RESB 1      ; candidate coordinate during a move
mask_on:    RESB 1      ; mask sprite active this frame
mask_col:   RESB 1      ; mask sprite color
mk_sum:     RESB 1      ; wx+wz of Sam
mk_sprx:    RESB 1      ; sprite screen x
mk_spry:    RESB 1      ; sprite screen y (top)
mk_lvl:     RESB 1      ; mask depth level
tk_i:       RESB 1      ; key-draw temps
tk_k:       RESB 1
tk_col:     RESB 1
tk_row:     RESB 1
tk_src:     RESB 2
cr_cellst:  RESB 25     ; per-cell crumble states (0 full,1 half,2 gone)
                        ; sized for worst case group*2+cell id across all
                        ; rooms - Room9's 13 solo-cell groups (floor1 +
                        ; step + floor2, every cell but the 2 hazard
                        ; ones) reach id 24, the current high-water mark
cr_prev:    RESB 1      ; cell id Sam is standing on (FF none)
cr_dwell_t: RESB 1      ; frames spent continuously on cr_prev's cell -
                        ; only used when room_crumb_continuous is set;
                        ; reset to 0 whenever cr_prev changes
cb_u:       RESB 1      ; crumble temps
cb_n:       RESB 1
cb_st:      RESB 1
cb_bank:    RESB 1      ; this cell's own crumble bank (read from its
                        ; crumb_tab row) - lets a room's groups span
                        ; more than one 8KB crumble bank
cb_c0:      RESB 1
cb_r0:      RESB 1
cb_c1:      RESB 1
cb_r1:      RESB 1
cb_c:       RESB 1
cb_r:       RESB 1
cb_ph:      RESB 1
cb_src:     RESB 2
cb_ci:      RESB 1
cb_id:      RESB 1
cb_rec:     RESB 2
slabdis:    RESB 12     ; per-slab mask disable flags
en_x:       RESB 1      ; enemy world x
en_dir:     RESB 1      ; 0=+x 1=-x
en_anim:    RESB 1
lift_h:     RESB 1      ; current lift surface height (bounces between
                        ; room_lift_ymin/ymax)
lift_dir:   RESB 1      ; 0=rising(+) 1=falling(-)
on_lift:    RESB 1      ; nonzero while Sam is actually riding it this
                        ; frame (drives the forced-movement push and
                        ; locks sam_h to lift_h instead of the static
                        ; floor_surface scan)
lift_ride_t: RESB 1     ; frames since boarding this ride - the forced
                        ; push only kicks in once this passes a short
                        ; grace period, so a just-boarded player has
                        ; time to notice before being shoved (an
                        ; instant push was shoving people into the
                        ; adjacent cell before they even realized
                        ; they'd boarded - Fausto's own report)
coyote_t:   RESB 1      ; frames since last grounded, capped at
                        ; COYOTE_MAX+1 - lets a jump still trigger for
                        ; a few frames after walking off an edge (see
                        ; the jump-trigger check), matching every
                        ; other platformer's standard "coyote time"
                        ; forgiveness - added after Fausto found that
                        ; walking continuously toward a gap-jump (the
                        ; natural way to approach one) steps off the
                        ; edge and starts falling before there's ever
                        ; a frame where fire can register a fresh
                        ; jump, since the old check required being
                        ; grounded at the EXACT instant fire is
                        ; pressed - needing a frame-perfect stop right
                        ; at the edge, then a separate fresh jump, was
                        ; never a deliberate design, just an
                        ; unforgiving side effect of the strict check.
sfx_step:   RESB 2      ; frequency slide per frame
ex_st:      RESB 1      ; exit blink state (0/16)
lives:      RESB 1
air:        RESB 1      ; remaining air units (bar pixels)
air_t:      RESB 1      ; frame counter for air depletion
; --- title screen / music state ---
mus_mel_ptr: RESB 2     ; melody sequencer read pointer
mus_mel_t:   RESB 1     ; frames left on current melody note
mus_bass_ptr:RESB 2     ; waltz bass sequencer read pointer
mus_bass_t:  RESB 1     ; frames left on current bass note
mtmp0:      RESB 1      ; sequencer scratch (period lo)
mtmp1:      RESB 1      ; sequencer scratch (period hi)
ttl_key_cur: RESB 1     ; piano key index (0-14) currently sounding
ttl_key_prev:RESB 1     ; previous key index, so it can be un-lit
ttl_pose:   RESB 1      ; last blitted Sam pose (0FFh=none yet)
kc_idx:     RESB 1      ; key_set_color scratch
kc_col:     RESB 1
kc_color:   RESB 1
kc_rows:    RESB 1
kc_width:   RESB 1
ttl_blast:  RESB 1      ; last blink state ("PRESS SPACE")
ds_row:     RESB 1      ; draw_string: target tile row
ds_col:     RESB 1      ; draw_string: current tile column
scr_bit:    RESB 1      ; scrolling banner: sub-byte pixel shift (0-7)
scr_byte:   RESB 1      ; scrolling banner: whole-character byte offset
scr_src:    RESB 2      ; scrolling banner: generic src cursor
scr_dst:    RESB 2      ; scrolling banner: generic dst cursor
scr_rowidx: RESB 1      ; scrolling banner: which of the 8 pixel-rows
scb_cnt:    RESB 1      ; scrolling banner: blit tile-column counter
won_t:      RESB 1      ; frames spent in the post-exit victory blink
dbg_bit:    RESB 1      ; debug_room_key scratch
current_room: RESB 1    ; 0=Central Cavern, 1=The Cold Room, ...
; --- room_state: bulk-loaded from room_tab (leveldata.asm) by a single
; ldir in room_start. Field order/sizes MUST match room_tab's rows. ---
room_state:
room_bg_bank:    RESB 1
room_bgcol_bank: RESB 1
room_map_ptr:    RESB 2
room_keys_ptr:   RESB 2
room_nkeys:      RESB 1
room_keysgfx_ptr:RESB 2
room_slab_ptr:   RESB 2
room_nslabs:     RESB 1
room_nunits:     RESB 1
room_crumb_ptr:  RESB 2
room_crumb_bank: RESB 1
room_hazards_ptr:RESB 2
room_nhaz:       RESB 1
room_exit_bx16:  RESB 1
room_exit_bz16:  RESB 1
room_exsurf:     RESB 1
room_exc0:       RESB 1
room_exr0:       RESB 1
room_exnrow:     RESB 1
room_exrowlen:   RESB 1
room_exit_gfx0_ptr: RESB 2
room_exit_gfx1_ptr: RESB 2
room_enemy_gfx_ptr: RESB 2
room_enemy_color:   RESB 1
room_enxmin:     RESB 1
room_enxmax:     RESB 1
room_enz:        RESB 1
room_ensurf:     RESB 1
room_en_axis:    RESB 1  ; 0=horizontal patrol (existing rooms), 1=
                         ; vertical (Eugene's Lair boss) - when 1,
                         ; en_x is reinterpreted as height, bouncing
                         ; between enxmin/enxmax, at the FIXED world
                         ; position (room_enz,room_ensurf) instead of
                         ; the usual (moving-x, fixed room_enz,ensurf).
                         ; 2=mirrored pair (Processing Plant pacmen) -
                         ; en_x is reinterpreted as a HALF-GAP distance
                         ; from room_en_centerx, bouncing between
                         ; enxmin (min gap)/enxmax (max gap); the two
                         ; enemies sit at (centerx-en_x) and
                         ; (centerx+en_x), both at the fixed
                         ; (room_enz,room_ensurf) - approaching each
                         ; other as the gap shrinks, receding as it grows
room_en_centerx: RESB 1  ; only meaningful when room_en_axis=2
room_lift_wx:    RESB 1  ; fixed world x of the rising/falling lift
                         ; platform's centre; 0FFh (never a valid world
                         ; x, MAPW*16=128 max) = no lift in this room
room_lift_wz:    RESB 1  ; fixed world z
room_lift_ymin:  RESB 1  ; lift bounces its surface height between
room_lift_ymax:  RESB 1  ; these two, reversing at each bound
room_name_ptr:   RESB 2
room_crumb_continuous: RESB 1  ; 0=touch-based degrade (original,
                        ; rooms 1/2/3/8): standing still does nothing,
                        ; only a FRESH touch (arriving from a different
                        ; cell) advances one stage. 1=dwell-based
                        ; (Room9): standing still keeps degrading every
                        ; CRUMB_DWELL frames until destroyed - see
                        ; cr_dwell_t.
room_state_end:
NROOMS equ 9
ram_end:

ram_map     equ 0C100h  ; 6*8*8 = 384 bytes  (index = z*64+y*8+x)
mkbuf       equ 0C540h  ; 32-byte occlusion window (OR of overlaps)
mbuf        equ 0C560h  ; 128-byte masked Sam patterns

; ============================================================
;  BANK 0: engine
; ============================================================
        ORG 04000h
        db  "AB"
        dw  init
        dw  0,0,0,0,0,0

init:
        di
        ; enable our slot on page 2 (8000-BFFF)
        call RSLREG
        rrca
        rrca
        and 3
        ld  c,a
        ld  b,0
        ld  hl,EXPTBL
        add hl,bc
        ld  a,(hl)
        and 80h
        or  c
        ld  c,a
        inc hl
        inc hl
        inc hl
        inc hl
        ld  a,(hl)
        rrca
        rrca
        and 3
        rlca
        rlca
        or  c
        ld  h,80h
        call ENASLT
        di

        ; ASCII8 banks 0..3
        xor a
        ld  (BANK0R),a
        inc a
        ld  (BANK1R),a
        inc a
        ld  (BANK2R),a
        inc a
        ld  (BANK3R),a

        ; clear vars
        ld  hl,ram_start
        ld  de,ram_start+1
        ld  bc,ram_end-ram_start-1
        ld  (hl),0
        ldir

        ei
        ld  a,2
        call CHGMOD
        ld  b,11100010b     ; 16x16 sprites
        ld  c,1
        call WRTVDP
        ld  b,001h
        ld  c,7
        call WRTVDP

        ld  a,LIVES0
        ld  (lives),a
        call psg_init
        call title_setup
        jr  title_loop          ; skip over the two routines below -
                                 ; they're subroutines, not fall-through

; ------------------------------------------------------------
; read_stick_any/read_trig_any: keyboard (cursor keys/space) OR
; joystick 1 OR joystick 2 - whichever one is actually being
; used. GTSTCK/GTTRIG device numbers: 0=keyboard, 1=joystick 1,
; 2=joystick 2 (standard MSX BIOS convention).
; ------------------------------------------------------------
read_stick_any:
        xor a
        call GTSTCK
        or  a                   ; 0 = centred/no direction
        ret nz
        ld  a,1
        call GTSTCK
        or  a
        ret nz
        ld  a,2
        jp  GTSTCK

; Only a clean 0FFh ("pressed", the documented GTTRIG convention)
; from any source counts. An unplugged joystick port on this BIOS
; doesn't reliably read back as a clean 0 when idle, so a plain
; OR-together falsely reads as "pressed" - checking for the exact
; pressed value instead of just "non-zero" avoids that.
read_trig_any:
        xor a
        call GTTRIG
        cp  0FFh
        jr  z,.pressed
        ld  a,1
        call GTTRIG
        cp  0FFh
        jr  z,.pressed
        ld  a,2
        call GTTRIG
        cp  0FFh
        jr  z,.pressed
        xor a
        ret
.pressed:
        ld  a,0FFh
        ret

; ------------------------------------------------------------
; debug_room_key: scans keyboard matrix rows 2-5 (the letter keys) for
; a pressed letter. A=room0/Central Cavern, B=room1/The Cold Room, etc,
; clamped to the rooms that actually exist. Returns A=0FFh
; (current_room set) if one was found, else 0. Not documented anywhere
; on purpose - debug/dev shortcut only.
; Real MSX matrix (confirmed against https://map.grauw.nl/articles/
; keymatrix.php - the row2=@ABCDEFG layout an earlier pass assumed was
; wrong, which is why this silently didn't respond to real key presses):
;   row2: bit7=B bit6=A bit5..0=symbols (only 2 letters in this row)
;   row3: bit0=C bit1=D bit2=E bit3=F bit4=G bit5=H bit6=I bit7=J
;   row4: bit0=K ... bit7=R          row5: bit0=S ... bit7=Z
; ------------------------------------------------------------
row_bases: db 0FAh, 2, 10, 18   ; room index = row_bases[row-2] + bitpos
                                 ; (0FAh=-6, so row2 bit6/7 -> 0/1='A'/'B';
                                 ; bit0-5 wrap past NROOMS and are ignored)

debug_room_key:
        ld  e,0
.rowlp: ld  a,e
        add a,2
        call SNSMAT
        cpl
        ld  d,a
        xor a
        ld  (dbg_bit),a
        ld  b,8
.bitlp: srl d
        jr  nc,.next
        ld  hl,row_bases
        ld  a,e
        add a,l
        ld  l,a
        jr  nc,.noc
        inc h
.noc:   ld  a,(hl)
        ld  hl,dbg_bit
        add a,(hl)
        cp  NROOMS
        jr  nc,.next
        ld  (current_room),a
        ld  a,0FFh
        ret
.next:  ld  hl,dbg_bit
        inc (hl)
        djnz .bitlp
        inc e
        ld  a,e
        cp  4
        jr  nz,.rowlp
        xor a
        ret

title_loop:
        halt
        ld  hl,frame
        inc (hl)
        call music_update
        call title_sam_draw
        call title_blink
        ld  a,(frame)
        and 3
        call z,scroll_update    ; 1 in 4 frames - still reads as a
                                 ; smooth scroll, just costs a lot
                                 ; less than doing it every frame
        call debug_room_key
        or  a
        jr  nz,.go              ; letter pressed - current_room already set
        call read_trig_any
        or  a
        jr  z,title_loop
        xor a
        ld  (current_room),a
.go:    call music_stop
        call psg_init
        call room_enter
        jp  main_loop

; ------------------------------------------------------------
; room_start: (re)enter the level: fresh state except lives
; ------------------------------------------------------------
room_start:
        ld  a,(lives)
        ex  af,af'
        ld  a,(current_room)
        push af
        ld  hl,ram_start
        ld  de,ram_start+1
        ld  bc,ram_end-ram_start-1
        ld  (hl),0
        ldir
        pop af
        ld  (current_room),a
        ex  af,af'
        ld  (lives),a
        ld  a,0FFh
        ld  (cr_prev),a
        ld  a,AIRMAX
        ld  (air),a
        ; load this room's descriptor row: hl = room_tab + current_room*
        ; ROOMROWLEN, via repeated addition (current_room is always
        ; small) - deliberately NOT hand-tuned shifts: those silently
        ; go stale every time a field is added and ROOMROWLEN grows,
        ; which has already happened twice.
        ld  a,(current_room)
        ld  b,a
        ld  hl,0
        ld  de,ROOMROWLEN
.rowmul:ld  a,b
        or  a
        jr  z,.rowmuldone
        add hl,de
        dec b
        jr  .rowmul
.rowmuldone:
        ld  de,room_tab
        add hl,de
        ld  de,room_state
        ld  bc,ROOMROWLEN
        ldir
        ; select this room's background/colour ROM banks
        ld  a,(room_bg_bank)
        ld  (BANK2R),a
        ld  a,(room_bgcol_bank)
        ld  (BANK3R),a
        ld  a,(room_enxmin)
        ld  (en_x),a
        ld  a,(room_lift_ymin)
        ld  (lift_h),a
        call load_room
        call sam_init
        call level_music_init
        jp  hud_init

; ------------------------------------------------------------
; room_enter: room_start + the ~2s name-card intro. Used only when
; entering a room for the FIRST time (title -> room 1, room 1 -> room
; 2); sam_die's respawn calls room_start directly so the card doesn't
; replay on death.
; ------------------------------------------------------------
room_enter:
        call room_start
        jp  room_intro

; ------------------------------------------------------------
; room_intro: hide any leftover sprites, show the room's name
; centred on tile row 11 for ~100 frames (still ticking the level
; music), then erase it by restoring that row from BG_PAT/BG_COL -
; same restore trick key pickups use, just for a whole tile row.
; ------------------------------------------------------------
room_intro:
        ld  hl,VR_SPRA          ; hide title-screen/previous-room sprites
        ld  a,208
        call WRTVRM

        ld  hl,(room_name_ptr)
        ld  b,0
.slen:  ld  a,(hl)
        or  a
        jr  z,.gotlen
        inc hl
        inc b
        jr  .slen
.gotlen:
        ld  a,32
        sub b
        srl a
        ld  (ds_col),a
        ld  a,11
        ld  (ds_row),a

        ; solid black backdrop, 2 cols padding either side, 3 tile
        ; rows tall - drawn BEFORE the text so spaces inside the name
        ; (and the margin around it) read as a clean box instead of
        ; showing raw level background through them
        ld  a,(ds_col)
        sub 2
        ld  c,a                 ; box_col0
        ld  a,b
        add a,4
        ld  b,a                 ; box width in columns
        ld  a,10
        call box_row
        ld  a,11
        call box_row
        ld  a,12
        call box_row

        ld  hl,(room_name_ptr)
        call draw_string

        ld  b,100
.hold:  push bc
        halt
        ld  hl,frame
        inc (hl)
        call level_music_update
        pop bc
        djnz .hold

        ld  hl,BG_PAT+10*256
        ld  de,VR_PAT+10*256
        ld  bc,768              ; 3 rows (10,11,12) x 256 bytes
        call LDIRVM
        ld  hl,BG_COL+10*256
        ld  de,VR_COL+10*256
        ld  bc,768
        call LDIRVM
        ; the row restore above uses the keyless base background, so
        ; any pickups load_room already drew that fall within rows
        ; 10-12 need to be put back
        jp  key_draw_all

; box_row: A=tile row, B=width(cols), C=col0 -> fill pattern=0/colour=011h
; (solid black - the box backdrop behind a room-name card)
box_row:
        push bc
        ld  h,a
        ld  l,0
        ld  a,c
        add a,a
        add a,a
        add a,a
        ld  e,a
        ld  d,0
        add hl,de               ; hl = row*256 + col0*8
        ld  a,b
        add a,a
        add a,a
        add a,a
        ld  e,a
        ld  d,0                 ; de = width*8 (byte count)
        push hl
        push de
        ld  bc,VR_PAT
        add hl,bc
        pop bc
        push bc
        xor a
        call vram_fill
        pop bc
        pop hl
        ld  de,VR_COL
        add hl,de
        ld  a,011h
        call vram_fill
        pop bc
        ret

; ------------------------------------------------------------
; sam_die: lose a life, restart the room (0 lives -> fresh game)
; ------------------------------------------------------------
sam_die:
        ld  a,(lives)
        dec a
        jr  nz,.ok
        ; game over: show the message, then bail out to the title
        ; screen instead of respawning. sam_die is always reached via
        ; a tail `jp` from enemy_update/hazard_check/air_update (each
        ; itself `call`ed once from main_loop), so exactly one stale
        ; return address is on the stack - discard it before leaving
        ; main_loop's per-frame call chain for good.
        ld  a,LIVES0
        ld  (lives),a
        pop hl
        call game_over_screen
        call title_setup
        jp  title_loop
.ok:    ld  (lives),a
        call room_start
        ; death jingle: low rising-period slide
        ld  a,30
        ld  (sfx_t),a
        ld  hl,0040h
        ld  (sfx_freq),hl
        ld  hl,12
        ld  (sfx_step),hl
        ret

; ------------------------------------------------------------
; game_over_screen: silence the level music, hide sprites, show
; "GAME OVER" boxed on tile row 11 for ~3s. No restore needed - the
; caller goes straight into title_setup, which redraws the whole
; screen anyway.
; ------------------------------------------------------------
game_over_str: db "GAME OVER",0

game_over_screen:
        call music_stop
        ld  hl,VR_SPRA
        ld  a,208
        call WRTVRM

        ld  a,32
        sub 9                    ; strlen("GAME OVER")
        srl a
        ld  (ds_col),a
        ld  a,11
        ld  (ds_row),a

        ld  a,(ds_col)
        sub 2
        ld  c,a
        ld  b,13                 ; 9 + 4 cols padding
        ld  a,10
        call box_row
        ld  a,11
        call box_row
        ld  a,12
        call box_row

        ld  hl,game_over_str
        call draw_string

        ld  b,150                ; ~3s
.hold:  push bc
        halt
        ld  hl,frame
        inc (hl)
        pop bc
        djnz .hold
        ret

main_loop:
        halt
        ld  hl,frame
        inc (hl)
        call read_stick_any
        ld  (stick),a
        ld  a,(trig)
        ld  (trig_prev),a
        call read_trig_any
        ld  (trig),a

        ld  a,(level_done)
        or  a
        jr  nz,.won
        call lift_update
        call sam_update
        call enemy_update
        call hazard_check
        call exit_check
        call air_update
        call sam_draw
        call door_fx
        call sfx_update
        call level_music_update
        jr  main_loop
.won:
        ld  a,(frame)
        rrca
        rrca
        and 1
        jr  z,.w1
        ld  b,15
        jr  .w2
.w1:    ld  b,7
.w2:    ld  c,7
        call WRTVDP
        call sfx_update
        call level_music_update

        ld  hl,won_t
        inc (hl)
        ld  a,(hl)
        cp  120                 ; ~2.4s of blinking before advancing
        jr  c,main_loop
        ld  a,(current_room)
        inc a
        cp  NROOMS
        jr  nc,main_loop        ; already on the last room: keep blinking
        ld  (current_room),a
        call room_enter
        jr  main_loop

; ------------------------------------------------------------
; load_room: name=identity, copy bg pattern+color, sprites, map
; ------------------------------------------------------------
load_room:
        ; name table = 0..255 x3 (bitmap mode)
        ld  hl,VR_NAME
        call SETWRT
        ld  c,3
.nt3:   xor a
.ntl:   out (098h),a
        nop
        nop
        inc a
        jr  nz,.ntl
        dec c
        jr  nz,.nt3

        ; background image
        ld  hl,BG_PAT
        ld  de,VR_PAT
        ld  bc,6144
        call LDIRVM
        ld  hl,BG_COL
        ld  de,VR_COL
        ld  bc,6144
        call LDIRVM

        ; enemy: 2 frames at sprite patterns 0 and 4
        ld  hl,(room_enemy_gfx_ptr)
        ld  de,VR_SPRP
        ld  bc,64
        call LDIRVM

        ; lift platform: 2 halves (left/right) at sprite patterns 8/12 -
        ; a single fixed design, not per-room (only unused when a room
        ; has no lift, room_lift_wx=0FFh skips ever drawing it)
        ld  hl,lift_gfx
        ld  de,VR_SPRP+8*8
        ld  bc,64
        call LDIRVM

        ; map ROM -> RAM
        ld  hl,(room_map_ptr)
        ld  de,ram_map
        ld  bc,MAPW*MAPH*MAPD
        ldir
        call key_draw_all
        ret

; ------------------------------------------------------------
; key_draw_all: draw every key's 2x2 chars from keys_gfx
; ------------------------------------------------------------
key_draw_all:
        xor a
        ld  (tk_i),a
.loop:  ; tab entry ptr = keys_tab + i*5 (+0,1,2 -> bx,bz,y; +3,4 -> ccol,crow)
        ld  a,(tk_i)
        ld  e,a
        add a,a
        add a,a
        add a,e             ; i*5
        ld  e,a
        ld  d,0
        ld  hl,(room_keys_ptr)
        add hl,de
        ld  b,(hl)          ; bx
        inc hl
        ld  d,(hl)          ; bz
        inc hl
        ld  c,(hl)          ; y (celly)
        inc hl              ; hl -> ccol
        push hl
        call map_at         ; tile already cleared (collected) -> skip redraw
        pop hl
        cp  T_KEY
        jr  nz,.nextkey
        ld  a,(hl)
        ld  (tk_col),a
        inc hl
        ld  a,(hl)
        ld  (tk_row),a
        ; src = keys_gfx + i*64
        ld  a,(tk_i)
        ld  l,a
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl           ; *64
        ld  de,(room_keysgfx_ptr)
        add hl,de
        ld  (tk_src),hl
        xor a
        ld  (tk_k),a
.ch:    ; off = (row + k/2)*256 + (col + k%2)*8
        ld  a,(tk_k)
        srl a
        ld  d,a
        ld  a,(tk_row)
        add a,d
        ld  d,a
        ld  a,(tk_k)
        and 1
        ld  e,a
        ld  a,(tk_col)
        add a,e
        add a,a
        add a,a
        add a,a
        ld  e,a             ; de = VRAM offset
        ; pattern: src + k*8
        ld  a,(tk_k)
        add a,a
        add a,a
        add a,a
        ld  c,a
        ld  b,0
        ld  hl,(tk_src)
        add hl,bc
        push de
        push hl
        ld  bc,8
        call LDIRVM
        pop hl
        pop de
        ; color: src + 32 + k*8 -> VRAM 2000h+off
        ld  bc,32
        add hl,bc
        ld  a,d
        add a,020h
        ld  d,a
        ld  bc,8
        call LDIRVM
        ; next char
        ld  a,(tk_k)
        inc a
        ld  (tk_k),a
        cp  4
        jr  nz,.ch
.nextkey:
        ld  a,(tk_i)
        inc a
        ld  (tk_i),a
        ld  b,a
        ld  a,(room_nkeys)
        cp  b
        jp  nz,.loop
        ret

; ------------------------------------------------------------
; map_at: A = tile at B=x C=y D=z    addr = ram_map + z*64+y*8+x
; ------------------------------------------------------------
map_at:
        ld  a,b
        cp  MAPW
        jr  nc,.out
        ld  a,c
        cp  MAPH
        jr  nc,.out         ; above the room = empty
        ld  a,d
        cp  MAPD
        jr  nc,.out
        push hl
        push de
        call map_addr
        ld  a,(hl)
        pop de
        pop hl
        ret
.out:   xor a
        ret

map_addr:                   ; HL = &ram_map[z][y][x]
        push bc
        ld  l,d
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl           ; z*64
        ld  a,c
        add a,a
        add a,a
        add a,a             ; y*8
        add a,b             ; +x  (y*8+x <= 63, no carry)
        ld  c,a
        ld  b,0
        add hl,bc
        ld  bc,ram_map
        add hl,bc
        pop bc
        ret

; ------------------------------------------------------------
; sam_init
; ------------------------------------------------------------
sam_init:
        ld  a,START_WX
        ld  (sam_wx),a
        ld  a,START_WZ
        ld  (sam_wz),a
        ld  hl,0800h
        ld  (sam_h),hl
        ld  hl,0
        ld  (sam_vy),hl
        ld  a,1
        ld  (sam_fl),a
        ret

; ------------------------------------------------------------
; floor_surface: A = highest solid surface <= C(feet px) at B=x D=z
;                E = tile type; A=0 if pit
; ------------------------------------------------------------
floor_surface:
        push bc
        ld  e,0
        ld  a,c
        srl a
        srl a
        srl a               ; start at feet/8 (catches fast falls
        cp  MAPH            ;  that sink into the slab)
        jr  c,.y0
        ld  a,MAPH-1
.y0:    ld  c,a
.scan:  push de
        call map_at
        pop de
        or  a
        jr  z,.lower
        cp  T_CRUMB+1
        jr  nc,.lower
        ld  e,a
        ld  a,c
        inc a
        add a,a
        add a,a
        add a,a
        pop bc
        ret
.lower: ld  a,c
        or  a
        jr  z,.none
        dec c
        jr  .scan
.none:  xor a
        pop bc
        ret

; ------------------------------------------------------------
; sam_update
; ------------------------------------------------------------
dxtab:  db 0, 0, 1, 1, 1, 0,-1,-1,-1   ; stick 0..8
dztab:  db 0,-1,-1, 0, 1, 1, 1, 0,-1

sam_update:
        xor a
        ld  (moved),a

        ; ---- directional movement (iso axes) ----
        ld  a,(stick)
        ld  e,a
        ld  d,0
        ld  hl,dxtab
        add hl,de
        ld  a,(hl)
        or  a
        jr  z,.nodx
        call move_x
.nodx:  ld  a,(stick)       ; reload index (move_x clobbers DE)
        ld  e,a
        ld  d,0
        ld  hl,dztab
        add hl,de
        ld  a,(hl)
        or  a
        jr  z,.nodz
        call move_z
.nodz:

        ; ---- conveyor drag (+x) ----
        ld  a,(sam_fl)
        bit 0,a
        jr  z,.noconv
        ld  a,(ground_t)
        cp  T_CONV
        jr  nz,.noconv
        ld  a,(frame)
        and 1
        jr  nz,.noconv
        ld  a,1
        call move_x
.noconv:

        ; ---- lift forced-movement push (+x), same cadence as the
        ; conveyor drag above - if Sam doesn't counter it while riding
        ; the rising/falling lift, he's pushed off its footprint and
        ; falls (no static floor under the lift's own shaft). A short
        ; grace period after boarding (GRACE_FRAMES) delays the push
        ; itself, so a just-boarded player has a moment to notice
        ; before being shoved - an instant push was shoving people
        ; into the adjacent cell before they even realized they'd
        ; boarded, which then never re-catches since the lift no
        ; longer shares that cell (Fausto's own report, "non riesco a
        ; salire sulla piattaforma"). ----
        ld  a,(sam_fl)
        bit 0,a
        jr  z,.nolift
        ld  a,(on_lift)
        or  a
        jr  z,.nolift
        ld  a,(lift_ride_t)
        cp  200
        jr  nc,.noinc
        inc a
        ld  (lift_ride_t),a
.noinc: cp  GRACE_FRAMES
        jr  c,.nolift
        ld  a,(frame)
        and 1
        jr  nz,.nolift
        ld  a,1
        call move_x
.nolift:

        ; ---- coyote time bookkeeping: 0 while grounded, otherwise
        ; counts frames since the last grounded frame (capped) ----
        ld  a,(sam_fl)
        bit 0,a
        jr  z,.coyinc
        xor a
        ld  (coyote_t),a
        jr  .coydone
.coyinc: ld  a,(coyote_t)
        cp  COYOTE_MAX+1
        jr  nc,.coydone
        inc a
        ld  (coyote_t),a
.coydone:

        ; ---- jump ---- (grounded OR still within the coyote window)
        ld  a,(sam_fl)
        bit 0,a
        jr  nz,.jumpok
        ld  a,(coyote_t)
        cp  COYOTE_MAX+1
        jr  nc,.phys
.jumpok:
        ld  a,(trig)
        or  a
        jr  z,.phys
        ld  a,(trig_prev)
        or  a
        jr  nz,.phys
        ld  hl,JUMPV
        ld  (sam_vy),hl
        ld  a,(sam_fl)
        res 0,a
        ld  (sam_fl),a
        ld  a,COYOTE_MAX+1
        ld  (coyote_t),a    ; consumed - block a second coyote jump
                            ; before the next real landing
        ld  a,20
        ld  (sfx_t),a
        ld  hl,0100h
        ld  (sfx_freq),hl
        ld  hl,-4
        ld  (sfx_step),hl

.phys:  ld  a,(sam_fl)
        bit 0,a
        jp  nz,.grounded
        ; airborne
        ld  hl,(sam_h)
        ld  de,(sam_vy)
        add hl,de
        ld  (sam_h),hl
        ld  hl,(sam_vy)
        ld  de,-GRAV
        add hl,de
        ld  (sam_vy),hl
        bit 7,h
        jr  nz,.faller
        ; rising: head bump against a solid cell above
        ld  a,(sam_h+1)
        add a,15            ; top pixel of Sam's 16px body
        srl a
        srl a
        srl a
        cp  MAPH
        jp  nc,.chkpit
        ld  c,a             ; head cell y
        ld  a,(sam_wx)
        srl a
        srl a
        srl a
        srl a
        ld  b,a
        ld  a,(sam_wz)
        srl a
        srl a
        srl a
        srl a
        ld  d,a
        call map_at
        or  a
        jp  z,.chkpit
        cp  T_CRUMB+1
        jp  nc,.chkpit
        ; bonk: clamp feet just below the cell, start falling
        ld  a,c
        add a,a
        add a,a
        add a,a
        sub 16
        ld  (sam_h+1),a
        xor a
        ld  (sam_h),a
        ld  hl,0
        ld  (sam_vy),hl
        jp  .chkpit
.faller:
        call lift_land_check
        or  a
        jp  nz,.chkpit
        call get_fs
        ld  b,a
        ld  a,(sam_h+1)
        cp  b
        jp  nc,.chkpit
        ; land
        ld  a,b
        ld  (sam_h+1),a
        xor a
        ld  (sam_h),a
        ld  hl,0
        ld  (sam_vy),hl
        ld  a,(sam_fl)
        set 0,a
        ld  (sam_fl),a
        ld  a,e
        ld  (ground_t),a
        jp  .chkpit
.grounded:
        call lift_ride_check
        or  a
        jp  nz,.chkpit
        call get_fs
        ld  b,a
        ld  a,e
        ld  (ground_t),a
        ld  a,(sam_h+1)
        cp  b
        jp  z,.chkpit
        ld  a,(sam_fl)
        res 0,a
        ld  (sam_fl),a
        ld  hl,0
        ld  (sam_vy),hl

.chkpit:
        ld  a,(sam_fl)
        bit 0,a
        jr  nz,.crumb
        ld  a,(sam_h+1)
        or  a
        jr  z,.resp
        bit 7,a
        jr  z,.crumb
.resp:  call sam_die

        ; ---- crumble erosion: each fresh touch degrades one stage ----
        ; (not a sustained-standing timer: that made jump-bouncing on a
        ; unit never break it, since every landing reset the clock -
        ; a single touch/landing now advances it immediately instead)
.crumb: ld  a,(sam_fl)
        bit 0,a
        jr  z,.crair
        call get_fs
        or  a
        jr  z,.crd
        srl a
        srl a
        srl a
        dec a
        ld  c,a             ; slab cell y
        ld  a,(sam_wx)
        srl a
        srl a
        srl a
        srl a
        ld  b,a
        ld  a,(sam_wz)
        srl a
        srl a
        srl a
        srl a
        ld  d,a
        call cell_at
        ld  e,a
        ld  a,(cr_prev)
        cp  e
        jr  nz,.crnew       ; arrived on a different cell than last frame
        ; same cell as last frame - touch-only rooms ignore this
        ; entirely; dwell-based rooms (room_crumb_continuous=1) keep
        ; degrading the longer Sam stands still on it
        ld  a,(room_crumb_continuous)
        or  a
        jr  z,.crd
        ld  a,e
        cp  0FFh
        jr  z,.crd          ; standing on solid ground
        ld  hl,cr_dwell_t
        inc (hl)
        ld  a,(hl)
        cp  CRUMB_DWELL
        jr  c,.crd          ; not dwelt long enough yet
        xor a
        ld  (hl),a          ; reset dwell timer, degrade one more stage
        ld  a,e
        call degrade_cell
        jr  .crd
.crnew: ld  a,e
        ld  (cr_prev),a
        xor a
        ld  (cr_dwell_t),a  ; fresh arrival always resets the dwell clock
        ld  a,e
        cp  0FFh
        jr  z,.crd          ; stepped onto solid/non-crumbling ground
        ld  a,(room_crumb_continuous)
        or  a
        jr  nz,.crd         ; dwell-based rooms: a touch alone doesn't
                            ; crack it - both stages now cost the same
                            ; CRUMB_DWELL wait, so standing still reads
                            ; as one smooth process instead of an
                            ; instant crack followed by a fast kill
                            ; (Fausto: "si sgretolano troppo
                            ; velocemente in una fase sola")
        ld  a,e
        call degrade_cell   ; touch-based rooms (1/3/8): fresh touch
                            ; still advances one stage instantly, as
                            ; always
        jr  .crd
.crair: ld  a,0FFh
        ld  (cr_prev),a
.crd:

.items: ld  a,(sam_wx)
        srl a
        srl a
        srl a
        srl a
        ld  b,a
        ld  a,(sam_h+1)
        srl a
        srl a
        srl a
        ld  c,a
        ld  a,(sam_wz)
        srl a
        srl a
        srl a
        srl a
        ld  d,a
        call map_at
        cp  T_KEY
        jr  z,.pick
        ret
.pick:  call key_erase
        ld  a,(keys_got)
        inc a
        ld  (keys_got),a
        ld  a,12
        ld  (sfx_t),a
        ld  hl,0050h
        ld  (sfx_freq),hl
        ld  hl,-4
        ld  (sfx_step),hl
        ret

; ------------------------------------------------------------
; hazard_check: deadly bushes - die when Sam's feet cell matches
; a bush cell and his feet are within [floor,ceiling) of that bush.
; A ground-level bush (floor=0) is deadly to anything below the
; ceiling, same as always; a platform-TOP hazard sets floor==its own
; surf so the kill zone doesn't extend all the way down through open
; ground below that column too (real bug: it used to, since this was
; ceiling-only - Fausto died walking under a hazard-marked platform
; cell, nowhere near the hazard's visible sprite).
; ------------------------------------------------------------
hazard_check:
        ld  a,(sam_wx)
        srl a
        srl a
        srl a
        srl a
        ld  d,a             ; cell x
        ld  a,(sam_wz)
        srl a
        srl a
        srl a
        srl a
        ld  e,a             ; cell z
        ld  hl,(room_hazards_ptr)
        ld  a,(room_nhaz)
        or  a
        ret z
        ld  b,a
.lp:    ld  a,(hl)
        inc hl
        cp  d
        jr  nz,.n1
        ld  a,(hl)
        cp  e
        jr  nz,.n1
        inc hl
        ld  a,(sam_h+1)
        cp  (hl)
        jr  c,.n2           ; feet below the hazard's floor: safe
        inc hl
        ld  a,(sam_h+1)
        cp  (hl)
        jr  nc,.n4          ; feet at/above kill ceiling: safe
        jp  sam_die
.n1:    inc hl
        inc hl
        jr  .n3
.n2:    inc hl
.n4:
.n3:    inc hl
        djnz .lp
        ret

; ------------------------------------------------------------
; exit_check: standing on top of the exit cube with all keys
; -> level complete (only reachable by jumping in from above)
; ------------------------------------------------------------
exit_check:
        ld  a,(room_nkeys)
        ld  b,a
        ld  a,(keys_got)
        cp  b
        ret c               ; keys_got < room_nkeys -> not enough yet
        ld  hl,(sam_vy)
        ld  a,h
        or  l
        ret nz              ; must be settled (grounded)
        ld  a,(sam_h+1)
        ld  b,a
        ld  a,(room_exsurf)
        cp  b
        ret nz
        ld  a,(sam_wx)
        and 0F0h
        ld  b,a
        ld  a,(room_exit_bx16)
        cp  b
        ret nz
        ld  a,(sam_wz)
        and 0F0h
        ld  b,a
        ld  a,(room_exit_bz16)
        cp  b
        ret nz
        ld  a,1
        ld  (level_done),a
        ret

; ------------------------------------------------------------
; move_x / move_z: A = +1/-1 delta on that axis, with clamps
; and solid-block check at the destination column
; ------------------------------------------------------------
; edge-based collision, two checks per move:
;  1) BODY cells (feet, torso) at the directional edge: ground-level
;     obstacles use asymmetric margins (tuck in from the far side,
;     stop early from the near side)
;  2) HEAD-CLEARANCE cell (+2) at the tight edge: floating slabs
;     block passage but Sam can walk right up under their rim
move_x:
        ld  c,a
        ; facing: +x = right(3), -x = left(2)
        bit 7,a
        ld  a,3
        jr  z,.fx
        ld  a,2
.fx:    ld  (sam_dir),a
        ld  a,(sam_wx)
        add a,c
        cp  CLMIN
        ret c
        cp  MAPW*16-CLMIN+1
        ret nc
        ld  (mv_new),a
        ; centre-lane leading edge: HARD block, never bypassed
        call xhard
        ret nz
        ; transverse corners: soft (escape allowed if already inside)
        ld  a,(mv_new)
        call xsoft
        jr  z,.ok
        ld  a,(sam_wx)
        call xsoft
        ret z               ; current clear -> refuse
.ok:    ld  a,(mv_new)
        ld  (sam_wx),a
        ld  a,1
        ld  (moved),a
        ret

; xhard: leading-edge column at Sam's centre lane (A=cand wx in mv_new)
xhard:
        ld  a,(mv_new)
        call xedge
        ld  b,a
        ld  a,(sam_wz)
        srl a
        srl a
        srl a
        srl a
        ld  d,a
        jp  cells_body

; xsoft: leading-edge column at the two corner lanes (A = coordinate)
xsoft:
        call xedge
        ld  b,a
        ld  a,(sam_wz)
        sub MARGT
        srl a
        srl a
        srl a
        srl a
        ld  d,a
        push bc
        call cells_body
        pop bc
        ret nz
        ld  a,(sam_wz)
        add a,MARGT
        srl a
        srl a
        srl a
        srl a
        ld  d,a
        jp  cells_body

; xedge: A = coordinate -> A = leading-edge block column
xedge:
        ld  e,a
        ld  a,(sam_dir)
        cp  3
        ld  a,e
        jr  nz,.n
        add a,MARG
        jr  .e
.n:     sub MARG
        jr  nc,.e
        xor a
.e:     srl a
        srl a
        srl a
        srl a
        ret

move_z:
        ld  c,a
        ; facing: +z = front(0), -z = rear(1)
        bit 7,a
        ld  a,0
        jr  z,.fz
        inc a
.fz:    ld  (sam_dir),a
        ld  a,(sam_wz)
        add a,c
        cp  CLMIN
        ret c
        cp  MAPD*16-CLMIN+1
        ret nc
        ld  (mv_new),a
        call zhard
        ret nz
        ld  a,(mv_new)
        call zsoft
        jr  z,.ok
        ld  a,(sam_wz)
        call zsoft
        ret z
.ok:    ld  a,(mv_new)
        ld  (sam_wz),a
        ld  a,1
        ld  (moved),a
        ret

zhard:
        ld  a,(mv_new)
        call zedge
        ld  d,a
        ld  a,(sam_wx)
        srl a
        srl a
        srl a
        srl a
        ld  b,a
        jp  cells_body

zsoft:
        call zedge
        ld  d,a
        ld  a,(sam_wx)
        sub MARGT
        srl a
        srl a
        srl a
        srl a
        ld  b,a
        push de
        call cells_body
        pop de
        ret nz
        ld  a,(sam_wx)
        add a,MARGT
        srl a
        srl a
        srl a
        srl a
        ld  b,a
        jp  cells_body

; zedge: A = coordinate -> A = leading-edge block row
zedge:
        ld  e,a
        ld  a,(sam_dir)
        or  a               ; 0 = front = +z
        ld  a,e
        jr  nz,.n
        add a,MARG
        jr  .e
.n:     sub MARG
        jr  nc,.e
        xor a
.e:     srl a
        srl a
        srl a
        srl a
        ret

; cells_body: NZ if feet or torso cell solid at B=x D=z
; (16px of clearance suffice: Sam can slip under taller platforms)
cells_body:
        ld  a,(sam_h+1)
        srl a
        srl a
        srl a
        ld  c,a
        push bc
        call map_at
        call solid_q
        pop bc
        ret nz
        inc c
        call map_at
        call solid_q
        ret

solid_q:                    ; NZ if solid (1..3)
        or  a
        ret z
        cp  T_CRUMB+1
        jr  c,.s
        xor a
        ret
.s:     or  1
        ret

; ------------------------------------------------------------
; get_fs: A = floor surface at Sam's column, E = tile
; ------------------------------------------------------------
get_fs:
        ld  a,(sam_wx)
        srl a
        srl a
        srl a
        srl a
        ld  b,a
        ld  a,(sam_wz)
        srl a
        srl a
        srl a
        srl a
        ld  d,a
        ld  a,(sam_h+1)
        ld  c,a
        call floor_surface
        ret

; ------------------------------------------------------------
; lift: a rising/falling platform riding a fixed (room_lift_wx,
; room_lift_wz) column, bouncing its surface height between
; room_lift_ymin/ymax. Not part of the static map at all (the shaft
; it rides is otherwise open air) - handled as a special case injected
; into sam_update's existing landing/grounded checks instead.
; LIFT_GT is a synthetic ground_t value (no real tile uses 8) so the
; forced-push block in sam_update can tell "standing on the lift" apart
; from every real floor tile.
; ------------------------------------------------------------
LIFT_GT equ 8
BOARD_TOL equ 24   ; boarding-from-the-ground height tolerance in px -
                    ; the lift is a moving target, so this needs to be
                    ; wide enough to give a real multi-frame catch
                    ; window each time it swings back down near
                    ; standing height, not an exact match
GRACE_FRAMES equ 25 ; frames after boarding before the forced push
                    ; starts (~0.5s) - gives a just-boarded player time
                    ; to notice before being shoved

; lift_in_footprint: A=1 if Sam's (wx,wz) is in the SAME GRID CELL as
; the lift (and a lift actually exists in this room), else A=0. Uses
; the exact-cell convention every other environmental check in this
; game already uses (hazard_check, key pickup) rather than a bespoke
; pixel-radius box - a player has no way to see an arbitrary sub-cell
; catch zone, but "stand in the lift's cell" matches how every other
; interactive tile in the game already works, and gives a full 16x16
; window instead of a much smaller one (an earlier draft's tighter
; radius made boarding from a standstill feel broken - Fausto's own
; report, "continuo a non riuscire a salirci").
lift_in_footprint:
        ld  a,(room_lift_wx)
        cp  0FFh
        jr  z,.no
        srl a
        srl a
        srl a
        srl a
        ld  b,a
        ld  a,(sam_wx)
        srl a
        srl a
        srl a
        srl a
        cp  b
        jr  nz,.no
        ld  a,(room_lift_wz)
        srl a
        srl a
        srl a
        srl a
        ld  b,a
        ld  a,(sam_wz)
        srl a
        srl a
        srl a
        srl a
        cp  b
        jr  nz,.no
        ld  a,1
        ret
.no:    xor a
        ret

; lift_land_check: called only while airborne+falling. Lands Sam on
; the lift (grounded, height synced, on_lift=1) if he's within its
; footprint and has fallen to/below its current surface; returns A=1
; when handled (caller skips the normal static-floor landing check
; this frame), A=0 otherwise (normal check runs, e.g. for the real
; floor far below the lift's own open shaft).
lift_land_check:
        call lift_in_footprint
        or  a
        ret  z
        ld  a,(lift_h)
        ld  b,a
        ld  a,(sam_h+1)
        cp  b
        jr  nc,.no2         ; still above the lift - keep falling
        ld  a,b
        ld  (sam_h+1),a
        xor a
        ld  (sam_h),a
        ld  hl,0
        ld  (sam_vy),hl
        ld  a,(sam_fl)
        set 0,a
        ld  (sam_fl),a
        ld  a,LIFT_GT
        ld  (ground_t),a
        ld  a,1
        ld  (on_lift),a
        xor a
        ld  (lift_ride_t),a     ; fresh board - grace period restarts
        ld  a,1
        ret
.no2:   xor a
        ret

; lift_ride_check: called only while grounded. Two cases both return
; A=1 (handled, sam_h synced to lift_h, ground_t=LIFT_GT, on_lift=1):
; (1) was already riding (on_lift!=0) and is still within the lift's
; footprint - keeps tracking its moving height unconditionally, or
; (2) wasn't riding yet but just walked into the footprint at a height
; already CLOSE to the lift's current surface (boarding it from
; adjacent floor, not falling onto it - that's lift_land_check's job).
; Case 2 uses a tolerance (BOARD_TOL), not exact equality: the lift is
; a moving target that bounces 1px every other frame, so it only
; passes through any exact height for 1-2 real frames per cycle -
; requiring an exact match made boarding it while standing still
; practically un-timeable for a real player (found via Fausto's own
; playtesting - "non riesco a salire sulla piattaforma"). A tolerance
; gives a real multi-frame window each time the lift swings back down
; near standing height, while still small enough that merely passing
; under the lift's column at some unrelated height (e.g. it's high
; overhead) doesn't falsely snap Sam up to meet it.
lift_ride_check:
        call lift_in_footprint
        or  a
        jr  z,.notlift
        ld  a,(on_lift)
        or  a
        jr  nz,.continuing       ; already riding - sync unconditionally
        ld  a,(lift_h)
        ld  b,a
        ld  a,(sam_h+1)
        sub b
        jr  nc,.bdx
        neg
.bdx:   cp  BOARD_TOL
        jr  nc,.notlift          ; too far from the lift's own height
        ld  a,(lift_h)
        ld  (sam_h+1),a
        xor a
        ld  (sam_h),a
        ld  (lift_ride_t),a     ; fresh board - grace period restarts
        ld  a,LIFT_GT
        ld  (ground_t),a
        ld  a,1
        ld  (on_lift),a
        ret
.continuing:
        ld  a,(lift_h)
        ld  (sam_h+1),a
        xor a
        ld  (sam_h),a
        ld  a,LIFT_GT
        ld  (ground_t),a
        ld  a,1
        ld  (on_lift),a
        ret
.notlift:
        xor a
        ld  (on_lift),a
        ret

; lift_update: bounces lift_h between room_lift_ymin/ymax, 1px every
; other frame - same cadence/structure as enemy_update's horizontal
; patrol bounce, just applied to a platform instead of an enemy.
lift_update:
        ld  a,(room_lift_wx)
        cp  0FFh
        ret z
        ld  a,(frame)
        and 1
        ret nz
        ld  a,(lift_dir)
        or  a
        ld  a,(lift_h)
        jr  nz,.down
        inc a
        ld  b,a
        ld  a,(room_lift_ymax)
        ld  c,a
        ld  a,b
        cp  c
        jr  c,.st
        ld  a,1
        ld  (lift_dir),a
        ld  a,(room_lift_ymax)
        jr  .st
.down:  dec a
        ld  b,a
        ld  a,(room_lift_ymin)
        ld  c,a
        ld  a,b
        cp  c
        jr  nc,.st
        xor a
        ld  (lift_dir),a
        ld  a,(room_lift_ymin)
.st:    ld  (lift_h),a
        ret

; ------------------------------------------------------------
; key_erase: restore background chars under key at B=x C=y D=z
; keys_tab entries: bx,bz,y,ccol,crow
; ------------------------------------------------------------
key_erase:
        push bc
        push de
        ; clear map cell
        call map_addr
        ld  (hl),0
        ; find key in table
        ld  hl,(room_keys_ptr)
        ld  a,(room_nkeys)
        ld  e,a
.find:  ld  a,(hl)
        cp  b
        jr  nz,.next
        inc hl
        ld  a,(hl)
        cp  d
        jr  nz,.back1
        inc hl
        ld  a,(hl)
        cp  c
        jr  nz,.back2
        inc hl
        ld  a,(hl)          ; ccol
        inc hl
        ld  h,(hl)          ; crow
        ld  l,a
        jr  .got
.back2: dec hl
.back1: dec hl
.next:  ld  a,5
        add a,l
        ld  l,a
        jr  nc,.nc
        inc h
.nc:    dec e
        jr  nz,.find
        pop de
        pop bc
        ret                 ; not found (shouldn't happen)
.got:   ; l=ccol h=crow : restore 2x2 chars (pattern+color)
        ld  b,2             ; rows
.rl:    ld  c,2             ; cols
        push hl
.cl:    push bc
        push hl
        ; off = crow*256 + ccol*8
        ld  a,h
        ld  b,a             ; crow
        ld  a,l
        add a,a
        add a,a
        add a,a             ; ccol*8 (<=255? ccol<=31 -> 248 ok)
        ld  e,a
        ld  d,b             ; de = crow*256 + ccol*8
        ; pattern: ROM 8000h+off -> VRAM 0000h+off
        ld  hl,BG_PAT
        add hl,de
        push de
        ld  bc,8
        call LDIRVM
        pop de
        ; color: ROM A000h+off -> VRAM 2000h+off
        ld  hl,BG_COL
        add hl,de
        push hl
        ld  hl,02000h
        add hl,de
        ex  de,hl
        pop hl
        ld  bc,8
        call LDIRVM
        pop hl
        pop bc
        inc l               ; next col
        dec c
        jr  nz,.cl
        pop hl
        inc h               ; next row
        djnz .rl
        pop de
        pop bc
        ret

; ------------------------------------------------------------
; Crumbling platforms (two-stage).  crumb_tab record, 17 bytes:
;  +0 ncells, +1 (bx,y,bz)x2 (FF pad), +7 c0, +8 r0, +9 w, +10 h,
;  +11 dw half-data, +13 dw gone-data, +15 slab_tab idx x2 (FF pad)
; ------------------------------------------------------------
; cell_at: B=bx C=celly D=bz -> A = cell id (group*2+cell) or FFh
cell_at:
        ld  a,(room_nunits)
        or  a
        jr  nz,.have
        ld  a,0FFh
        ret
.have:  ld  hl,(room_crumb_ptr)
        xor a
        ld  (cb_u),a
.ul:    ld  a,(hl)
        ld  (cb_n),a
        push hl
        inc hl
        xor a
        ld  (cb_ci),a
.cl:    ld  a,(hl)
        cp  b
        jr  nz,.nx
        inc hl
        ld  a,(hl)
        cp  c
        jr  nz,.nx1
        inc hl
        ld  a,(hl)
        cp  d
        jr  nz,.nx2
        pop hl
        ld  a,(cb_u)
        add a,a
        ld  e,a
        ld  a,(cb_ci)
        add a,e
        ret
.nx2:   dec hl
.nx1:   dec hl
.nx:    inc hl
        inc hl
        inc hl
        ld  a,(cb_ci)
        inc a
        ld  (cb_ci),a
        ld  a,(cb_n)
        dec a
        ld  (cb_n),a
        jr  nz,.cl
        pop hl
        ld  a,l
        add a,18            ; row grew 17->18 bytes/group (added a
                             ; per-group crumble-bank byte - see
                             ; degrade_cell)
        ld  l,a
        jr  nc,.k
        inc h
.k:     ld  a,(cb_u)
        inc a
        ld  (cb_u),a
        ld  e,a             ; NOT b: b/c/d are the caller's bx/celly/bz,
                             ; still needed if the loop continues to the
                             ; next group's .cl scan
        ld  a,(room_nunits)
        sub e
        jr  z,.kdone
        jr  c,.kdone
        jr  .ul
.kdone: ld  a,0FFh
        ret

; degrade_cell: A = cell id -> advance that cell and redraw the group
degrade_cell:
        push bc
        push de
        ld  (cb_id),a
        ld  e,a
        ld  d,0
        ld  hl,cr_cellst
        add hl,de
        ld  a,(hl)
        cp  2
        jp  nc,.done
        inc (hl)
        ld  a,(hl)
        ld  (cb_st),a
        ; record base = crumb_tab + group*18 (17 bytes of cell/rect/
        ; blit data, plus 1 trailing byte: this cell's OWN crumble
        ; bank - lets a room's groups span more than one 8KB crumble
        ; bank instead of being stuck with one bank room-wide, needed
        ; once Room9 grew past a single bank's budget)
        ld  a,(cb_id)
        srl a
        ld  (cb_u),a
        ld  l,a
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl           ; *16
        ld  e,a
        ld  d,0
        add hl,de           ; *17
        add hl,de           ; *18
        ld  de,(room_crumb_ptr)
        add hl,de
        ld  (cb_rec),hl
        ; this cell's own crumble bank lives at record+17 (the new
        ; trailing byte) - read it now, before hl gets reused below
        ld  de,17
        add hl,de
        ld  a,(hl)
        ld  (cb_bank),a
        ld  hl,(cb_rec)
        ; rect
        ld  de,7
        add hl,de
        ld  a,(hl)
        ld  (cb_c0),a
        inc hl
        ld  a,(hl)
        ld  (cb_r0),a
        inc hl
        ld  a,(hl)
        ld  (cb_c1),a
        inc hl
        ld  a,(hl)
        ld  (cb_r1),a
        inc hl
        ld  e,(hl)
        inc hl
        ld  d,(hl)          ; de = rectsize
        inc hl
        ld  a,(hl)
        inc hl
        ld  h,(hl)
        ld  l,a             ; hl = data base (8000h window)
        push hl
        ; combo index -> a
        push de
        ld  a,(cb_u)
        add a,a
        ld  e,a
        ld  d,0
        ld  hl,cr_cellst
        add hl,de
        ld  a,(hl)          ; st0
        ld  (cb_n),a
        ld  hl,(cb_rec)
        ld  a,(hl)
        dec a
        jr  z,.idx1         ; single-cell group: idx = st0
        ld  a,(cb_u)
        add a,a
        inc a
        ld  e,a
        ld  d,0
        ld  hl,cr_cellst
        add hl,de
        ld  a,(cb_n)
        ld  e,a
        add a,a
        add a,e             ; st0*3
        add a,(hl)          ; + st1
        jr  .gidx
.idx1:  ld  a,(cb_n)
.gidx:  pop de
        pop hl
        ; src = base + idx*rectsize
        or  a
        jr  z,.m0
.ml:    add hl,de
        dec a
        jr  nz,.ml
.m0:    ld  (cb_src),hl
        ld  a,(cb_bank)
        ld  (BANK2R),a
        call crumb_blit
        ld  a,(room_bg_bank)
        ld  (BANK2R),a
        ; gone: clear this cell in the map + disable its mask entry
        ld  a,(cb_st)
        cp  2
        jr  nz,.done
        ld  hl,(cb_rec)
        inc hl
        ld  a,(cb_id)
        and 1
        ld  (cb_ci),a
        jr  z,.cc
        ld  de,3
        add hl,de
.cc:    ld  b,(hl)
        inc hl
        ld  c,(hl)
        inc hl
        ld  d,(hl)
        push hl
        call map_addr
        ld  (hl),0
        pop hl
        ; slab idx at record+15+ci
        ld  hl,(cb_rec)
        ld  de,15
        add hl,de
        ld  a,(cb_ci)
        ld  e,a
        ld  d,0
        add hl,de
        ld  a,(hl)
        cp  0FFh
        jr  z,.done
        ld  e,a
        ld  d,0
        ld  hl,slabdis
        add hl,de
        ld  (hl),1
.done:  ; crumb_blit's redraw rect is computed from the keyless base
        ; image, so it can incidentally overwrite a still-uncollected
        ; pickup that happens to overlap it - put any such pickup back
        call key_draw_all
        pop de
        pop bc
        ret

; crumb_blit: copy the unit rect from (cb_src): first w*h*8 pattern
; bytes, then as many colour bytes, to VRAM
crumb_blit:
        ld  hl,(cb_src)
        xor a
        ld  (cb_ph),a
.phase: ld  a,(cb_r0)
        ld  (cb_r),a
.rp:    ld  a,(cb_c0)
        ld  (cb_c),a
.cp:    ld  a,(cb_r)
        ld  d,a
        ld  a,(cb_ph)
        or  a
        jr  z,.pp
        ld  a,d
        add a,020h
        ld  d,a
.pp:    ld  a,(cb_c)
        add a,a
        add a,a
        add a,a
        ld  e,a
        push hl
        ld  bc,8
        call LDIRVM
        pop hl
        ld  bc,8
        add hl,bc
        ld  a,(cb_c)
        inc a
        ld  (cb_c),a
        ld  e,a
        ld  a,(cb_c1)
        cp  e
        jr  nz,.cp
        ld  a,(cb_r)
        inc a
        ld  (cb_r),a
        ld  e,a
        ld  a,(cb_r1)
        cp  e
        jr  nz,.rp
        ld  a,(cb_ph)
        or  a
        ret nz
        inc a
        ld  (cb_ph),a
        jr  .phase

; ------------------------------------------------------------
; mask_update: accumulate all occluding windows into mkbuf
; ------------------------------------------------------------
mask_update:
        ; clear accumulation buffer
        ld  hl,mkbuf
        ld  de,mkbuf+1
        ld  bc,31
        ld  (hl),0
        ldir
        ld  hl,(room_slab_ptr)
        ld  a,(room_nslabs)
        ld  b,a
        ld  c,0             ; entry index
.lp:    push bc
        push hl             ; entry base
        ld  e,c
        ld  d,0
        ld  hl,slabdis
        add hl,de
        ld  a,(hl)
        or  a
        jr  nz,.no          ; slab gone -> never occludes
        pop hl
        push hl
        inc hl
        inc hl              ; -> base_sum
        ld  a,(mk_sum)
        sub (hl)            ; delta = sam_sum - base
        jr  c,.lv0          ; behind -> full mask
        add a,12            ; bias: only cut pixels clearly in front
        cp  32
        jr  nc,.no          ; at/near the front corner -> fully visible
        srl a
        srl a               ; level = (delta+12)/4 (0..7)
        jr  .lvok
.lv0:   xor a
.lvok:  ld  (mk_lvl),a
        inc hl              ; -> surface
        ld  a,(sam_h+1)
        cp  (hl)
        jr  nc,.no          ; at/above its top
        pop hl
        push hl
        ld  a,(mk_sprx)
        sub (hl)            ; dx = sprx - winx0
        cp  64
        jr  nc,.no
        ld  d,a
        inc hl
        ld  a,(mk_spry)
        sub (hl)            ; dy = spry - winy0
        cp  40
        jr  nc,.no
        ld  e,a
        call mask_or        ; mkbuf |= this window
.no:    pop hl
        ld  bc,5
        add hl,bc
        pop bc
        inc c
        djnz .lp
        ld  a,(room_bg_bank)
        ld  (BANK2R),a      ; restore gfx bank
        ret

; mask_or: D=dx E=dy (mk_lvl)=level -> OR the 32-byte ROM window
; into mkbuf.  idx = level*2560 + dy*64 + dx
mask_or:
        ld  l,e
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl           ; dy*64
        ld  c,d
        ld  b,0
        add hl,bc           ; + dx
        ld  a,(mk_lvl)
        add a,a
        ld  c,a
        push hl
        ld  hl,lvl_off
        ld  b,0
        add hl,bc
        ld  c,(hl)
        inc hl
        ld  b,(hl)
        pop hl
        add hl,bc           ; + level*2560
        ld  a,h
        add a,MASKBANK0
        ld  (BANK2R),a
        ld  a,l
        ld  l,a
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl           ; (idx&255)*32
        ld  a,h
        add a,080h
        ld  h,a             ; ROM window ptr
        ld  de,mkbuf
        ld  b,32
.o:     ld  a,(de)
        or  (hl)
        ld  (de),a
        inc hl
        inc de
        djnz .o
        ret

lvl_off: dw 0,2560,5120,7680,10240,12800,15360,17920

; ------------------------------------------------------------
; enemy_update: patrol the conveyor, kill Sam on contact
; ------------------------------------------------------------
enemy_update:
        ld  a,(room_en_axis)
        cp  1
        jp  z,.vertical
        cp  2
        jp  z,.mirror

; ---- horizontal patrol (Rooms 1-4): en_x moves, fixed z/height ----
        ; move at 0.5 px/frame
        ld  a,(frame)
        and 1
        jr  nz,.anim
        ld  a,(en_dir)
        or  a
        ld  a,(en_x)
        jr  nz,.left
        inc a
        ld  b,a
        ld  a,(room_enxmax)
        ld  c,a
        ld  a,b
        cp  c
        jr  c,.st
        ld  a,1
        ld  (en_dir),a
        ld  a,(room_enxmax)
        jr  .st
.left:  dec a
        ld  b,a
        ld  a,(room_enxmin)
        ld  c,a
        ld  a,b
        cp  c
        jr  nc,.st
        xor a
        ld  (en_dir),a
        ld  a,(room_enxmin)
.st:    ld  (en_x),a
.anim:  ld  a,(en_anim)
        inc a
        ld  (en_anim),a

        ; ---- collision with Sam ----
        ld  a,(sam_wx)
        ld  b,a
        ld  a,(en_x)
        sub b
        jr  nc,.dx
        neg
.dx:    cp  10
        ret nc
        ld  a,(sam_wz)
        ld  b,a
        ld  a,(room_enz)
        ld  c,a
        ld  a,b
        sub c
        jr  nc,.dz
        neg
.dz:    cp  10
        ret nc
        ; vertical: enemy body ensurf..ensurf+16, Sam body h..h+16
        ld  a,(room_ensurf)
        ld  c,a
        ld  a,(sam_h+1)
        ld  b,a
        ld  a,c
        add a,16
        ld  d,a
        ld  a,b
        cp  d
        ret nc              ; Sam wholly above
        ld  a,c
        inc a
        ld  d,a
        ld  a,b
        add a,16
        cp  d
        ret c               ; Sam wholly below
        ; hit: lose a life
        jp  sam_die

; ---- vertical patrol (Eugene's Lair boss): en_x is reinterpreted as
; HEIGHT, bouncing between room_enxmin/enxmax; the fixed world position
; is (room_enz=world x, room_ensurf=world z) instead of the usual
; (moving x, fixed z/height) - same bounce/collision shape, transposed.
.vertical:
        ld  a,(frame)
        and 1
        jr  nz,.vanim
        ld  a,(en_dir)
        or  a
        ld  a,(en_x)
        jr  nz,.vdown
        inc a
        ld  b,a
        ld  a,(room_enxmax)
        ld  c,a
        ld  a,b
        cp  c
        jr  c,.vst
        ld  a,1
        ld  (en_dir),a
        ld  a,(room_enxmax)
        jr  .vst
.vdown: dec a
        ld  b,a
        ld  a,(room_enxmin)
        ld  c,a
        ld  a,b
        cp  c
        jr  nc,.vst
        xor a
        ld  (en_dir),a
        ld  a,(room_enxmin)
.vst:   ld  (en_x),a
.vanim: ld  a,(en_anim)
        inc a
        ld  (en_anim),a

        ; ---- collision with Sam (fixed x/z, moving height) ----
        ld  a,(sam_wx)
        ld  b,a
        ld  a,(room_enz)
        sub b
        jr  nc,.vdx
        neg
.vdx:   cp  10
        ret nc
        ld  a,(sam_wz)
        ld  b,a
        ld  a,(room_ensurf)
        sub b
        jr  nc,.vdz
        neg
.vdz:   cp  10
        ret nc
        ld  a,(en_x)
        ld  c,a
        ld  a,(sam_h+1)
        ld  b,a
        ld  a,c
        add a,16
        ld  d,a
        ld  a,b
        cp  d
        ret nc              ; Sam wholly above
        ld  a,c
        inc a
        ld  d,a
        ld  a,b
        add a,16
        cp  d
        ret c               ; Sam wholly below
        jp  sam_die

; ---- mirrored pair (Processing Plant pacmen): en_x is reinterpreted
; as a HALF-GAP distance from room_en_centerx, bouncing between
; room_enxmin (min gap)/enxmax (max gap); the two enemies sit at
; (centerx-en_x) and (centerx+en_x), both at the fixed (room_enz,
; room_ensurf) - checked against Sam independently, either can kill.
.mirror:
        ld  a,(frame)
        and 1
        jr  nz,.manim
        ld  a,(en_dir)
        or  a
        ld  a,(en_x)
        jr  nz,.mshrink
        inc a
        ld  b,a
        ld  a,(room_enxmax)
        ld  c,a
        ld  a,b
        cp  c
        jr  c,.mst
        ld  a,1
        ld  (en_dir),a
        ld  a,(room_enxmax)
        jr  .mst
.mshrink:
        dec a
        ld  b,a
        ld  a,(room_enxmin)
        ld  c,a
        ld  a,b
        cp  c
        jr  nc,.mst
        xor a
        ld  (en_dir),a
        ld  a,(room_enxmin)
.mst:   ld  (en_x),a
.manim: ld  a,(en_anim)
        inc a
        ld  (en_anim),a

        ld  a,(room_en_centerx)
        ld  b,a
        ld  a,(en_x)
        ld  c,a
        ld  a,b
        sub c
        call .mcheck            ; pos1 = centerx - en_x
        ld  a,(room_en_centerx)
        ld  b,a
        ld  a,(en_x)
        add a,b                 ; pos2 = centerx + en_x
        call .mcheck
        ret

; .mcheck: A=enemy world x to test against Sam; ret if clear, tail-jp
; to sam_die on a hit (pops its own call-frame first so the stack is
; exactly as sam_die expects - see the standing "one live frame" rule).
; Always reached via `call` (never a tail jp) so that discard is valid
; every time this runs, not just on a particular caller.
.mcheck:
        ld  d,a
        ld  a,(sam_wx)
        ld  b,a
        ld  a,d
        sub b
        jr  nc,.mdx
        neg
.mdx:   cp  10
        ret nc
        ld  a,(sam_wz)
        ld  b,a
        ld  a,(room_enz)
        ld  c,a
        ld  a,b
        sub c
        jr  nc,.mdz
        neg
.mdz:   cp  10
        ret nc
        ld  a,(room_ensurf)
        ld  c,a
        ld  a,(sam_h+1)
        ld  b,a
        ld  a,c
        add a,16
        ld  e,a
        ld  a,b
        cp  e
        ret nc              ; Sam wholly above
        ld  a,c
        inc a
        ld  e,a
        ld  a,b
        add a,16
        cp  e
        ret c               ; Sam wholly below
        pop hl              ; discard this call's own return address
        jp  sam_die

; ------------------------------------------------------------
; sam_draw: sprites at sx=PX0-8+wx-wz  sy=PY0+(wx+wz)/2-h-16
; ------------------------------------------------------------
sam_draw:
        ; sx
        ld  a,(sam_wx)
        ld  l,a
        ld  h,0
        ld  de,PX0-8
        add hl,de
        ld  a,(sam_wz)
        ld  e,a
        ld  d,0
        or  a
        sbc hl,de
        ld  c,l             ; sx (0..239)
        ; sy
        ld  a,(sam_wz)
        ld  e,a
        ld  a,(sam_wx)
        add a,e             ; <=222
        srl a
        add a,PY0
        ld  b,a
        ld  a,(sam_h+1)
        add a,16            ; sprite height
        ld  e,a
        ld  a,b
        sub e
        jr  nc,.syok
        xor a
.syok:  dec a
        ld  b,a             ; sy-1

        ; mask bookkeeping
        ld  a,c
        ld  (mk_sprx),a
        ld  a,b
        inc a
        ld  (mk_spry),a
        ld  a,(sam_wx)
        ld  e,a
        ld  a,(sam_wz)
        add a,e
        ld  (mk_sum),a
        push bc
        call mask_update
        pop bc

        ; pose = dir*3 (+ 1 or 2 while walking)
        ld  a,(sam_dir)
        ld  e,a
        add a,a
        add a,e             ; dir*3
        ld  e,a
        ld  a,(moved)
        or  a
        jr  z,.pok
        ld  a,(sam_anim)
        inc a
        ld  (sam_anim),a
        rrca
        rrca
        rrca
        and 1
        inc a               ; 1 or 2
        add a,e
        ld  e,a
.pok:   ; pattern base = pose*16 (4 layers x 4)
        ld  a,e
        add a,a
        add a,a
        add a,a
        add a,a
        ld  e,a

        ; ---- build masked Sam patterns: pose AND NOT mkbuf -> mbuf ----
        push bc
        ld  a,e             ; pose*16
        ld  l,a
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl           ; pose*128
        ld  bc,gfx_sprites
        add hl,bc           ; ROM source (bank 1, fixed)
        ld  de,mbuf
        ld  c,4             ; 4 layers
.lyr:   exx
        ld  hl,mkbuf
        exx
        ld  b,32
.mb:    exx
        ld  a,(hl)
        inc hl
        exx
        cpl
        and (hl)
        ld  (de),a
        inc hl
        inc de
        djnz .mb
        dec c
        jr  nz,.lyr
        ld  hl,mbuf
        ld  de,VR_SPRP+48*8
        ld  bc,128
        call LDIRVM
        pop bc

        ; sprite 0: the enemy (priority over Sam)
        push bc
        ld  a,(room_en_axis)
        cp  1
        jp  z,.enaxis1
        cp  2
        jp  z,.enaxis2

        ld  a,(en_x)
        ld  l,a
        ld  h,0
        ld  de,PX0-8
        add hl,de
        ld  a,(room_enz)
        ld  e,a
        ld  d,0
        or  a
        sbc hl,de
        ld  a,l             ; sx = 112 + ex - enz
        ld  c,a
        ld  a,(en_x)
        ld  hl,room_enz
        add a,(hl)
        srl a
        add a,PY0
        push af
        ld  hl,room_ensurf
        ld  a,(hl)
        add a,16
        ld  e,a             ; e = ensurf+16
        pop af
        sub e
        dec a
        ld  b,a             ; sy-1
        jp  .enpos_done

.enaxis1:
        ; vertical patrol: room_enz/room_ensurf are the FIXED world x/z,
        ; en_x is the moving height
        ld  a,(room_enz)
        ld  l,a
        ld  h,0
        ld  de,PX0-8
        add hl,de
        ld  a,(room_ensurf)
        ld  e,a
        ld  d,0
        or  a
        sbc hl,de
        ld  a,l             ; sx = 112 + enz - ensurf (both fixed)
        ld  c,a
        ld  a,(room_enz)
        ld  hl,room_ensurf
        add a,(hl)
        srl a
        add a,PY0
        push af
        ld  a,(en_x)
        add a,16
        ld  e,a             ; e = en_x(height)+16
        pop af
        sub e
        dec a
        ld  b,a             ; sy-1

.enpos_done:
        ld  hl,VR_SPRA
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,(en_anim)
        and 16
        srl a
        srl a               ; 0 or 4
        call WRTVRM
        inc hl
        ld  a,(room_enemy_color)
        call WRTVRM
        inc hl
        jp  .enemy_sprites_done

; ---- mirrored pair (Processing Plant pacmen): two enemy sprites,
; at (centerx-en_x) and (centerx+en_x), both at the fixed (room_enz,
; room_ensurf) - same per-sprite sx/sy formula as the horizontal
; branch above, computed twice via .mkpos/.spr4.
.enaxis2:
        ld  hl,VR_SPRA
        ld  a,(room_en_centerx)
        ld  b,a
        ld  a,(en_x)
        ld  c,a
        ld  a,b
        sub c
        push hl             ; .mkpos uses hl as scratch - save/restore
        call .mkpos         ; the running vram pointer around it, or
        pop hl              ; .spr4 below writes to garbage instead
        call .spr4
        ld  a,(room_en_centerx)
        ld  b,a
        ld  a,(en_x)
        add a,b
        push hl
        call .mkpos
        pop hl
        call .spr4
        jp  .enemy_sprites_done

; .mkpos: in A=enemy world x (fixed room_enz/room_ensurf) -> out b=sy-1,c=sx
.mkpos:
        push af
        ld  l,a
        ld  h,0
        ld  de,PX0-8
        add hl,de
        ld  a,(room_enz)
        ld  e,a
        ld  d,0
        or  a
        sbc hl,de
        ld  a,l
        ld  c,a
        pop af
        ld  hl,room_enz
        add a,(hl)
        srl a
        add a,PY0
        push af
        ld  hl,room_ensurf
        ld  a,(hl)
        add a,16
        ld  e,a
        pop af
        sub e
        dec a
        ld  b,a
        ret

; .spr4: in b=sy-1,c=sx, hl=vram ptr -> writes the 4 sprite-attribute
; bytes at (hl) and advances hl past them
.spr4:
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,(en_anim)
        and 16
        srl a
        srl a
        call WRTVRM
        inc hl
        ld  a,(room_enemy_color)
        call WRTVRM
        inc hl
        ret

.enemy_sprites_done:
        pop bc
        push hl
        pop hl
        ; 4 overlapped Sam sprites (dynamic masked patterns 48/52/56/60)
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,48
        call WRTVRM
        inc hl
        ld  a,14
        call WRTVRM
        inc hl
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,52
        call WRTVRM
        inc hl
        ld  a,9
        call WRTVRM
        inc hl
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,56
        call WRTVRM
        inc hl
        ; body layer color 4 (dark blue) - Fausto wants Sam's original
        ; color kept as-is (reverted an experimental recolor: color 4
        ; does coincide with the T_STONE platform face_l color and can
        ; make Sam's body blend into a platform he's standing in front
        ; of, but that's a secondary visual concern, not what's causing
        ; the reported "walks onto a platform without jumping" issue -
        ; see the walk-through investigation instead).
        ld  a,4
        call WRTVRM
        inc hl
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,60
        call WRTVRM
        inc hl
        ld  a,15
        call WRTVRM
        inc hl

        ; lift platform (2 side-by-side 16x16 sprites, patterns 8/12) -
        ; whichever room has none (room_lift_wx=0FFh) just skips this
        ld  a,(room_lift_wx)
        cp  0FFh
        jr  z,.noliftdraw
        push hl              ; hl is the running VRAM sprite pointer -
                             ; the sx/sy math below clobbers hl itself,
                             ; same lesson as the mirrored-pair enemy's
                             ; .mkpos (see the Processing Plant comment)
        ld  a,(room_lift_wx)
        ld  l,a
        ld  h,0
        ld  de,PX0-8
        add hl,de
        ld  a,(room_lift_wz)
        ld  e,a
        ld  d,0
        or  a
        sbc hl,de
        ld  a,l              ; base sx
        sub 8
        ld  c,a              ; left-half sx
        ld  a,(room_lift_wx)
        ld  hl,room_lift_wz
        add a,(hl)
        srl a
        add a,PY0
        push af
        ld  a,(lift_h)
        add a,16
        ld  e,a
        pop af
        sub e
        dec a
        ld  b,a              ; sy-1 (shared by both halves)
        pop hl
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,8
        call WRTVRM
        inc hl
        ld  a,6
        call WRTVRM
        inc hl
        ld  a,c
        add a,16
        ld  c,a              ; right-half sx
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,12
        call WRTVRM
        inc hl
        ld  a,6
        call WRTVRM
        inc hl
.noliftdraw:
        ld  a,208
        call WRTVRM
        ret

; ------------------------------------------------------------
; door_fx: blink the exit cube (bright/normal) when all keys held
door_fx:
        ld  a,(room_nkeys)
        ld  b,a
        ld  a,(keys_got)
        cp  b
        ret c
        ld  a,(frame)
        and 16
        ld  hl,ex_st
        cp  (hl)
        ret z               ; state unchanged
        ld  (hl),a
        or  a
        jr  z,.norm
        ld  hl,(room_exit_gfx1_ptr)
        jr  .go
.norm:  ld  hl,(room_exit_gfx0_ptr)
.go:    ld  a,(room_exr0)
        ld  d,a
        ld  a,(room_exc0)
        add a,a
        add a,a
        add a,a
        ld  e,a             ; de = EXR0*256 + EXC0*8
        call .rows          ; patterns
        ld  a,(room_exr0)
        ld  d,a
        ld  a,(room_exc0)
        add a,a
        add a,a
        add a,a
        ld  e,a
        ld  a,d
        add a,020h
        ld  d,a             ; de = 2000h + EXR0*256 + EXC0*8
.rows:  ld  a,(room_exnrow)
        ld  b,a
.rl:    push bc
        push de
        push hl
        ld  a,(room_exrowlen)
        ld  c,a
        ld  b,0
        call LDIRVM
        pop hl
        ld  a,(room_exrowlen)
        ld  c,a
        ld  b,0
        add hl,bc
        pop de
        pop bc
        inc d               ; next tile row (+256)
        djnz .rl
        ret

; ------------------------------------------------------------
; HUD (tile row 23): "LIVES n" + "AIR" + depleting bar
; ------------------------------------------------------------
hud_text:                       ; col, font index ('0'-relative)
        db 0,28, 1,25, 2,38, 3,21, 4,35  ; L I V E S
        db 8,17, 9,25, 10,34             ; A I R
        db 0FFh

hud_putc:                       ; A=font index, C=column
        push bc
        push af
        ld  l,c
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl               ; col*8
        push hl
        ld  de,HUDCOL
        add hl,de
        ex  de,hl               ; DE = colour addr
        ld  a,0F1h              ; white on black
        ld  bc,8
        call FILVRM
        pop hl
        ld  de,HUDPAT
        add hl,de
        ex  de,hl               ; DE = pattern addr
        pop af
        ld  l,a
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld  bc,fonts_tab
        add hl,bc
        ld  bc,8
        call LDIRVM
        pop bc
        ret

hud_init:
        ld  hl,hud_text
.tx:    ld  a,(hl)
        cp  0FFh
        jr  z,.bar
        ld  c,a
        inc hl
        ld  a,(hl)
        inc hl
        push hl
        call hud_putc
        pop hl
        jr  .tx
.bar:   ; bar colours (white on black) for cols BARCOL..31
        ld  hl,HUDCOL+BARCOL*8
        ld  a,0F1h
        ld  bc,(32-BARCOL)*8
        call FILVRM
        ; bar patterns: rows 2..5 solid, drawn as full then edge-fix
        ld  hl,HUDPAT+BARCOL*8
        xor a
        ld  bc,(32-BARCOL)*8
        call FILVRM
        ld  b,32-BARCOL
        ld  hl,HUDPAT+BARCOL*8+2
.bt:    push bc
        push hl
        ld  a,0FFh
        ld  bc,4
        call FILVRM
        pop hl
        ld  bc,8
        add hl,bc
        pop bc
        djnz .bt
        ; lives digit
        call hud_lives
        ; redraw edge for current air (full at start)
        ret

hud_lives:
        ld  a,(lives)
        ld  c,LIVCOL
        jp  hud_putc

; air_update: deplete 1 bar pixel every AIRRATE frames
air_masks:
        db 000h,080h,0C0h,0E0h,0F0h,0F8h,0FCh,0FEh
air_update:
        ld  hl,air_t
        inc (hl)
        ld  a,(hl)
        cp  AIRRATE
        ret c
        ld  (hl),0
        ld  a,(air)
        dec a
        ld  (air),a
        jp  z,sam_die
        ; redraw the edge tile: col = BARCOL + air/8, mask = air&7
        ld  c,a
        and 7
        ld  l,a
        ld  h,0
        ld  de,air_masks
        add hl,de
        ld  b,(hl)              ; edge mask byte
        ld  a,c
        srl a
        srl a
        srl a
        add a,BARCOL
        ld  l,a
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld  de,HUDPAT+2
        add hl,de               ; rows 2..5 of the edge tile
        ld  c,4
.wr:    push bc
        push hl
        ld  a,b
        call WRTVRM
        pop hl
        inc hl
        pop bc
        dec c
        jr  nz,.wr
        ret

; ------------------------------------------------------------
psg_init:
        ld  a,7
        ld  e,GAME_MIX
        call WRTPSG
        ld  a,10
        ld  e,0
        call WRTPSG
        ret

sfx_update:
        ld  a,(sfx_t)
        or  a
        jr  z,.off
        dec a
        ld  (sfx_t),a
        ld  hl,(sfx_freq)
        ld  de,(sfx_step)
        add hl,de
        ld  (sfx_freq),hl
        ld  a,4
        ld  e,l
        call WRTPSG
        ld  a,5
        ld  e,h
        call WRTPSG
        ld  a,10
        ld  e,12
        call WRTPSG
        ret
.off:   ld  a,10
        ld  e,0
        call WRTPSG
        ret

; ============================================================
;  Title screen: "SAM.PR MINER" + a piano keyboard Sam.Pr hops
;  along in time with the tune (a wink at Manic Miner's title,
;  without borrowing its actual tune or logo).
;  PSG waltz music: channel A = melody, channel B = oom-pah-pah
;  bass. Channel C stays free (used for gameplay SFX only).
; ============================================================

; ------------------------------------------------------------
; music_init/update/stop: 2-channel PSG sequencer
; ------------------------------------------------------------
music_init:
        ld  a,7
        ld  e,TITLE_MIX
        call WRTPSG
        ld  a,8
        ld  e,12
        call WRTPSG
        ld  a,9
        ld  e,9
        call WRTPSG
        ld  hl,melody_tab
        ld  (mus_mel_ptr),hl
        xor a
        ld  (mus_mel_t),a
        ld  hl,bass_tab
        ld  (mus_bass_ptr),hl
        ld  (mus_bass_t),a
        ld  a,0FFh
        ld  (ttl_key_cur),a
        ld  (ttl_key_prev),a
        ld  (ttl_pose),a
        ret

music_stop:
        ld  a,8
        ld  e,0
        call WRTPSG
        ld  a,9
        ld  e,0
        call WRTPSG
        ret

music_update:
        ld  hl,mus_mel_t
        ld  a,(hl)
        or  a
        jr  nz,.meldec
        call mel_next
        jr  .bass
.meldec:
        dec (hl)
.bass:
        ld  hl,mus_bass_t
        ld  a,(hl)
        or  a
        jr  nz,.bassdec
        jp  bass_next
.bassdec:
        dec (hl)
        ret

; mel_next: load the next melody event, write ch A period,
; and kick off a hop toward its piano key
mel_next:
        ld  hl,(mus_mel_ptr)
        ld  a,(hl)
        ld  (mtmp0),a
        inc hl
        ld  a,(hl)
        ld  (mtmp1),a
        inc hl
        ld  a,(mtmp0)
        cp  0FFh
        jr  nz,.go
        ld  a,(mtmp1)
        cp  0FFh
        jr  nz,.go
        ld  hl,melody_tab
        ld  (mus_mel_ptr),hl
        jr  mel_next
.go:    ld  a,(ttl_key_cur)
        ld  (ttl_key_prev),a
        ld  a,(hl)              ; new key index
        ld  (ttl_key_cur),a
        inc hl
        ld  a,(hl)              ; frames
        ld  (mus_mel_t),a
        inc hl
        ld  (mus_mel_ptr),hl
        ; un-light the previous key, light the new one
        ld  a,(ttl_key_prev)
        cp  0FFh
        jr  z,.nounlit
        ld  c,KEY_NORMAL
        call key_set_color
.nounlit:
        ld  a,(ttl_key_cur)
        ld  c,KEY_LIT
        call key_set_color
        ; PSG ch A period (reg 0/1)
        ld  a,(mtmp0)
        ld  e,a
        ld  a,0
        call WRTPSG
        ld  a,(mtmp1)
        ld  e,a
        ld  a,1
        call WRTPSG
        ret

; bass_next: load the next bass event, write ch B period
bass_next:
        ld  hl,(mus_bass_ptr)
        ld  a,(hl)
        ld  (mtmp0),a
        inc hl
        ld  a,(hl)
        ld  (mtmp1),a
        inc hl
        ld  a,(mtmp0)
        cp  0FFh
        jr  nz,.go
        ld  a,(mtmp1)
        cp  0FFh
        jr  nz,.go
        ld  hl,bass_tab
        ld  (mus_bass_ptr),hl
        jr  bass_next
.go:    ld  a,(hl)
        ld  (mus_bass_t),a
        inc hl
        ld  (mus_bass_ptr),hl
        ld  a,(mtmp0)
        ld  e,a
        ld  a,2
        call WRTPSG
        ld  a,(mtmp1)
        ld  e,a
        ld  a,3
        call WRTPSG
        ret

; ------------------------------------------------------------
; level (in-game) music: same 2-channel design as the title
; screen's player, on its own tables/state so it can loop for as
; long as a level is being played, independent of the title tune
; ------------------------------------------------------------
level_music_init:
        ld  a,8
        ld  e,12
        call WRTPSG
        ld  a,9
        ld  e,9
        call WRTPSG
        ld  hl,level_melody_tab
        ld  (mus_mel_ptr),hl
        xor a
        ld  (mus_mel_t),a
        ld  hl,level_bass_tab
        ld  (mus_bass_ptr),hl
        ld  (mus_bass_t),a
        ret

level_music_update:
        ld  hl,mus_mel_t
        ld  a,(hl)
        or  a
        jr  nz,.meldec
        call level_mel_next
        jr  .bass
.meldec:
        dec (hl)
.bass:
        ld  hl,mus_bass_t
        ld  a,(hl)
        or  a
        jr  nz,.bassdec
        jp  level_bass_next
.bassdec:
        dec (hl)
        ret

level_mel_next:
        ld  hl,(mus_mel_ptr)
        ld  a,(hl)
        ld  (mtmp0),a
        inc hl
        ld  a,(hl)
        ld  (mtmp1),a
        inc hl
        ld  a,(mtmp0)
        cp  0FFh
        jr  nz,.go
        ld  a,(mtmp1)
        cp  0FFh
        jr  nz,.go
        ld  hl,level_melody_tab
        ld  (mus_mel_ptr),hl
        jr  level_mel_next
.go:    ld  a,(hl)
        ld  (mus_mel_t),a
        inc hl
        ld  (mus_mel_ptr),hl
        ld  a,(mtmp0)
        ld  e,a
        ld  a,0
        call WRTPSG
        ld  a,(mtmp1)
        ld  e,a
        ld  a,1
        call WRTPSG
        ret

level_bass_next:
        ld  hl,(mus_bass_ptr)
        ld  a,(hl)
        ld  (mtmp0),a
        inc hl
        ld  a,(hl)
        ld  (mtmp1),a
        inc hl
        ld  a,(mtmp0)
        cp  0FFh
        jr  nz,.go
        ld  a,(mtmp1)
        cp  0FFh
        jr  nz,.go
        ld  hl,level_bass_tab
        ld  (mus_bass_ptr),hl
        jr  level_bass_next
.go:    ld  a,(hl)
        ld  (mus_bass_t),a
        inc hl
        ld  (mus_bass_ptr),hl
        ld  a,(mtmp0)
        ld  e,a
        ld  a,2
        call WRTPSG
        ld  a,(mtmp1)
        ld  e,a
        ld  a,3
        call WRTPSG
        ret

; level_melody_tab/level_bass_tab: dw period, db frames; FFFFh=loop
; Transcribed from the public-domain (1875) Mutopia Project MIDI
; edition of Grieg's "In the Hall of the Mountain King" (Peer Gynt,
; Op. 46 No. 4), the famous creeping B-minor ostinato that opens
; the piece - the whole excerpt shifted up an octave to fit the
; PSG's tone-period range, staccato notes rendered legato (held to
; the next onset) for a fuller chiptune sound. 16-beat (4-bar) loop.
level_melody_tab:
        dw P_B2
        db 8
        dw P_CS3
        db 8
        dw P_D3
        db 8
        dw P_E3
        db 8
        dw P_FS3
        db 8
        dw P_D3
        db 8
        dw P_FS3
        db 16
        dw P_F3
        db 8
        dw P_CS3
        db 8
        dw P_F3
        db 16
        dw P_E3
        db 8
        dw P_C3
        db 8
        dw P_E3
        db 16
        dw P_B2
        db 8
        dw P_CS3
        db 8
        dw P_D3
        db 8
        dw P_E3
        db 8
        dw P_FS3
        db 8
        dw P_D3
        db 8
        dw P_FS3
        db 8
        dw P_B3
        db 8
        dw P_A3
        db 8
        dw P_FS3
        db 8
        dw P_D3
        db 8
        dw P_FS3
        db 8
        dw P_A3
        db 32
        dw 0FFFFh

level_bass_tab:
        dw P_B1
        db 16
        dw P_FS2
        db 16
        dw P_B1
        db 16
        dw P_FS2
        db 16
        dw P_B1
        db 16
        dw P_FS2
        db 16
        dw P_B1
        db 16
        dw P_FS2
        db 16
        dw P_B1
        db 16
        dw P_FS2
        db 16
        dw P_B1
        db 16
        dw P_FS2
        db 16
        dw P_D2
        db 16
        dw P_A2
        db 16
        dw P_D2
        db 16
        dw P_A2
        db 16
        dw 0FFFFh

; ------------------------------------------------------------
; key_x_lookup/key_y_lookup: A(key idx 0-6) -> A(pixel coord)
; keys (0-14, two octaves D4..D6): 0=D4 1=E4 2=F#4 3=G4 4=A4 5=B4
; 6=C#4 7=D5 8=E5 9=F#5 10=G5 11=A5 12=B5 13=C#5 14=D6
; (F#/C# entries are the black keys)
; ------------------------------------------------------------
key_x_tab: db 24,40,68,72,88,104,20,136,152,180,184,200,216,132,248
key_y_tab: db 159,159,143,159,159,159,143,159,159,143,159,159,159,143,159

key_x_lookup:
        push hl
        ld  hl,key_x_tab
        ld  e,a
        ld  d,0
        add hl,de
        ld  a,(hl)
        pop hl
        ret

key_y_lookup:
        push hl
        ld  hl,key_y_tab
        ld  e,a
        ld  d,0
        add hl,de
        ld  a,(hl)
        pop hl
        ret

; key_col_tab: first tile column of each of the 15 keys above
key_col_tab: db 2,4,8,8,10,12,2,16,18,22,22,24,26,16,30
KEY_NORMAL equ 01Fh     ; black-on-white, matches the rest of the keyboard
KEY_LIT    equ 077h     ; cyan "pressed" look (works for white or black keys)

; key_set_color: A=key index (0-14), C=colour byte -> repaint just
; that key's colour bytes (its pattern/shape is untouched, so a
; white key stays white-shaped and a black key stays black-shaped;
; only the colour used to render it changes).
key_set_color:
        ld  (kc_idx),a
        ld  a,c
        ld  (kc_color),a
        ld  a,(kc_idx)
        push hl
        ld  hl,key_col_tab
        ld  e,a
        ld  d,0
        add hl,de
        ld  a,(hl)
        pop hl
        ld  (kc_col),a
        ld  a,(kc_idx)
        push hl
        ld  hl,key_y_tab
        ld  e,a
        ld  d,0
        add hl,de
        ld  a,(hl)
        pop hl
        cp  143
        jr  nz,.white
        ld  a,1
        ld  (kc_rows),a
        ld  a,8
        ld  (kc_width),a
        jr  .go
.white: ld  a,KBD_ROWS
        ld  (kc_rows),a
        ld  a,16
        ld  (kc_width),a
.go:    ld  a,(kc_col)
        add a,a
        add a,a
        add a,a
        ld  l,a
        ld  h,KBD_R0
        ld  de,02000h
        add hl,de               ; hl = colour addr, row KBD_R0
        ld  a,(kc_rows)
        ld  b,a
.rl:    push bc
        push hl
        ld  a,(kc_width)
        ld  c,a
        ld  b,0
        ld  a,(kc_color)
        call vram_fill
        pop hl
        ld  de,256
        add hl,de
        pop bc
        djnz .rl
        ret

; ------------------------------------------------------------
; title_sam_draw: advance the hop (if any) and redraw Sam using the
; same 4-layer sprite system as gameplay: gfx_sprites is organised as
; 12 poses (dir*3+walkframe) of 128 bytes = 4x32-byte colour layers.
; In-game these get AND-NOT'ed against an occlusion mask; the title
; screen has nothing to occlude Sam with, so the raw layer bytes can
; be blitted straight to the sprite pattern table.
; ------------------------------------------------------------
title_sam_draw:
        ; Sam just dances in place above the keyboard: walk-cycle
        ; frames alternate on the beat, always facing right, with a
        ; small bob - no more travelling from key to key. Pose/Y/X
        ; all only actually change once every 8 frames (on the bit3
        ; flip), so when they don't, skip this whole routine - not
        ; just the 128-byte blit but the 9 sprite-attribute writes
        ; too, since they'd just rewrite the same values.
        ld  a,(frame)
        bit 3,a
        ld  a,10                ; pose = dir3(right)*3 + walkframe1
        ld  b,SAM_Y
        jr  z,.gotpose
        ld  a,11                ; pose = dir3*3 + walkframe2
        ld  b,SAM_Y-2
.gotpose:
        ld  hl,ttl_pose
        cp  (hl)
        ret z                   ; nothing changed since last frame
        ld  (hl),a
        push bc
        ld  l,a
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl               ; hl = pose*128
        ld  bc,gfx_sprites
        add hl,bc
        ld  de,VR_SPRP
        ld  bc,128
        call vram_copy
        pop bc
.goty:  ld  c,SAM_X
        ld  hl,VR_SPRA
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,0
        call WRTVRM
        inc hl
        ld  a,14
        call WRTVRM
        inc hl
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,4
        call WRTVRM
        inc hl
        ld  a,9
        call WRTVRM
        inc hl
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,8
        call WRTVRM
        inc hl
        ld  a,4
        call WRTVRM
        inc hl
        ld  a,b
        call WRTVRM
        inc hl
        ld  a,c
        call WRTVRM
        inc hl
        ld  a,12
        call WRTVRM
        inc hl
        ld  a,15
        call WRTVRM
        inc hl
        ld  a,208               ; end of sprite list
        call WRTVRM
        ret

; ------------------------------------------------------------
; title_blink: toggle the "PRESS SPACE" text on/off
; ------------------------------------------------------------
title_blink:
        ld  a,(frame)
        and 16
        ld  hl,ttl_blast
        cp  (hl)
        ret z
        ld  (hl),a
        or  a
        ld  a,0F1h
        jr  z,.vis
        ld  a,011h              ; black-on-black: vanish into the
                                 ; (now black) backdrop
.vis:   ld  hl,02000h+6*256+6*8
        ld  bc,19*8
        call vram_fill
        ret

; ------------------------------------------------------------
; vram_fill: HL=VRAM addr, A=value, BC=count -> raw fill.
; FILVRM misbehaves here past a few hundred bytes on this BIOS
; (verified empirically), so bulk fills use SETWRT + a plain
; OUT loop instead, same technique as the name-table loop above.
; ------------------------------------------------------------
vram_fill:
        push af
        call SETWRT
        pop af
.loop:  out (098h),a
        nop
        nop
        dec bc
        ld  d,a
        ld  a,b
        or  c
        ld  a,d
        jr  nz,.loop
        ret

; vram_copy: HL=src (RAM/ROM), DE=dest VRAM addr, BC=count -> raw copy.
; (LDIRVM showed the same unreliability as FILVRM here.)
vram_copy:
        push hl
        ex  de,hl
        call SETWRT
        pop hl
.loop:  ld  a,(hl)
        out (098h),a
        nop
        nop
        nop
        nop
        inc hl
        dec bc
        ld  e,a
        ld  a,b
        or  c
        ld  a,e
        jr  nz,.loop
        ret

; ------------------------------------------------------------
; draw_string: HL=text (0=end,1=custom dot glyph,2=custom apostrophe
; glyph,' '=blank). fonts_tab only covers ASCII 48-123 ('0'-relative,
; see title_putc) - punctuation below '0' (like the apostrophe, 39)
; has no glyph there and needs its own custom byte code instead, same
; as the dot.
; ds_row/ds_col set by caller; ds_col advances per character
; ------------------------------------------------------------
draw_string:
        ld  a,(hl)
        or  a
        ret z
        inc hl
        push hl
        cp  1
        jr  z,.dot
        cp  2
        jr  z,.apos
        cp  ' '
        jr  z,.skip
        sub '0'
        call title_putc
        jr  .adv
.dot:   call title_putdot
        jr  .adv
.apos:  call title_putapos
        jr  .adv
.skip:
.adv:   ld  a,(ds_col)
        inc a
        ld  (ds_col),a
        pop hl
        jr  draw_string

title_putc:                     ; A = font index (fonts_tab, from '0')
        push af
        ld  a,(ds_col)
        add a,a
        add a,a
        add a,a
        ld  l,a
        ld  a,(ds_row)
        ld  h,a                 ; hl = row*256 + col*8 (pattern addr)
        push hl
        ld  de,02000h
        add hl,de               ; hl = colour addr
        ld  a,0F1h
        ld  bc,8
        call vram_fill
        pop hl                  ; hl = pattern addr
        ex  de,hl               ; de = pattern addr
        pop af
        ld  l,a
        ld  h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld  bc,fonts_tab
        add hl,bc
        ld  bc,8
        call vram_copy
        ret

title_putdot:                   ; draws the custom '.' glyph
        ld  a,(ds_col)
        add a,a
        add a,a
        add a,a
        ld  l,a
        ld  a,(ds_row)
        ld  h,a
        push hl
        ld  de,02000h
        add hl,de                ; hl = colour addr
        ld  a,0F1h
        ld  bc,8
        call vram_fill
        pop hl                  ; hl = pattern addr
        ex  de,hl               ; de = pattern addr
        ld  hl,title_dot
        ld  bc,8
        call vram_copy
        ret

title_dot: db 0,0,0,0,0,0,018h,018h

title_putapos:                  ; draws the custom apostrophe glyph
        ld  a,(ds_col)
        add a,a
        add a,a
        add a,a
        ld  l,a
        ld  a,(ds_row)
        ld  h,a
        push hl
        ld  de,02000h
        add hl,de                ; hl = colour addr
        ld  a,0F1h
        ld  bc,8
        call vram_fill
        pop hl                  ; hl = pattern addr
        ex  de,hl               ; de = pattern addr
        ld  hl,title_apos
        ld  bc,8
        call vram_copy
        ret

title_apos: db 018h,018h,010h,0,0,0,0,0

; ------------------------------------------------------------
; title_kbd / _sep / _black: draw a real 2-octave piano keyboard
; (16 white keys C4..D6 at 2 tiles/16px each = the full 256px
; width, standard 12-note-per-octave black key layout so it
; reads as a genuine keyboard even though Sam only ever visits
; the 7 D-major keys in it - see key_x_tab/key_y_tab above)
; ------------------------------------------------------------
KBD_R0  equ 18
KBD_ROWS equ 4          ; shorter keyboard (was 6) - rows 18-21
KBD_C0  equ 0
KBD_COLS equ 32

; a vertical divider between every adjacent white key (all 15
; boundaries: cols 2,4,6,...,30), full keyboard height - not just
; the 4 boundaries that lack a black key on top
sep_addrs:
        dw KBD_R0*256+2*8,  KBD_R0*256+4*8,  KBD_R0*256+6*8,  KBD_R0*256+8*8,  KBD_R0*256+10*8
        dw KBD_R0*256+12*8, KBD_R0*256+14*8, KBD_R0*256+16*8, KBD_R0*256+18*8, KBD_R0*256+20*8
        dw KBD_R0*256+22*8, KBD_R0*256+24*8, KBD_R0*256+26*8, KBD_R0*256+28*8, KBD_R0*256+30*8
        dw (KBD_R0+1)*256+2*8,  (KBD_R0+1)*256+4*8,  (KBD_R0+1)*256+6*8,  (KBD_R0+1)*256+8*8,  (KBD_R0+1)*256+10*8
        dw (KBD_R0+1)*256+12*8, (KBD_R0+1)*256+14*8, (KBD_R0+1)*256+16*8, (KBD_R0+1)*256+18*8, (KBD_R0+1)*256+20*8
        dw (KBD_R0+1)*256+22*8, (KBD_R0+1)*256+24*8, (KBD_R0+1)*256+26*8, (KBD_R0+1)*256+28*8, (KBD_R0+1)*256+30*8
        dw (KBD_R0+2)*256+2*8,  (KBD_R0+2)*256+4*8,  (KBD_R0+2)*256+6*8,  (KBD_R0+2)*256+8*8,  (KBD_R0+2)*256+10*8
        dw (KBD_R0+2)*256+12*8, (KBD_R0+2)*256+14*8, (KBD_R0+2)*256+16*8, (KBD_R0+2)*256+18*8, (KBD_R0+2)*256+20*8
        dw (KBD_R0+2)*256+22*8, (KBD_R0+2)*256+24*8, (KBD_R0+2)*256+26*8, (KBD_R0+2)*256+28*8, (KBD_R0+2)*256+30*8
        dw (KBD_R0+3)*256+2*8,  (KBD_R0+3)*256+4*8,  (KBD_R0+3)*256+6*8,  (KBD_R0+3)*256+8*8,  (KBD_R0+3)*256+10*8
        dw (KBD_R0+3)*256+12*8, (KBD_R0+3)*256+14*8, (KBD_R0+3)*256+16*8, (KBD_R0+3)*256+18*8, (KBD_R0+3)*256+20*8
        dw (KBD_R0+3)*256+22*8, (KBD_R0+3)*256+24*8, (KBD_R0+3)*256+26*8, (KBD_R0+3)*256+28*8, (KBD_R0+3)*256+30*8
SEP_N equ 60

; full chromatic black keys: C#4 D#4 F#4 G#4 A#4 (octave4), C#5 D#5
; F#5 G#5 A#5 (octave5), C#6 -- cols 2,4,8,10,12, 16,18,22,24,26, 30
; (just 1 row tall now, shorter keyboard - was 2)
black_addrs:
        dw KBD_R0*256+2*8,  KBD_R0*256+4*8,  KBD_R0*256+8*8,  KBD_R0*256+10*8,  KBD_R0*256+12*8
        dw KBD_R0*256+16*8, KBD_R0*256+18*8, KBD_R0*256+22*8, KBD_R0*256+24*8,  KBD_R0*256+26*8
        dw KBD_R0*256+30*8
BLACK_N equ 11

title_kbd:
        ld  hl,KBD_R0*256+KBD_C0*8
        ld  b,KBD_ROWS
.rl:    push bc
        push hl
        xor a
        ld  bc,KBD_COLS*8
        call vram_fill
        pop  hl
        push hl
        ld  de,02000h
        add hl,de
        ld  a,01Fh
        ld  bc,KBD_COLS*8
        call vram_fill
        pop hl
        ld  de,256
        add hl,de
        pop bc
        djnz .rl
        ret

; solid line across the very top of the keyboard, so it reads as
; one defined strip instead of just fading into the page above
title_kbd_top:
        ld  hl,KBD_R0*256
        ld  b,32
.tl:    push bc
        push hl
        ld  a,0FFh
        ld  bc,1
        call vram_fill
        pop hl
        ld  de,8
        add hl,de
        pop bc
        djnz .tl
        ret

title_kbd_sep:
        ld  hl,sep_addrs
        ld  b,SEP_N
.sl:    push bc
        ld  e,(hl)
        inc hl
        ld  d,(hl)
        inc hl
        push hl
        ex  de,hl
        ld  a,080h
        ld  bc,8
        call vram_fill
        pop hl
        pop bc
        djnz .sl
        ret

title_kbd_black:
        ld  hl,black_addrs
        ld  b,BLACK_N
.bl:    push bc
        ld  e,(hl)
        inc hl
        ld  d,(hl)
        inc hl
        push hl
        ex  de,hl
        ld  a,0FFh
        ld  bc,8
        call vram_fill
        pop hl
        pop bc
        djnz .bl
        ret

title_str1: db "SAM",1,"PR MINER",0
title_str2: db "PRESS FIRE TO START",0

; ------------------------------------------------------------
; scrolling credit banner (row 23, right under the keyboard).
; Each scroll_rowN table is the font data for "SAM.PR Miner -
; FAUSTO PRACEK 2026" (36 chars incl. trailing gap), transposed
; so row N holds that pixel-row's byte from every character in
; turn, with the first 32 bytes repeated at the end so a 32-byte
; window can always be read starting anywhere in 0..SCROLL_LEN-1
; without special-casing the wrap.
; ------------------------------------------------------------
SCROLLROW equ 23
SCROLL_LEN equ 65       ; message + a full 32-col blank gap, so it
                         ; fully exits before starting to re-enter

scroll_row0: db 00Eh,002h,061h,000h,06Eh,06Eh,000h,061h,006h,061h,023h,06Eh,000h,000h,000h,01Ch,00Eh,01Ch,00Eh,000h,043h,002h,063h,00Eh,067h,03Eh,000h,06Eh,06Eh,002h,00Ch,023h,041h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,00Eh,002h,061h,000h,06Eh,06Eh,000h,061h,006h,061h,023h,06Eh,000h,000h,000h,01Ch,00Eh,01Ch,00Eh,000h,043h,002h,063h,00Eh,067h,03Eh,000h,06Eh,06Eh,002h,00Ch,023h
scroll_row1: db 013h,006h,033h,000h,033h,033h,000h,033h,002h,031h,03Eh,033h,000h,000h,000h,036h,019h,036h,018h,000h,07Eh,006h,031h,013h,03Eh,013h,000h,033h,033h,006h,01Ah,03Eh,031h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,013h,006h,033h,000h,033h,033h,000h,033h,002h,031h,03Eh,033h,000h,000h,000h,036h,019h,036h,018h,000h,07Eh,006h,031h,013h,03Eh,013h,000h,033h,033h,006h,01Ah,03Eh
scroll_row2: db 011h,006h,015h,000h,011h,011h,000h,015h,004h,013h,010h,011h,000h,000h,000h,022h,031h,022h,030h,000h,010h,006h,011h,011h,010h,021h,000h,011h,011h,006h,032h,010h,013h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,011h,006h,015h,000h,011h,011h,000h,015h,004h,013h,010h,011h,000h,000h,000h,022h,031h,022h,030h,000h,010h,006h,011h,011h,010h,021h,000h,011h,011h,006h,032h,010h
scroll_row3: db 04Ch,04Ah,029h,000h,051h,053h,000h,029h,004h,02Ah,05Ch,053h,000h,07Eh,000h,006h,031h,006h,03Ch,000h,052h,04Ah,021h,04Ch,010h,021h,000h,051h,053h,04Ah,020h,05Ch,026h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,04Ch,04Ah,029h,000h,051h,053h,000h,029h,004h,02Ah,05Ch,053h,000h,07Eh,000h,006h,031h,006h,03Ch,000h,052h,04Ah,021h,04Ch,010h,021h,000h,051h,053h,04Ah,020h,05Ch
scroll_row4: db 026h,073h,02Ah,000h,072h,07Eh,000h,02Ah,02Ch,026h,070h,07Eh,000h,000h,000h,00Ch,031h,00Ch,066h,000h,07Ch,073h,021h,026h,030h,061h,000h,072h,07Eh,073h,061h,070h,038h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,026h,073h,02Ah,000h,072h,07Eh,000h,02Ah,02Ch,026h,070h,07Eh,000h,000h,000h,00Ch,031h,00Ch,066h,000h,07Ch,073h,021h,026h,030h,061h,000h,072h,07Eh,073h,061h,070h
scroll_row5: db 063h,03Bh,062h,000h,03Ch,028h,000h,062h,01Ch,062h,021h,028h,000h,000h,000h,031h,033h,031h,046h,000h,024h,03Bh,062h,063h,060h,062h,000h,03Ch,028h,03Bh,062h,021h,06Eh,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,063h,03Bh,062h,000h,03Ch,028h,000h,062h,01Ch,062h,021h,028h,000h,000h,000h,031h,033h,031h,046h,000h,024h,03Bh,062h,063h,060h,062h,000h,03Ch,028h,03Bh,062h,021h
scroll_row6: db 073h,067h,067h,018h,060h,066h,000h,067h,018h,067h,067h,066h,000h,000h,000h,07Eh,03Fh,07Eh,07Ch,000h,060h,067h,07Eh,073h,060h,03Eh,000h,060h,066h,067h,076h,067h,067h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,073h,067h,067h,018h,060h,066h,000h,067h,018h,067h,067h,066h,000h,000h,000h,07Eh,03Fh,07Eh,07Ch,000h,060h,067h,07Eh,073h,060h,03Eh,000h,060h,066h,067h,076h,067h
scroll_row7: db 03Eh,066h,063h,018h,060h,063h,000h,063h,018h,063h,07Ch,063h,000h,000h,000h,07Ch,01Eh,07Ch,038h,000h,070h,066h,03Ch,03Eh,060h,018h,000h,060h,063h,066h,03Ch,07Ch,063h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,000h,03Eh,066h,063h,018h,060h,063h,000h,063h,018h,063h,07Ch,063h,000h,000h,000h,07Ch,01Eh,07Ch,038h,000h,070h,066h,03Ch,03Eh,060h,018h,000h,060h,063h,066h,03Ch,07Ch

scroll_row_tab: dw scroll_row0,scroll_row1,scroll_row2,scroll_row3,scroll_row4,scroll_row5,scroll_row6,scroll_row7

; scroll_emit_row: caller sets scr_src/scr_dst, writes 32 shifted
; bytes (uses scr_bit as the 0-7 sub-byte shift amount)
; scroll_calc_row: hl=src ptr into a row-stream table (already
; offset by scr_byte) -> computes 32 shifted bytes into SCRBUF,
; one per tile column, at stride 8 starting at SCRBUF+scr_rowidx.
; Pure RAM work, no VDP access - cheap, can run every frame.
SCRBUF equ 0C100h       ; reuses ram_map's space (idle during title)

; hl=src ptr (already offset by scr_byte). Keeps src in HL and dst
; in IX for the whole 32-byte run instead of round-tripping through
; memory each byte - that round-trip was the dominant cost here.
scroll_calc_row:
        push hl
        ld  a,(scr_rowidx)
        ld  l,a
        ld  h,0
        ld  de,SCRBUF
        add hl,de
        push hl
        pop ix                  ; ix = dst cursor (SCRBUF+rowidx)
        pop hl                  ; hl = src cursor
        ld  b,32
.loop:  ld  a,(scr_bit)
        or  a
        jr  z,.noshift
        ld  d,(hl)
        inc hl
        ld  e,(hl)
        dec hl
        ld  c,a
.sh:    sla e
        rl  d
        dec c
        jr  nz,.sh
        ld  a,d
        jr  .have
.noshift:
        ld  a,(hl)
.have:  ld  (ix+0),a
        inc hl
        ld  de,8
        add ix,de
        djnz .loop
        ret

; scroll_blit: copy SCRBUF (32 tiles x 8 bytes, already in the
; right byte order for each tile) to VRAM row SCROLLROW. Only
; 32 SETWRT calls (one per tile, then 8 fast sequential OUTs
; using the VDP's own auto-increment) instead of 256.
scroll_blit:
        ld  hl,SCRBUF
        ld  (scr_src),hl
        ld  hl,SCROLLROW*256
        ld  (scr_dst),hl
        ld  a,32
        ld  (scb_cnt),a
.blit:  ld  hl,(scr_dst)
        call SETWRT
        ld  hl,(scr_src)
        ld  b,8
.inner: ld  a,(hl)
        out (098h),a
        inc hl
        djnz .inner
        ld  (scr_src),hl
        ld  hl,(scr_dst)
        ld  de,8
        add hl,de
        ld  (scr_dst),hl
        ld  hl,scb_cnt
        dec (hl)
        jr  nz,.blit
        ret

; scroll_update: advance the banner by 1 pixel, recompute all 8
; rows into SCRBUF, then blit once
scroll_update:
        ld  hl,scr_bit
        ld  a,(hl)
        inc a
        cp  8
        jr  c,.gotbit
        xor a
        ld  hl,scr_byte
        ld  a,(hl)
        inc a
        cp  SCROLL_LEN
        jr  c,.gotbyte
        xor a
.gotbyte:
        ld  (scr_byte),a
        xor a
.gotbit:
        ld  (scr_bit),a
        ld  hl,scroll_row_tab
        ld  b,8
        ld  c,0
.rl:    push bc
        push hl
        ld  e,(hl)
        inc hl
        ld  d,(hl)              ; de = this row's table base address
        ld  a,(scr_byte)
        ld  l,a
        ld  h,0
        add hl,de               ; hl = table base + byte offset
        ld  a,c
        ld  (scr_rowidx),a
        call scroll_calc_row
        pop hl
        inc hl
        inc hl                  ; advance to next dw entry
        pop bc
        inc c
        djnz .rl
        call scroll_blit
        ret

; ------------------------------------------------------------
; title_setup: draw the whole title screen and start the music
; ------------------------------------------------------------
title_setup:
        di                       ; whole-screen VRAM writes must not be
                                 ; interrupted (H.TIMI can desync the VDP
                                 ; write-address latch mid-transfer)
        ld  hl,VR_NAME
        call SETWRT
        ld  c,3
.nt3:   xor a
.ntl:   out (098h),a
        nop
        nop
        inc a
        jr  nz,.ntl
        dec c
        jr  nz,.nt3

        ld  hl,VR_PAT
        xor a
        ld  bc,6144
        call vram_fill
        ld  hl,VR_COL
        ld  a,0F1h              ; black backdrop, white text/scroller -
                                 ; title_kbd repaints the keyboard rows
                                 ; back to white/black keys afterward
        ld  bc,6144
        call vram_fill

        ld  a,3
        ld  (ds_row),a
        ld  a,10
        ld  (ds_col),a
        ld  hl,title_str1
        call draw_string

        ld  a,6
        ld  (ds_row),a
        ld  a,6
        ld  (ds_col),a
        ld  hl,title_str2
        call draw_string

        call title_kbd
        call title_kbd_top
        call title_kbd_sep
        call title_kbd_black
        ei
        call music_init
        ret

; ------------------------------------------------------------
; melody_tab: dw period, db key(0-14), db frames ; FFFFh = loop
; bass_tab:   dw period, db frames               ; FFFFh = loop
; Transcribed from the public-domain (1866) Mutopia Project MIDI
; edition of Strauss II's "An der schonen blauen Donau" Waltz 1
; main theme (mutopiaproject.org, CC-BY-SA edition of a PD score),
; transposed from the edition's C major to the familiar D major and
; reduced to top melody line + a simple oom-pah-pah bass. 20-bar
; loop (5 four-bar phrases: I, I, vi, vi, IV->I climax on D6).
; ------------------------------------------------------------
melody_tab:
        dw P_D4
        db 0,16
        dw P_D4
        db 0,16
        dw P_FS4
        db 2,16
        dw P_A4
        db 4,48
        dw P_A5
        db 11,48
        dw P_FS5
        db 9,48
        dw P_D4
        db 0,16
        dw P_D4
        db 0,16
        dw P_FS4
        db 2,16
        dw P_A4
        db 4,48
        dw P_A5
        db 11,48
        dw P_G5
        db 10,48
        dw P_CS4
        db 6,16
        dw P_CS4
        db 6,16
        dw P_E4
        db 1,16
        dw P_B4
        db 5,48
        dw P_B5
        db 12,48
        dw P_G5
        db 10,48
        dw P_CS4
        db 6,16
        dw P_CS4
        db 6,16
        dw P_E4
        db 1,16
        dw P_B4
        db 5,48
        dw P_B5
        db 12,48
        dw P_FS5
        db 9,48
        dw P_D4
        db 0,16
        dw P_D4
        db 0,16
        dw P_FS4
        db 2,16
        dw P_A4
        db 4,16
        dw P_D5
        db 7,32
        dw P_D6
        db 14,48
        dw P_A5
        db 11,48
        ; coda (continuation of the same MIDI edition, bars 21+):
        ; repeats the D6 climax once more then winds down to a
        ; full cadence before the loop restarts
        dw P_E4
        db 1,16
        dw P_E4
        db 1,16
        dw P_G4
        db 3,16
        dw P_B4
        db 5,64
        dw P_GS4
        db 0FFh,16
        dw P_A4
        db 4,16
        dw P_FS5
        db 9,64
        dw P_D5
        db 7,16
        dw P_FS4
        db 2,48
        dw P_E4
        db 1,16
        dw P_B4
        db 5,32
        dw P_A4
        db 4,16
        dw P_D4
        db 0,24
        dw P_D5
        db 7,40
        dw 0FFFFh

bass_tab:
        ; bars1-8: tonic (D)
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        ; bars9-16: vi (B minor pedal)
        dw P_B3
        db 16
        dw P_B4
        db 16
        dw P_B4
        db 16
        dw P_B3
        db 16
        dw P_B4
        db 16
        dw P_B4
        db 16
        dw P_B3
        db 16
        dw P_B4
        db 16
        dw P_B4
        db 16
        dw P_B3
        db 16
        dw P_B4
        db 16
        dw P_B4
        db 16
        dw P_B3
        db 16
        dw P_B4
        db 16
        dw P_B4
        db 16
        dw P_B3
        db 16
        dw P_B4
        db 16
        dw P_B4
        db 16
        dw P_B3
        db 16
        dw P_B4
        db 16
        dw P_B4
        db 16
        dw P_B3
        db 16
        dw P_B4
        db 16
        dw P_B4
        db 16
        ; bar17: tonic (D) under the final pickup
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        ; bar18: IV (G)
        dw P_G3
        db 16
        dw P_G4
        db 16
        dw P_G4
        db 16
        ; bars19-20: tonic (D), climax + resolution
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        dw P_D3
        db 16
        dw P_D4
        db 16
        dw P_D4
        db 16
        ; coda: vi pedal, then IV, then back to tonic for the
        ; final cadence (matches the melody coda above)
        dw P_B3
        db 16
        dw P_B4
        db 16
        dw P_B4
        db 16
        dw P_B4
        db 64
        dw P_G3
        db 16
        dw P_G4
        db 16
        dw P_G4
        db 64
        dw P_G3
        db 16
        dw P_G4
        db 48
        dw P_D3
        db 16
        dw P_D4
        db 32
        dw P_D3
        db 16
        dw P_D4
        db 64
        dw 0FFFFh

        ; gfx_sprites (Sam's 12-pose sprite table, 1536 bytes) lives
        ; right after the code - not padded to exactly 06000h first,
        ; and leveldata.asm's own ORG below was removed too, so this
        ; table is free to spill across the bank0/bank1 boundary into
        ; bank1's space if bank0 doesn't have enough room left (it
        ; doesn't, once Room6's tables filled bank1 to where this used
        ; to live). Safe because both banks are FIXED (their switch
        ; registers are set once at boot and never touched again), so
        ; together they're one permanently-mapped, contiguous 16KB
        ; window - nothing like the switchable per-room background
        ; banks, where straddling a boundary would be a real bug.
gfx_sprites:
        INCBIN "src/sam_sprites.bin"

; lift_gfx: the rising/falling lift platform's sprite art (2 halves,
; 64 bytes total) - a single fixed design shared by every room that
; has a lift, not per-room data, so it lives here in bank0's spare
; space alongside gfx_sprites rather than in the tight bank1 window.
lift_gfx:
        INCBIN "src/lift_gfx.bin"

; ============================================================
;  BANK 1: level data (fixed at 6000, but see gfx_sprites above -
;  it may push this a little past 06000h if bank0 ran out of room)
; ============================================================
        INCLUDE "src/leveldata.asm"
        BLOCK 08000h-$,0FFh

; ============================================================
;  BANK 2: pre-rendered background PATTERN (fixed at 8000)
; ============================================================
        ORG 08000h
        INCBIN "src/bg_pattern.bin"
        ; enemy_gfx (64B) rides in this bank's spare tail - see the
        ; _write_room_bg comment in tools/gen_iso.py for why this is
        ; safe (BANK2R is already this room's own bank when read).
enemy_gfx:
        INCBIN "src/enemy_gfx.bin"
        BLOCK 0A000h-$,0FFh

; ============================================================
;  BANK 3: pre-rendered background COLOR (fixed at A000)
; ============================================================
        ORG 0A000h
        INCBIN "src/bg_color.bin"
keys_gfx:
        INCBIN "src/keys_gfx.bin"
exit_gfx_0:
        INCBIN "src/exit_gfx_0.bin"
exit_gfx_1:
        INCBIN "src/exit_gfx_1.bin"
        BLOCK 0C000h-$,0FFh

; ============================================================
;  BANKS 4-83: pre-computed occlusion mask windows (640KB, shared
;  by every room - pure projection geometry, not room content)
;  BANK 84: Central Cavern's crumbling-platform variants
; ============================================================
        ; (assembler warning about ORG overflow here is expected and
        ;  harmless: this is pure banked data, appended sequentially)
        INCBIN "src/mask.bin"
        INCBIN "src/crumb.bin"

; ============================================================
;  BANKS 85-86: room 2 (The Cold Room) pre-rendered background.
;  Bank numbers must match ROOM2_BGBANK/ROOM2_BGCOLBANK in
;  tools/gen_iso.py (baked into room_tab's bg_bank/bgcol_bank
;  fields, so they can't be equ-referenced from Python).
; ============================================================
ROOM2_BGBANK    equ 85
ROOM2_BGCOLBANK equ 86
        ORG 08000h
        INCBIN "src/bg_pattern2.bin"
bear_gfx:
        INCBIN "src/enemy_gfx2.bin"
        BLOCK 0A000h-$,0FFh
        ORG 0A000h
        INCBIN "src/bg_color2.bin"
keys_gfx2:
        INCBIN "src/keys_gfx2.bin"
exit_gfx2_0:
        INCBIN "src/exit_gfx2_0.bin"
exit_gfx2_1:
        INCBIN "src/exit_gfx2_1.bin"
        BLOCK 0C000h-$,0FFh

; ============================================================
;  BANK 87: room 2's own crumbling-platform variants (must match
;  CRUMBBANK2 in tools/gen_iso.py)
; ============================================================
CRUMBBANK2 equ 87
        INCBIN "src/crumb2.bin"

; ============================================================
;  BANKS 88-89: room 3 (The Menagerie) pre-rendered background.
;  Bank numbers must match ROOM3_BGBANK/ROOM3_BGCOLBANK in
;  tools/gen_iso.py.
; ============================================================
ROOM3_BGBANK    equ 88
ROOM3_BGCOLBANK equ 89
        ORG 08000h
        INCBIN "src/bg_pattern3.bin"
chicken_gfx:
        INCBIN "src/enemy_gfx3.bin"
        BLOCK 0A000h-$,0FFh
        ORG 0A000h
        INCBIN "src/bg_color3.bin"
keys_gfx3:
        INCBIN "src/keys_gfx3.bin"
exit_gfx3_0:
        INCBIN "src/exit_gfx3_0.bin"
exit_gfx3_1:
        INCBIN "src/exit_gfx3_1.bin"
        BLOCK 0C000h-$,0FFh

; ============================================================
;  BANK 90: room 3's own crumbling-platform variants (must match
;  CRUMBBANK3 in tools/gen_iso.py)
; ============================================================
CRUMBBANK3 equ 90
        INCBIN "src/crumb3.bin"

; ============================================================
;  BANKS 91-92: room 4 (Abandoned Uranium Workings) pre-rendered
;  background. Bank numbers must match ROOM4_BGBANK/ROOM4_BGCOLBANK
;  in tools/gen_iso.py. Room 4 has no crumbling platforms, so there
;  is no dedicated crumb bank for it (room_tab reuses CRUMBBANK).
; ============================================================
ROOM4_BGBANK    equ 91
ROOM4_BGCOLBANK equ 92
        ORG 08000h
        INCBIN "src/bg_pattern4.bin"
rat_gfx:
        INCBIN "src/enemy_gfx4.bin"
        BLOCK 0A000h-$,0FFh
        ORG 0A000h
        INCBIN "src/bg_color4.bin"
keys_gfx4:
        INCBIN "src/keys_gfx4.bin"
exit_gfx4_0:
        INCBIN "src/exit_gfx4_0.bin"
exit_gfx4_1:
        INCBIN "src/exit_gfx4_1.bin"
        BLOCK 0C000h-$,0FFh

; ============================================================
;  BANKS 93-94: room 5 (Eugene's Lair) pre-rendered background.
;  Bank numbers must match ROOM5_BGBANK/ROOM5_BGCOLBANK in
;  tools/gen_iso.py. Room 5 has no crumbling platforms, so there
;  is no dedicated crumb bank for it (room_tab reuses CRUMBBANK).
; ============================================================
ROOM5_BGBANK    equ 93
ROOM5_BGCOLBANK equ 94
        ORG 08000h
        INCBIN "src/bg_pattern5.bin"
eugene_gfx:
        INCBIN "src/enemy_gfx5.bin"
        BLOCK 0A000h-$,0FFh
        ORG 0A000h
        INCBIN "src/bg_color5.bin"
keys_gfx5:
        INCBIN "src/keys_gfx5.bin"
exit_gfx5_0:
        INCBIN "src/exit_gfx5_0.bin"
exit_gfx5_1:
        INCBIN "src/exit_gfx5_1.bin"
        BLOCK 0C000h-$,0FFh

; ============================================================
;  BANKS 95-96: room 6 (Processing Plant) pre-rendered background.
;  Bank numbers must match ROOM6_BGBANK/ROOM6_BGCOLBANK in
;  tools/gen_iso.py. Room 6 has no crumbling platforms, so there
;  is no dedicated crumb bank for it (room_tab reuses CRUMBBANK).
; ============================================================
ROOM6_BGBANK    equ 95
ROOM6_BGCOLBANK equ 96
        ORG 08000h
        INCBIN "src/bg_pattern6.bin"
pacman_gfx:
        INCBIN "src/enemy_gfx6.bin"
        BLOCK 0A000h-$,0FFh
        ORG 0A000h
        INCBIN "src/bg_color6.bin"
keys_gfx6:
        INCBIN "src/keys_gfx6.bin"
exit_gfx6_0:
        INCBIN "src/exit_gfx6_0.bin"
exit_gfx6_1:
        INCBIN "src/exit_gfx6_1.bin"
        BLOCK 0C000h-$,0FFh

; ============================================================
;  BANKS 97-98: room 7 (The Vat) pre-rendered background.
;  Bank numbers must match ROOM7_BGBANK/ROOM7_BGCOLBANK in
;  tools/gen_iso.py. Room 7 has no crumbling platforms, so there
;  is no dedicated crumb bank for it (room_tab reuses CRUMBBANK).
; ============================================================
ROOM7_BGBANK    equ 97
ROOM7_BGCOLBANK equ 98
        ORG 08000h
        INCBIN "src/bg_pattern7.bin"
guardian_gfx:
        INCBIN "src/enemy_gfx7.bin"
        BLOCK 0A000h-$,0FFh
        ORG 0A000h
        INCBIN "src/bg_color7.bin"
keys_gfx7:
        INCBIN "src/keys_gfx7.bin"
exit_gfx7_0:
        INCBIN "src/exit_gfx7_0.bin"
exit_gfx7_1:
        INCBIN "src/exit_gfx7_1.bin"
        BLOCK 0C000h-$,0FFh

; ============================================================
;  BANK 99: room 8's own crumbling-platform variants (must match
;  CRUMBBANK4 in tools/gen_iso.py)
; ============================================================
CRUMBBANK4 equ 99
        INCBIN "src/crumb4.bin"

; ============================================================
;  BANKS 100-101: room 8 (Kong Beast) pre-rendered background.
;  Bank numbers must match ROOM8_BGBANK/ROOM8_BGCOLBANK in
;  tools/gen_iso.py.
; ============================================================
ROOM8_BGBANK    equ 100
ROOM8_BGCOLBANK equ 101
        ORG 08000h
        INCBIN "src/bg_pattern8.bin"
kong_gfx:
        INCBIN "src/enemy_gfx8.bin"
        BLOCK 0A000h-$,0FFh
        ORG 0A000h
        INCBIN "src/bg_color8.bin"
keys_gfx8:
        INCBIN "src/keys_gfx8.bin"
exit_gfx8_0:
        INCBIN "src/exit_gfx8_0.bin"
exit_gfx8_1:
        INCBIN "src/exit_gfx8_1.bin"
        BLOCK 0C000h-$,0FFh

; ============================================================
;  BANKS 102-103: room 9 (Wacky Amoebatrons) pre-rendered background.
;  Bank numbers must match ROOM9_BGBANK/ROOM9_BGCOLBANK in
;  tools/gen_iso.py.
; ============================================================
ROOM9_BGBANK    equ 102
ROOM9_BGCOLBANK equ 103
        ORG 08000h
        INCBIN "src/bg_pattern9.bin"
urchin_gfx:
        INCBIN "src/enemy_gfx9.bin"
        BLOCK 0A000h-$,0FFh
        ORG 0A000h
        INCBIN "src/bg_color9.bin"
keys_gfx9:
        INCBIN "src/keys_gfx9.bin"
exit_gfx9_0:
        INCBIN "src/exit_gfx9_0.bin"
exit_gfx9_1:
        INCBIN "src/exit_gfx9_1.bin"
        BLOCK 0C000h-$,0FFh

; ============================================================
;  BANK 104: room 9's own crumbling-platform variants (must match
;  CRUMBBANK9 in tools/gen_iso.py)
; ============================================================
CRUMBBANK9 equ 104
        INCBIN "src/crumb9.bin"

; ============================================================
;  BANK 105: room 9's SECOND crumbling-platform bank (floor2 - must
;  match CRUMBBANK9B in tools/gen_iso.py). Added once floor1+step+
;  floor2 together (26400 bytes as solo cells) proved too big for one
;  8KB bank - each crumb_tab row now carries its own bank byte, so a
;  room's groups can be split across more than one crumble bank.
; ============================================================
CRUMBBANK9B equ 105
        INCBIN "src/crumb9b.bin"

        ; pad the ROM back out to a full 1MB (128 x 8KB banks) - openMSX's
        ; ascii8 mapper expects a power-of-two file size; a short file
        ; (as left by just rounding up to the next bank) fails to boot
        ; at all (falls through to plain MSX BASIC). Measured then
        ; computed exactly (1048576 - actual size before this BLOCK),
        ; not guessed by hand. 106 banks now used (0-105), so 22 banks
        ; (106-127) remain: 22*8192 = 180224.
        BLOCK 180224,0FFh
