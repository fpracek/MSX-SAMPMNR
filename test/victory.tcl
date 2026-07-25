proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x100]
    close $f
}
proc shot {n} { screenshot -raw ./build/vshot$n.png }

# select room index 19 (last room, T key = row5 bit1) directly from the title
after time 6   { keymatrixdown 5 0x02 }
after time 6.3 { keymatrixup 5 0x02 }
after time 7   { shot titlepick }

# let room_enter's name-card intro (~100 frames/2s) finish, then force test state
after time 9    {
    debug write memory 0xC090 4   ;# bonus_ctr = 4 (one more clear should award a life)
    debug write memory 0xC08F 3   ;# lives = 3
    debug write memory 0xC091 0   ;# won_awarded = 0
    debug write memory 0xC092 0   ;# victory_mode = 0
    debug write memory 0xC00D 1   ;# level_done = 1 -> force main_loop into .won
}
after time 9.1  { dumpram before ; shot before }

# won_t must cross 120 frames (~2.4s) before the bonus-award/advance logic fires
after time 12    { dumpram mid ; shot mid }
after time 12.4  { shot pose1 }
after time 12.7  { shot pose2 }
after time 13    { dumpram after ; shot after ; exit }
