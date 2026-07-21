# Cold Room content check: ice rocks, gray attacking bear, cones, and
# the new crumble-to-cone mechanic (intermediate platform -> jump to
# high platform -> both crumble away -> cone underneath falls-through
# collectible).

# letter B (row2 bit7) -> room1 (Cold Room)
after time 6 { keymatrixdown 2 0x80 }
after time 6.3 { keymatrixup 2 0x80 }
after time 9 { screenshot -raw ./build/x1_overview.png }

# place Sam on the intermediate crumbling platform (bx=0,bz=5,y=2)
after time 9.5 {
    debug write memory 0xC004 8
    debug write memory 0xC005 88
    debug write memory 0xC006 0
    debug write memory 0xC007 24
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 11 { screenshot -raw ./build/x2_intermediate_half.png }
after time 13 { screenshot -raw ./build/x3_intermediate_gone.png }

# hop to the high platform (bx=1,bz=5,y=3), directly above a cone
after time 13.5 {
    debug write memory 0xC004 24
    debug write memory 0xC005 88
    debug write memory 0xC006 0
    debug write memory 0xC007 32
    debug write memory 0xC008 0
    debug write memory 0xC009 0
}
after time 15 { screenshot -raw ./build/x4_high_half.png }
after time 17 { screenshot -raw ./build/x5_high_gone_falling.png }
after time 18 {
    screenshot -raw ./build/x6_after_fall.png
    set out [open ./build/x_regs.txt w]
    puts $out "keys_got=[debug read memory 0xC00C]"
    puts $out "sam_h_hi=[debug read memory 0xC007]"
    close $out
    exit
}
