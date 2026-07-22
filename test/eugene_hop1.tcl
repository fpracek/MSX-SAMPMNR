# Room5 hop 1: floor -> low platform (6,3,y=1,surf=16). Platform spans
# world x96-112,z48-64. Start just west of its edge on the floor, hold
# right + jump, and see if Sam lands on top. Same template as
# jump_hop1.tcl (Room4), just repositioned to Room5's low platform.

after time 6 { keymatrixdown 3 0x04 }
after time 6.3 { keymatrixup 3 0x04 }

set ::out [open ./build/eugene_hop1_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] fl=[debug read memory 0xC00A] keys=[debug read memory 0xC00C]"
}

after time 9 {
    debug write memory 0xC004 90
    debug write memory 0xC005 56
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
