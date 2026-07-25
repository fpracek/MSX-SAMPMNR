proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x100]
    close $f
}
proc shot {n} { screenshot -raw ./build/dfshot$n.png }

# select room 0 (Central Cavern, letter A = row2 bit6) from the title
after time 6   { keymatrixdown 2 0x40 }
after time 6.3 { keymatrixup 2 0x40 }

# let room_enter's name-card intro clear, then force a win with a
# partially-depleted air bar so the drain is visually obvious
after time 9    {
    debug write memory 0xC093 100  ;# air = 100 (of 160)
    debug write memory 0xC00D 1    ;# level_done = 1 -> force main_loop's .won:
}
after time 9.2  { shot 1_blink ; dumpram before }

# won_t needs ~120 frames (2.4s) before drain_air_fx kicks in
after time 11.7 { shot 2_drainstart }
after time 11.9 { shot 3_draining }
after time 12.3 { shot 4_drained ; dumpram after }
after time 13   { shot 5_nextroom ; dumpram settled ; exit }
