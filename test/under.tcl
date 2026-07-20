proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
proc shot {n} { screenshot -raw ./build/un$n.png }
# 1: walk the north corridor WEST through under the shelf
after time 6   { debug write memory 0xC004 120 ; debug write memory 0xC005 12 ; keymatrixdown 8 0x10 }
after time 8.2 { shot 1 }
after time 10  { dumpram u1 ; shot 2 ; keymatrixup 8 0x10 }
# 2: belt still blocked from the east
after time 10.5 { debug write memory 0xC004 120 ; debug write memory 0xC005 56 ; keymatrixdown 8 0x10 }
after time 12.5 { dumpram u2 ; keymatrixup 8 0x10 ; exit }
