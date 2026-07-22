# Room 4 (Abandoned Uranium Workings) end-to-end check: debug
# letter-select, twin platforms + keys, uranium-bar hazard kill,
# rat kill-zone, and the exit/win chain (Room4 is now the last room).

after time 6 { keymatrixdown 3 0x02 }
after time 6.3 { keymatrixup 3 0x02 }

set ::out [open ./build/uranium_log.txt w]
proc snap {label} {
    puts $::out "$label: keys=[debug read memory 0xC00C] lives=[debug read memory 0xC04C] room=[debug read memory 0xC06C] sam_fl=[debug read memory 0xC00A]"
}

after time 9 {
    snap "baseline"
    screenshot -raw ./build/uranium_overview.png
    # neutralize the rat (it patrols the exact same lane/height as the
    # twin platforms - working as intended, but would confound the key
    # checks below the same way the chicken did in Room3's testing).
    # Directly teleport en_x too, not just the bounds - changing only
    # room_enxmin/enxmax leaves en_x migrating there gradually (0.5px/
    # frame), which isn't far enough away in time for the platform2
    # check below and gets Sam killed by the rat mid-test instead.
    debug write memory 0xC08E 200
    debug write memory 0xC08F 208
    debug write memory 0xC046 204
}

# platform1 (3,2,y=3) -> wx=56,wz=40,surf=32 - snapshot fast, no dwell
after time 9.5 {
    debug write memory 0xC004 56
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 32
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.55 { snap "platform1 (want keys=1)" }

# platform2 (5,2,y=3) -> wx=88,wz=40,surf=32
after time 9.7 {
    debug write memory 0xC004 88
    debug write memory 0xC005 40
    debug write memory 0xC007 32
}
after time 9.75 { snap "platform2 (want keys=2)" }
after time 9.8  { screenshot -raw ./build/uranium_platforms.png }

# platform3/fixed (6,1,y=1) -> wx=104,wz=24,surf=16
after time 9.95 {
    debug write memory 0xC004 104
    debug write memory 0xC005 24
    debug write memory 0xC007 16
}
after time 10.0 { snap "platform3 (want keys=3)" }

# uranium bar hazard1 (1,2,surf=8) -> wx=24,wz=40
after time 10.3 {
    debug write memory 0xC004 24
    debug write memory 0xC005 40
    debug write memory 0xC007 8
}
after time 10.4 { snap "on-hazard1 (want lives dropped by 1)" }
after time 11   { snap "hazard1-settled" }
after time 11.1 { screenshot -raw ./build/uranium_hazard.png }

# re-enable the rat and deliberately test its kill-zone
after time 11.5 {
    debug write memory 0xC08E 48
    debug write memory 0xC08F 96
}
after time 12.5 {
    set ex [debug read memory 0xC046]
    puts $::out "rat en_x=$ex"
    debug write memory 0xC004 $ex
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 32
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 12.7 { snap "on-rat (want lives dropped again)" }
after time 13.3 { snap "rat-settled" }
after time 13.4 { screenshot -raw ./build/uranium_rat.png }

# exit: restore keys/lives, stand on exit cube (6,4,y=1) -> wx=104,wz=72,surf=16
after time 14 {
    debug write memory 0xC04C 5
    debug write memory 0xC00C 3
    debug write memory 0xC004 104
    debug write memory 0xC005 72
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 14.3 { snap "at-exit" }
after time 14.4 { screenshot -raw ./build/uranium_exit.png }
after time 17 {
    set wond [debug read memory 0xC06A]
    set room [debug read memory 0xC06C]
    puts $::out "exit-settled: won_t=$wond room=$room (Room4 is last room - room should stay 3, won_t blinking >0)"
    screenshot -raw ./build/uranium_exit_settled.png
}

after time 17.5 {
    close $::out
    exit
}
