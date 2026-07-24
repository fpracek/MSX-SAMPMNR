# Room 9 (Wacky Amoebatrons) end-to-end check - REDESIGNED layout
# (Fausto: "ridisegna l'intero schema"): two floors (y=2 then y=5),
# each a 2-cluster pair split by a gap, joined by a stepping stone,
# plus a top platform guarded by the urchin's vertical patrol. Plus
# (Fausto, after confirming the redesign works): crumbling platforms
# on the climb floors and static obstacles scattered on the fixed
# platforms. Plus (Fausto again, once that was visible): floor1 and
# the step are DWELL-based crumble (room_crumb_continuous=1) -
# standing still keeps destroying the platform every CRUMB_DWELL
# frames, no need to step off and back on. Plus (Fausto, once more:
# "prova a rendere friabili anche le piattaforme piu' in alto"):
# floor2 now crumbles too, via a SECOND crumble bank (CRUMBBANK9B) -
# floor1+step+floor2 together didn't fit one 8KB crumble bank, so
# each crumb_tab row now carries its own bank byte instead of one
# bank room-wide. Debug letter-select, 3 keys (one per floor + top),
# dwell-crumble degrade (both banks), hazard kills, urchin vertical-
# patrol kill, and the exit/win chain (Room9 is still the last room).
# All non-exit checks run BEFORE the exit/win trigger - once won_t
# starts blinking, the last-room infinite-blink state stops running
# normal per-frame gameplay (hazard_check/cell_at), so any test that
# needs live collision must happen first.
#
# RAM addresses below are POST cr_cellst-resize (RESB 15->25) + new
# cb_bank byte - regenerate build/main.sym and re-derive every address
# here again if any new RESB is ever added before these fields (see
# the sampr-miner-project memory for why). cr_cellst's OWN base
# (0xC021) and the first 8 groups' ids (0-14, floor1+step) are
# unchanged from before this round; only the shared globals after it
# (lives, current_room, won_t, en_x, en_dir, every room_en* field)
# shifted by +11.

# letter-select room 9 (0-indexed room 8): row3 bit6 = 'I'
after time 6 { keymatrixdown 3 0x40 }
after time 6.3 { keymatrixup 3 0x40 }

set ::out [open ./build/amoeba_log.txt w]
proc snap {label} {
    puts $::out "$label: keys=[debug read memory 0xC00C] lives=[debug read memory 0xC064] room=[debug read memory 0xC084] sam_fl=[debug read memory 0xC00A] sam_h=[debug read memory 0xC007]"
}

after time 9 {
    snap "baseline"
    puts $::out "en_axis=[debug read memory 0xC0AA] enz=[debug read memory 0xC0A8] ensurf=[debug read memory 0xC0A9] enxmin=[debug read memory 0xC0A6] enxmax=[debug read memory 0xC0A7]"
    screenshot -raw ./build/amoeba_overview.png
}

