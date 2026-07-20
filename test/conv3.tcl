proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
# walk +x one lane SOUTH of the conveyor (wz=52): must pass freely
after time 6  { debug write memory 0xC004 40 ; debug write memory 0xC005 52 ; keymatrixdown 8 0x80 }
after time 9  { dumpram p ; screenshot -raw ./build/p.png ; keymatrixup 8 0x80 }
# walk +x exactly in the conveyor lane (wz=40): must stop at footprint
after time 9.5 { debug write memory 0xC004 40 ; debug write memory 0xC005 40 ; keymatrixdown 8 0x80 }
after time 12 { dumpram q ; screenshot -raw ./build/q.png ; exit }
