# Room 6 (Processing Plant) end-to-end check: debug letter-select,
# conveyor arrival key, catwalk key (pacman-guarded), side-platform key,
# BOTH mirrored pacmen's kill-zone independently, and the exit/win chain
# (Room6 is now the last room).

# letter-select room 6 (0-indexed room 5): row3 bit3 = 'F'
after time 6 { keymatrixdown 3 0x08 }
after time 6.3 { keymatrixup 3 0x08 }

set ::out [open ./build/plant_log.txt w]
proc snap {label} {
    puts $::out "$label: keys=[debug read memory 0xC00C] lives=[debug read memory 0xC04C] room=[debug read memory 0xC06C] sam_fl=[debug read memory 0xC00A] sam_h=[debug read memory 0xC007]"
}

after time 9 {
    snap "baseline"
    puts $::out "room_en_axis=[debug read memory 0xC092] centerx=[debug read memory 0xC093] enz=[debug read memory 0xC090] ensurf=[debug read memory 0xC091] enxmin=[debug read memory 0xC08E] enxmax=[debug read memory 0xC08F]"
    screenshot -raw ./build/plant_overview.png
}

# conveyor arrival platform (6,3,y=1) -> wx=104,wz=56,surf=16
after time 9.3 {
    debug write memory 0xC004 104
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.35 { snap "conveyor platform (want keys=1)" }

# side platform (2,5,y=1) -> wx=40,wz=88,surf=16
after time 9.5 {
    debug write memory 0xC004 40
    debug write memory 0xC005 88
    debug write memory 0xC007 16
}
after time 9.55 { snap "side platform (want keys=2)" }

# catwalk center (3,2,y=3) -> wx=56,wz=40,surf=32 - away from either
# pacman extreme for now, just checking the key itself
after time 9.7 {
    debug write memory 0xC08E 6
    debug write memory 0xC08F 6
    debug write memory 0xC046 6
    debug write memory 0xC004 56
    debug write memory 0xC005 40
    debug write memory 0xC007 32
}
after time 9.75 { snap "catwalk center, pacmen forced to min gap (want keys=3)" }
after time 9.8 { screenshot -raw ./build/plant_platforms.png }

# pacman kill-zone, LEFT one: force en_x (gap) so pos1=centerx-en_x
# lands right on Sam's position
after time 10.1 {
    debug write memory 0xC00C 3
    debug write memory 0xC04C 5
    debug write memory 0xC004 56
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 32
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC08E 0
    debug write memory 0xC08F 0
    debug write memory 0xC046 0
}
after time 10.2 { snap "pacman1 (left) on top of Sam (want lives dropped by 1)" }
after time 10.7 { snap "pacman1-kill-settled" }

# pacman kill-zone, RIGHT one: pos2=centerx+en_x - use a nonzero gap so
# pos1 is safely clear, only pos2 lands on Sam
after time 11.0 {
    debug write memory 0xC04C 5
    debug write memory 0xC004 76
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 32
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC08E 20
    debug write memory 0xC08F 20
    debug write memory 0xC046 20
}
after time 11.1 { snap "pacman2 (right) on top of Sam (want lives dropped again)" }
after time 11.6 { snap "pacman2-kill-settled" }
after time 11.7 { screenshot -raw ./build/plant_pacman.png }

# both pacmen safely far (wide gap), Sam standing at center - must NOT die
after time 12.0 {
    debug write memory 0xC04C 5
    debug write memory 0xC00C 3
    debug write memory 0xC004 56
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 32
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC08E 24
    debug write memory 0xC08F 24
    debug write memory 0xC046 24
}
after time 12.1 { snap "both pacmen wide, Sam at center (want lives UNCHANGED)" }
after time 12.6 { snap "wide-gap-settled" }

# exit: stand on the exit platform (4,5,y=1) -> wx=72,wz=88,surf=16
after time 13.0 {
    debug write memory 0xC004 72
    debug write memory 0xC005 88
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 13.1 { snap "at-exit" }
after time 13.2 { screenshot -raw ./build/plant_exit.png }
after time 15.7 {
    set wond [debug read memory 0xC06A]
    set room [debug read memory 0xC06C]
    puts $::out "exit-settled: won_t=$wond room=$room (Room6 is last room - room should stay 5, won_t blinking >0)"
    screenshot -raw ./build/plant_exit_settled.png
}

after time 16.2 {
    close $::out
    exit
}
