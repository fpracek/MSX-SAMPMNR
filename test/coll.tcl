proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
# A: approach yellow slab from the RIGHT (walk left), lane z=72
after time 6  { debug write memory 0xC004 110 ; debug write memory 0xC005 72 ; keymatrixdown 8 0x10 }
after time 9  { dumpram a ; screenshot -raw ./build/ca.png ; keymatrixup 8 0x10 }
# B: walk right through the conveyor lane (z=40, floor)
after time 9.5 { debug write memory 0xC004 40 ; debug write memory 0xC005 40 ; keymatrixdown 8 0x80 }
after time 12.5 { dumpram b ; screenshot -raw ./build/cb.png ; exit }
