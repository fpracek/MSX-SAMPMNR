proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
proc shot {n} { screenshot -raw ./build/fx$n.png }
# 1: walk +x through the conveyor lane at floor level: must be BLOCKED now
after time 6   { debug write memory 0xC004 40 ; debug write memory 0xC005 56 ; keymatrixdown 8 0x80 }
after time 9   { dumpram f1 ; shot 1 ; keymatrixup 8 0x80 }
# 2: stand just SOUTH-EAST of conveyor (in front): fully visible
after time 9.5 { debug write memory 0xC004 108 ; debug write memory 0xC005 66 }
after time 10.5 { shot 2 }
# 3: north corridor under the shelf still passable
after time 11  { debug write memory 0xC004 120 ; debug write memory 0xC005 12 ; keymatrixdown 8 0x10 }
after time 14.5 { dumpram f3 ; shot 3 ; keymatrixup 8 0x10 ; exit }
