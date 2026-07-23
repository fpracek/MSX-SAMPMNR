# Room 9 (Wacky Amoebatrons) end-to-end check: debug letter-select, 3
# keys (one per tier), amoeba hazard kill, urchin vertical-patrol kill,
# and the exit/win chain (Room9 is now the last room).

# letter-select room 9 (0-indexed room 8): row3 bit6 = 'I'
after time 6 { keymatrixdown 3 0x40 }
after time 6.3 { keymatrixup 3 0x40 }

set ::out [open ./build/amoeba_log.txt w]
proc snap {label} {
    puts $::out "$label: keys=[debug read memory 0xC00C] lives=[debug read memory 0xC050] room=[debug read memory 0xC070] sam_fl=[debug read memory 0xC00A] sam_h=[debug read memory 0xC007]"
}

after time 9 {
    snap "baseline"
    puts $::out "en_axis=[debug read memory 0xC096] enz=[debug read memory 0xC094] ensurf=[debug read memory 0xC095] enxmin=[debug read memory 0xC092] enxmax=[debug read memory 0xC093]"
    screenshot -raw ./build/amoeba_overview.png
}

# key1: stand on cluster A2 (2,2,2) -> wx=40,wz=40,surf=24
after time 9.3 {
    debug write memory 0xC004 40
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 24
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.35 { snap "key1 on clusterA2 (want keys=1)" }

# key2: stand on cluster C2 (2,3,5) -> wx=40,wz=56,surf=48
after time 9.5 {
    debug write memory 0xC004 40
    debug write memory 0xC005 56
    debug write memory 0xC007 48
}
after time 9.55 { snap "key2 on clusterC2 (want keys=2)" }

# key3: stand on top platform (6,2,6) -> wx=104,wz=40,surf=56
after time 9.7 {
    debug write memory 0xC004 104
    debug write memory 0xC005 40
    debug write memory 0xC007 56
}
after time 9.75 { snap "key3 on top platform (want keys=3)" }
after time 9.8 { screenshot -raw ./build/amoeba_keys.png }

# amoeba hazard kill: stand at hazard cell (3,2) floor level -> wx=56,wz=40,surf=8
after time 10.0 {
    debug write memory 0xC004 56
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 10.05 { snap "on amoeba hazard (want lives dropped by 1)" }
after time 10.5 { snap "hazard-kill-settled" }

# urchin kill: force en_x (height) onto Sam at the fixed column (72,56)
after time 11.0 {
    debug write memory 0xC004 72
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 56
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC046 56
    debug write memory 0xC047 0
}
after time 11.05 { snap "urchin on top of Sam (want lives dropped again)" }
after time 11.5 { snap "urchin-kill-settled" }
after time 11.6 { screenshot -raw ./build/amoeba_urchin.png }

# exit: stand on exit platform (7,2,6) -> wx=120,wz=40,surf=56, all keys forced
after time 12.0 {
    debug write memory 0xC00C 3
    debug write memory 0xC050 5
    debug write memory 0xC004 120
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 56
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC046 200
}
after time 12.1 { snap "at-exit" }
after time 12.2 { screenshot -raw ./build/amoeba_exit.png }
after time 14.7 {
    set wond [debug read memory 0xC06E]
    set room [debug read memory 0xC070]
    puts $::out "exit-settled: won_t=$wond room=$room (Room9 is last room - room should stay 8, won_t blinking >0)"
    screenshot -raw ./build/amoeba_exit_settled.png
}

after time 15.2 {
    close $::out
    exit
}
