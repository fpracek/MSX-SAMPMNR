# Hop 2: fixed platform (6,1,y=1,surf=16) -> twin platform2
# (5,2,y=3,surf=32), a diagonal down-left jump gaining 16px height.

after time 6 { keymatrixdown 3 0x02 }
after time 6.3 { keymatrixup 3 0x02 }

set ::out [open ./build/jump_hop2_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] fl=[debug read memory 0xC00A] keys=[debug read memory 0xC00C]"
}

after time 9 {
    # neutralize the rat first - it patrols exactly platform2's lane/
    # height and would confound a pure landing-feasibility check
    debug write memory 0xC08E 200
    debug write memory 0xC08F 208
    debug write memory 0xC046 204
    # place Sam at the SW corner of the fixed platform, facing toward
    # platform2 (lower x, higher z)
    debug write memory 0xC004 97
    debug write memory 0xC005 31
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    snap "start"
}
after time 9.2 {
    keymatrixdown 8 0x01
}
after time 9.24 {
    keymatrixdown 8 0x50
}
after time 9.44 {
    keymatrixup 8 0x50
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
