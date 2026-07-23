# Room 8 (Kong Beast) end-to-end check: debug letter-select, 3
# crumbling-platform keys, dagger hazard kill, Kong beast patrol kill,
# lift bounce fields, and the exit/win chain (Room8 is now the last
# room).

# letter-select room 8 (0-indexed room 7): row3 bit5 = 'H'
after time 6 { keymatrixdown 3 0x20 }
after time 6.3 { keymatrixup 3 0x20 }

set ::out [open ./build/kong_log.txt w]
proc snap {label} {
    puts $::out "$label: keys=[debug read memory 0xC00C] lives=[debug read memory 0xC04F] room=[debug read memory 0xC06F] sam_fl=[debug read memory 0xC00A] sam_h=[debug read memory 0xC007]"
}

after time 9 {
    snap "baseline"
    puts $::out "lift_wx=[debug read memory 0xC097] lift_wz=[debug read memory 0xC098] lift_ymin=[debug read memory 0xC099] lift_ymax=[debug read memory 0xC09A] lift_h=[debug read memory 0xC049] on_lift=[debug read memory 0xC04B]"
    screenshot -raw ./build/kong_overview.png
}

# crumbling key1 (3,3,7) -> wx=56,wz=56,surf=64 (y=7 -> 8*8=64)
after time 9.3 {
    debug write memory 0xC004 56
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 64
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.35 { snap "key1 on crumbling platform (want keys=1)" }

# crumbling key2 (4,2,7) -> wx=72,wz=40,surf=64
after time 9.5 {
    debug write memory 0xC004 72
    debug write memory 0xC005 40
    debug write memory 0xC007 64
}
after time 9.55 { snap "key2 (want keys=2)" }

# crumbling key3 (5,3,7) -> wx=88,wz=56,surf=64
after time 9.7 {
    debug write memory 0xC004 88
    debug write memory 0xC005 56
    debug write memory 0xC007 64
}
after time 9.75 { snap "key3 (want keys=3)" }
after time 9.8 { screenshot -raw ./build/kong_keys.png }

# dagger hazard kill: stand on hazard cell (6,1) -> wx=104,wz=24,surf=8
after time 10.0 {
    debug write memory 0xC004 104
    debug write memory 0xC005 24
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 10.05 { snap "on dagger hazard (want lives dropped by 1)" }
after time 10.5 { snap "hazard-kill-settled" }

# Kong beast kill: force en_x onto Sam's position at the beast's row
after time 11.0 {
    debug write memory 0xC004 72
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 56
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC046 72
    debug write memory 0xC047 0
}
after time 11.05 { snap "kong on top of Sam (want lives dropped again)" }
after time 11.5 { snap "kong-kill-settled" }
after time 11.6 { screenshot -raw ./build/kong_beast.png }

# exit: stand on exit platform (4,4,6) -> wx=72,wz=72,surf=56, all keys forced
after time 12.0 {
    debug write memory 0xC00C 3
    debug write memory 0xC04F 5
    debug write memory 0xC004 72
    debug write memory 0xC005 72
    debug write memory 0xC006 0
    debug write memory 0xC007 56
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC046 200
}
after time 12.1 { snap "at-exit" }
after time 12.2 { screenshot -raw ./build/kong_exit.png }
after time 14.7 {
    set wond [debug read memory 0xC06D]
    set room [debug read memory 0xC06F]
    puts $::out "exit-settled: won_t=$wond room=$room (Room8 is last room - room should stay 7, won_t blinking >0)"
    screenshot -raw ./build/kong_exit_settled.png
}

after time 15.2 {
    close $::out
    exit
}
