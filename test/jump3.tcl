proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x50]
    close $f
}
after time 6    { debug write memory 0xC03F 200 ; debug write memory 0xC004 56 ; debug write memory 0xC005 36 ; debug write memory 0xC006 0 ; debug write memory 0xC007 24 ; debug write memory 0xC00A 1 }
after time 6.2  { keymatrixdown 8 0x10 ; keymatrixdown 8 0x20 ; keymatrixdown 8 0x01 }
after time 6.6  { keymatrixup 8 0x01 }
after time 6.9  { keymatrixup 8 0x10 ; keymatrixup 8 0x20 }
after time 7.0  { dumpram b1 }
after time 7.3  { dumpram b2 ; screenshot -raw ./build/b1.png ; exit }
