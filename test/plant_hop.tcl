# Room6 real-physics jump: conveyor's solid arrival platform (6,3,y=1)
# -> catwalk entry (5,2,y=3), a diagonal jump - identical world
# coordinates/deltas to Room5's already-validated hop2 (eugene_hop2.tcl),
# reused verbatim since it's the same geometry in a different room.
# Pacmen neutralized (forced to a wide, safe gap) so this test isolates
# pure jump reachability, matching this project's standing methodology.

after time 6 { keymatrixdown 3 0x08 }
after time 6.3 { keymatrixup 3 0x08 }

set ::out [open ./build/plant_hop_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] fl=[debug read memory 0xC00A] keys=[debug read memory 0xC00C]"
}

after time 9 {
    debug write memory 0xC090 200
    debug write memory 0xC004 97
    debug write memory 0xC005 49
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    snap "start"
}
after time 9.2 { keymatrixdown 8 0x01 }
after time 9.24 { keymatrixdown 8 0x30 }
after time 9.44 { keymatrixup 8 0x30 }
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