# key1: floor1 west (bx=2,bz=3,y=2) -> wx=40,wz=56,surf=24
after time 9.3 {
    debug write memory 0xC004 40
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 24
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.35 { snap "key1 on floor1 west (want keys=1)" }

# key2: floor2 west (bx=2,bz=1,y=5) -> wx=40,wz=24,surf=48
after time 9.5 {
    debug write memory 0xC004 40
    debug write memory 0xC005 24
    debug write memory 0xC007 48
}
after time 9.55 { snap "key2 on floor2 west (want keys=2)" }

# key3: floor2 east, past the urchin (bx=5,bz=1,y=5) -> wx=88,wz=24,surf=48
after time 9.7 {
    debug write memory 0xC004 88
    debug write memory 0xC005 24
    debug write memory 0xC007 48
}
after time 9.75 { snap "key3 on floor2 east (want keys=3)" }
after time 9.8 { screenshot -raw ./build/amoeba_keys.png }

# --- dwell-based crumble (Fausto: "sampr non puo' fermarsi su una
# piattaforma senza che lei si distrugga completamente") - land once
# and just WAIT, no leave-and-return needed. crumb_units order is
# [(1,3,2)],[(2,3,2)],[(3,3,2)],[(5,3,2)],[(1,2,4)],[(3,2,4)],
# [(4,2,4)],[(5,2,4)],[(1,1,5)],[(2,1,5)],[(3,1,5)],[(4,1,5)],[(5,1,5)]
# -> id=groupindex*2, so floor1(5,3,2) is group3 -> id6 ->
# cr_cellst[6] = 0xC021+6 = 0xC027; step(3,2,4) is group5 -> id10 ->
# cr_cellst[10] = 0xC021+10 = 0xC02B; floor2(1,1,5) is group8 -> id16
# -> cr_cellst[16] = 0xC021+16 = 0xC031 (bank 'b', CRUMBBANK9B - this
# is the one that actually proves the SECOND crumble bank works).

# land on floor1(5,3) -> wx=88,wz=56,surf=24 - fresh touch cracks it
# instantly (stage 0->1)
after time 10.0 {
    debug write memory 0xC004 88
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 24
    debug write memory 0xC00A 1
}
after time 10.1 {
    puts $::out "dwell floor1(5,3) fresh touch: cr_cellst\[6\]=[debug read memory 0xC027] (want 1)"
}
# no further pokes - Sam just sits there. After CRUMB_DWELL=18 frames
# of continuous dwelling it must degrade again on its own (stage 1->2,
# destroyed) without ever stepping off.
after time 10.6 {
    puts $::out "dwell floor1(5,3) after continuous standing: cr_cellst\[6\]=[debug read memory 0xC027] (want 2, destroyed while never leaving)"
}

# land on step(3,2) -> wx=56,wz=40,surf=40 - same story
after time 11.0 {
    debug write memory 0xC004 56
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 40
    debug write memory 0xC00A 1
}
after time 11.1 {
    puts $::out "dwell step(3,2) fresh touch: cr_cellst\[10\]=[debug read memory 0xC02B] (want 1)"
}
after time 11.6 {
    puts $::out "dwell step(3,2) after continuous standing: cr_cellst\[10\]=[debug read memory 0xC02B] (want 2, destroyed while never leaving)"
}

# land on floor2(1,1) -> wx=24,wz=24,surf=48 - the SECOND crumble
# bank (CRUMBBANK9B) - same dwell story, proves bank-switching works
after time 12.0 {
    debug write memory 0xC004 24
    debug write memory 0xC005 24
    debug write memory 0xC006 0
    debug write memory 0xC007 48
    debug write memory 0xC00A 1
}
after time 12.1 {
    puts $::out "dwell floor2(1,1) [bank b] fresh touch: cr_cellst\[16\]=[debug read memory 0xC031] (want 1)"
}
after time 12.6 {
    puts $::out "dwell floor2(1,1) [bank b] after continuous standing: cr_cellst\[16\]=[debug read memory 0xC031] (want 2, destroyed while never leaving)"
}

# hazard test 1: floor1 obstacle at (4,3,24), kill ceiling 34. Standing
# there at h+1=25 (<34) must die. wx=72,wz=56.
after time 13.0 {
    debug write memory 0xC064 5
    debug write memory 0xC004 72
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 24
    debug write memory 0xC00A 1
}
after time 13.1 {
    puts $::out "hazard floor1(4,3): lives=[debug read memory 0xC064] (want dropped from 5)"
}
# same height, DIFFERENT (still-intact) floor1 cell (1,3) - must stay
# safe (no death) - a cell that hasn't been dwelt-on in this test yet
after time 13.4 {
    debug write memory 0xC064 5
    debug write memory 0xC004 24
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 24
    debug write memory 0xC00A 1
}
after time 13.5 {
    puts $::out "floor1(1,3) same height off-hazard: lives=[debug read memory 0xC064] (want still 5)"
}

# hazard test 2: step obstacle at (2,2,40), kill ceiling 50. Standing
# there at h+1=41 (<50) must die. wx=40,wz=40.
after time 13.8 {
    debug write memory 0xC064 5
    debug write memory 0xC004 40
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 40
    debug write memory 0xC00A 1
}
after time 13.9 {
    puts $::out "hazard step(2,2): lives=[debug read memory 0xC064] (want dropped from 5)"
}
# same height, DIFFERENT (still-intact) step cell (1,2) - must stay safe
after time 14.2 {
    debug write memory 0xC064 5
    debug write memory 0xC004 24
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 40
    debug write memory 0xC00A 1
}
after time 14.3 {
    puts $::out "step(1,2) same height off-hazard: lives=[debug read memory 0xC064] (want still 5)"
}

# urchin kill: force en_x (height) onto Sam at the fixed column (64,24)
after time 15.0 {
    debug write memory 0xC064 5
    debug write memory 0xC004 64
    debug write memory 0xC005 24
    debug write memory 0xC006 0
    debug write memory 0xC007 48
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC059 40
    debug write memory 0xC05A 0
}
after time 15.05 { snap "urchin on top of Sam (want lives dropped)" }
after time 15.5 { snap "urchin-kill-settled" }
after time 15.6 { screenshot -raw ./build/amoeba_urchin.png }

# exit: (bx=6,bz=1,y=6) -> wx=104,wz=24,surf=56, all keys forced
after time 16.0 {
    debug write memory 0xC00C 3
    debug write memory 0xC064 5
    debug write memory 0xC004 104
    debug write memory 0xC005 24
    debug write memory 0xC006 0
    debug write memory 0xC007 56
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC059 200
}
after time 16.1 { snap "at-exit" }
after time 16.2 { screenshot -raw ./build/amoeba_exit.png }
after time 18.7 {
    set wond [debug read memory 0xC082]
    set room [debug read memory 0xC084]
    puts $::out "exit-settled: won_t=$wond room=$room (Room9 is last room - room should stay 8, won_t blinking >0)"
    screenshot -raw ./build/amoeba_exit_settled.png
}

after time 19.2 {
    close $::out
    exit
}
