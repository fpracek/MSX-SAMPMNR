# Room6 empirical validation of a computationally-proven-safe crossing,
# split into its two independently-provable phases:
#  1. the jump onto the catwalk (already validated separately in
#     test/plant_hop.tcl) - pacman neutralized here too, to isolate it
#  2. the walk from landing to the key - exhaustive simulation (every
#     starting phase x move/wait/retreat strategy) found that starting
#     this leg with en_x=41 (increasing) lets Sam walk CONTINUOUSLY to
#     the key with no pausing needed - pos2 (56+en_x) starts at 97,
#     already clear of the landing spot (87), and keeps moving AWAY as
#     Sam approaches. Setting this phase right at the landing moment
#     (as if the player waited there and watched for it) isolates
#     whether phase 2 alone is genuinely safe, same rigor as phase 1.

after time 6 { keymatrixdown 3 0x08 }
after time 6.3 { keymatrixup 3 0x08 }

set ::out [open ./build/plant_validated_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] fl=[debug read memory 0xC00A] keys=[debug read memory 0xC00C] lives=[debug read memory 0xC04C] en_x=[debug read memory 0xC046]"
}

# phase 1: the jump, with the pacman pushed off to the side (fixed z
# pushed far away) so it can't interfere - isolates pure jump physics,
# already proven safe on its own in plant_hop.tcl
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
after time 9.8 {
    keymatrixup 8 0x01
    snap "landed on catwalk"
}

# phase 2: restore the pacman to real play, at the validated
# walk-safe starting phase, right as the walk begins
after time 9.82 {
    debug write memory 0xC090 40
    debug write memory 0xC046 41
    debug write memory 0xC047 0
    snap "pacman restored, walk-safe phase set"
}
after time 9.85 { keymatrixdown 8 0x10 }
foreach t {9.9 10.0 10.1 10.2 10.3 10.4 10.5 10.6} {
    after time $t "snap t=$t"
}
after time 10.7 {
    keymatrixup 8 0x10
    snap "at key"
}

# return trip: set the validated clean-return phase, then continuous
# walk back to the refuge/conveyor side
after time 10.72 {
    debug write memory 0xC046 25
    debug write memory 0xC047 0
    snap "return phase set"
}
after time 10.75 { keymatrixdown 8 0x80 }
foreach t {10.8 10.9 11.0 11.1 11.2 11.3 11.4 11.5} {
    after time $t "snap t=$t"
}
after time 11.6 {
    keymatrixup 8 0x80
    snap "back at refuge"
}

after time 11.8 {
    close $::out
    exit
}
