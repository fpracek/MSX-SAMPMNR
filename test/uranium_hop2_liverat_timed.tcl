# Same hop2 setup as uranium_hop2_liverat.tcl, but the jump is timed to
# ~12.0s (matching the rat's low-point retreat phase sampled earlier -
# en_x around 50-56, far from platform2's ~80-97 zone) instead of the
# first-opportunity ~9.2s - simulating a player who WAITS for the rat
# to clear before jumping, rather than jumping the instant they land.

after time 6 { keymatrixdown 3 0x02 }
after time 6.3 { keymatrixup 3 0x02 }

set ::out [open ./build/uranium_hop2_liverat_timed_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] fl=[debug read memory 0xC00A] lives=[debug read memory 0xC04C] en_x=[debug read memory 0xC046]"
}

after time 12.0 {
    debug write memory 0xC004 97
    debug write memory 0xC005 31
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    snap "start"
}
after time 12.2 { keymatrixdown 8 0x01 }
after time 12.24 { keymatrixdown 8 0x50 }
after time 12.44 { keymatrixup 8 0x50 }
foreach t {12.3 12.4 12.5 12.6 12.7 12.8 12.9 13.0 13.2 13.4 13.6} {
    after time $t "snap t=$t"
}
after time 13.7 {
    keymatrixup 8 0x01
    snap "released"
}
after time 13.9 {
    close $::out
    exit
}
