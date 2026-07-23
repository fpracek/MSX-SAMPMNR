# Room 8 lift ride, take 2: a human doesn't hold the counter-direction
# solid (that overshoots the OTHER way, since Sam moves at 1px/frame
# vs the push's 0.5px/frame average) - they tap it rhythmically. This
# alternates short LEFT taps with short releases for the whole ~2s
# climb, modeling that natural "little counter-nudges" play style.

after time 6 { keymatrixdown 3 0x20 }
after time 6.3 { keymatrixup 3 0x20 }

set ::out [open ./build/kong_lift2_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] fl=[debug read memory 0xC00A] on_lift=[debug read memory 0xC04B] lift_h=[debug read memory 0xC049]"
}

after time 9 {
    debug write memory 0xC049 8
    debug write memory 0xC04A 0
    debug write memory 0xC004 72
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    snap "start"
}

# tap LEFT briefly every ~0.16s (8 frames at 50fps), each tap ~2 frames
# (0.04s) - a light, rhythmic nudge rather than a solid hold
set t 9.1
for {set i 0} {$i < 24} {incr i} {
    set tdown $t
    set tup [expr {$t + 0.04}]
    after time $tdown "keymatrixdown 8 0x10"
    after time $tup "keymatrixup 8 0x10"
    set snapt [expr {$t + 0.03}]
    after time $snapt "snap tap$i"
    set t [expr {$t + 0.16}]
}

after time 13.0 { screenshot -raw ./build/kong_lift2_final.png }
after time 13.2 { close $::out; exit }
