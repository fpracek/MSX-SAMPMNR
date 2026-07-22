# Room 5 (Eugene's Lair) end-to-end check: debug letter-select, the
# 3 platform keys, Eugene's NEW vertical kill-zone (room_en_axis=1 -
# both the "overlap kills" and "clear height is safe" cases, to prove
# the axis reinterpretation is wired correctly and not just reusing
# the old horizontal check), the chasm pit-death, and the exit/win
# chain (Room5 is now the last room).

# letter-select room 5 (0-indexed room 4): row3 bit2 = 'E' - this is a
# one-shot check at the title screen only (debug_room_key commits and
# jumps into main_loop as soon as any letter registers), so it must be
# the ONLY letter pressed, and early.
after time 6 { keymatrixdown 3 0x04 }
after time 6.3 { keymatrixup 3 0x04 }

set ::out [open ./build/eugene_log.txt w]
proc snap {label} {
    puts $::out "$label: keys=[debug read memory 0xC00C] lives=[debug read memory 0xC04C] room=[debug read memory 0xC06C] sam_fl=[debug read memory 0xC00A] sam_h=[debug read memory 0xC007]"
}

after time 9 {
    snap "baseline"
    puts $::out "room_en_axis=[debug read memory 0xC092] enz=[debug read memory 0xC090] ensurf=[debug read memory 0xC091] enxmin=[debug read memory 0xC08E] enxmax=[debug read memory 0xC08F]"
    screenshot -raw ./build/eugene_overview.png
}

# low platform (6,3,y=1) -> wx=104,wz=56,surf=16
after time 9.5 {
    debug write memory 0xC004 104
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.55 { snap "low platform (want keys=1)" }

# platform A (5,2,y=3) -> wx=88,wz=40,surf=32
after time 9.7 {
    debug write memory 0xC004 88
    debug write memory 0xC005 40
    debug write memory 0xC007 32
}
after time 9.75 { snap "platform A (want keys=2)" }

# platform B (3,2,y=3) -> wx=56,wz=40,surf=32
after time 9.9 {
    debug write memory 0xC004 56
    debug write memory 0xC005 40
}
after time 9.95 { snap "platform B (want keys=3)" }
after time 10.0 { screenshot -raw ./build/eugene_platforms.png }

# Eugene kill-zone, OVERLAP case: stand on the exit island (2,2,y=0)
# wx=40,wz=40,surf=8, force his height (en_x) to sit right on Sam's
# body band -> must die
after time 10.3 {
    debug write memory 0xC004 40
    debug write memory 0xC005 40
    debug write memory 0xC007 8
    debug write memory 0xC00A 1
    debug write memory 0xC046 8
}
after time 10.4 { snap "on-exit, eugene overlapping (want lives dropped by 1)" }
after time 11   { snap "eugene-overlap-settled" }
after time 11.1 { screenshot -raw ./build/eugene_kill.png }

# Eugene kill-zone, CLEAR case: same spot, but his height is up near
# the platform level, well clear of Sam's band -> must NOT die. This
# is the case that specifically proves the room_en_axis=1 branch is
# really comparing en_x-as-height against sam_h, not silently falling
# back to the old horizontal (world x/z) comparison.
after time 11.5 {
    debug write memory 0xC04C 5
    debug write memory 0xC004 40
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC046 44
}
after time 11.6 { snap "on-exit, eugene clear (want lives UNCHANGED)" }
after time 12.1 { snap "eugene-clear-settled" }
after time 12.2 { screenshot -raw ./build/eugene_safe.png }

# chasm pit-death: drop Sam mid-air over a gapped cell (1,1) - wx=24,
# wz=24 - with height already at the bottom and airborne, to prove
# floor_gaps really removed the floor tile there (not just its art)
after time 12.5 {
    debug write memory 0xC004 24
    debug write memory 0xC005 24
    debug write memory 0xC006 0
    debug write memory 0xC007 0
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 0
}
after time 12.6 { snap "over-the-chasm (want lives dropped again)" }
after time 13.1 { snap "chasm-settled" }
after time 13.2 { screenshot -raw ./build/eugene_pit.png }

# exit: restore keys/lives, stand on the exit island with Eugene safely
# clear, confirm the win chain starts (Room5 is the last room, so
# current_room should stay at 4 with won_t blinking forever)
after time 13.5 {
    debug write memory 0xC04C 5
    debug write memory 0xC00C 3
    debug write memory 0xC004 40
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC046 44
}
after time 13.8 { snap "at-exit" }
after time 13.9 { screenshot -raw ./build/eugene_exit.png }
after time 16.5 {
    set wond [debug read memory 0xC06A]
    set room [debug read memory 0xC06C]
    puts $::out "exit-settled: won_t=$wond room=$room (Room5 is last room - room should stay 4, won_t blinking >0)"
    screenshot -raw ./build/eugene_exit_settled.png
}

after time 17 {
    close $::out
    exit
}
