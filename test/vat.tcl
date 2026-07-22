# Room 7 (The Vat) end-to-end check: debug letter-select, west platform
# key, 2 field keys (tucked between hazards), spark-hazard kill, guardian
# patrol kill, and the exit/win chain (Room7 is now the last room).

# letter-select room 7 (0-indexed room 6): row3 bit4 = 'G'
after time 6 { keymatrixdown 3 0x10 }
after time 6.3 { keymatrixup 3 0x10 }

set ::out [open ./build/vat_log.txt w]
proc snap {label} {
    puts $::out "$label: keys=[debug read memory 0xC00C] lives=[debug read memory 0xC04C] room=[debug read memory 0xC06C] sam_fl=[debug read memory 0xC00A] sam_h=[debug read memory 0xC007]"
}

after time 9 {
    snap "baseline"
    puts $::out "room_en_axis=[debug read memory 0xC092] enz=[debug read memory 0xC090] ensurf=[debug read memory 0xC091] enxmin=[debug read memory 0xC08E] enxmax=[debug read memory 0xC08F]"
    screenshot -raw ./build/vat_overview.png
}

# west key platform (2,2,y=1) -> wx=40,wz=40,surf=16
after time 9.3 {
    debug write memory 0xC004 40
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.35 { snap "west platform key (want keys=1)" }

# field key 2 (4,3,y=1), on open floor between hazard cells -> wx=72,wz=56
after time 9.5 {
    debug write memory 0xC004 72
    debug write memory 0xC005 56
    debug write memory 0xC007 16
}
after time 9.55 { snap "field key2 (want keys=2)" }

# field key 3 (5,4,y=1) -> wx=88,wz=72
after time 9.7 {
    debug write memory 0xC004 88
    debug write memory 0xC005 72
    debug write memory 0xC007 16
}
after time 9.75 { snap "field key3 (want keys=3)" }
after time 9.8 { screenshot -raw ./build/vat_keys.png }

# spark hazard kill: stand exactly on hazard cell (3,1) -> wx=56,wz=24,
# floor height surf=8 (no platform there)
after time 10.0 {
    debug write memory 0xC004 56
    debug write memory 0xC005 24
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 10.05 { snap "on spark hazard (want lives dropped by 1)" }
after time 10.5 { snap "hazard-kill-settled" }
after time 10.6 { screenshot -raw ./build/vat_hazard.png }

# guardian kill: force the patrol (en_x) onto Sam's own position, well
# clear of any hazard cell so only the guardian is being tested
after time 11.0 {
    debug write memory 0xC004 90
    debug write memory 0xC005 88
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC046 90
    debug write memory 0xC047 0
}
after time 11.05 { snap "guardian on top of Sam (want lives dropped again)" }
after time 11.5 { snap "guardian-kill-settled" }
after time 11.6 { screenshot -raw ./build/vat_guardian.png }

# exit: stand on the exit platform (7,5,y=1) -> wx=120,wz=88,surf=16,
# with all 3 keys forced (bypassing the hazard/guardian gauntlet itself -
# that live-timing feasibility is checked separately)
after time 12.0 {
    debug write memory 0xC00C 3
    debug write memory 0xC04C 5
    debug write memory 0xC004 120
    debug write memory 0xC005 88
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC046 200
}
after time 12.1 { snap "at-exit" }
after time 12.2 { screenshot -raw ./build/vat_exit.png }
after time 14.7 {
    set wond [debug read memory 0xC06A]
    set room [debug read memory 0xC06C]
    puts $::out "exit-settled: won_t=$wond room=$room (Room7 is last room - room should stay 6, won_t blinking >0)"
    screenshot -raw ./build/vat_exit_settled.png
}

after time 15.2 {
    close $::out
    exit
}
