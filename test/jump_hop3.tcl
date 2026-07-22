# Hop 3: twin platform2 (5,2,y=3,surf=32) -> twin platform1
# (3,2,y=3,surf=32), a pure horizontal jump clearing the 1-tile gap
# (bx=4, no platform there) at the same height.

after time 6 { keymatrixdown 3 0x02 }
after time 6.3 { keymatrixup 3 0x02 }

set ::out [open ./build/jump_hop3_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] fl=[debug read memory 0xC00A] keys=[debug read memory 0xC00C]"
}

after time 9 {
    debug write memory 0xC08E 200
    debug write memory 0xC08F 208
    debug write memory 0xC046 204
    # start on platform2, near its west edge, keys already at 2 (as if
    # arriving fresh from hop2)
    debug write memory 0xC004 82
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 32
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    debug write memory 0xC00C 2
    snap "start"
}
after time 9.2 {
    keymatrixdown 8 0x01
}
after time 9.24 {
    keymatrixdown 8 0x10
}
after time 9.7 {
    keymatrixup 8 0x10
}
foreach t {9.3 9.4 9.5 9.6 9.7 9.8 9.9 10.0 10.2 10.4 10.6} {
    after time $t "snap t=$t"
}
after time 10.7 {
    keymatrixup 8 0x01
    snap "released"
}
after time 10.9 {
    close $::out
    exit
}
