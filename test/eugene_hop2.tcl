# Room5 hop 2: low platform (6,3,y=1,surf=16) -> platform A (5,2,y=3,
# surf=32), a diagonal up-left jump (toward LOWER bz this time, mirror
# of Room4's hop2 which went toward higher bz) gaining 16px height.

after time 6 { keymatrixdown 3 0x04 }
after time 6.3 { keymatrixup 3 0x04 }

set ::out [open ./build/eugene_hop2_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] fl=[debug read memory 0xC00A] keys=[debug read memory 0xC00C]"
}

after time 9 {
    # place Sam at the NW corner of the low platform, facing toward
    # platform A (lower x, lower z)
    debug write memory 0xC004 97
    debug write memory 0xC005 49
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
    keymatrixdown 8 0x30
}
after time 9.44 {
    keymatrixup 8 0x30
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
