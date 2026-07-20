proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
after time 6  { debug write memory 0xC004 110 ; debug write memory 0xC005 72 ; keymatrixdown 8 0x10 }
after time 8  { dumpram a ; screenshot -raw ./build/ce.png ; keymatrixup 8 0x10 }
after time 8.5 { debug write memory 0xC004 12 ; debug write memory 0xC005 72 ; keymatrixdown 8 0x80 }
after time 10.5 { dumpram b ; screenshot -raw ./build/cw.png ; keymatrixup 8 0x80 }
after time 11 { debug write memory 0xC004 56 ; debug write memory 0xC005 20 ; keymatrixdown 8 0x40 }
after time 13 { dumpram c ; screenshot -raw ./build/cn.png ; keymatrixup 8 0x40 }
after time 13.5 { debug write memory 0xC004 56 ; debug write memory 0xC005 90 ; keymatrixdown 8 0x20 }
after time 15.5 { dumpram d ; screenshot -raw ./build/cs.png ; exit }
