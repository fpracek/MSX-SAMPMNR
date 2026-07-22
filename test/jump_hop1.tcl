# Hop 1: floor -> fixed platform (6,1,y=1,surf=16). Platform spans
# world x96-112,z16-32. Start just west of its edge on the floor,
# hold right + jump, and see if Sam lands on top.

after time 6 { keymatrixdown 3 0x02 }
after time 6.3 { keymatrixup 3 0x02 }

set ::out [open ./build/jump_hop1_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] fl=[debug read memory 0xC00A] keys=[debug read memory 0xC00C]"
}

after time 9 {
    # place Sam on the floor just west of the platform's edge
    debug write memory 0xC004 90
    debug write memory 0xC005 24
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    snap "start"
}
after time 9.2 {
    keymatrixdown 8 0x81
}
after time 9.4 {
    keymatrixup 8 0x80
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
