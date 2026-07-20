proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x50]
    close $f
}
after time 6.0 { debug write memory 0xC00C 3 }
after time 6.5  { screenshot -raw ./build/g1.png }
after time 6.77 { screenshot -raw ./build/g2.png }
after time 7.0 { debug write memory 0xC004 84 ; debug write memory 0xC005 8 ; debug write memory 0xC006 0 ; debug write memory 0xC007 8 ; debug write memory 0xC00A 1 }
after time 7.3 { keymatrixdown 8 0x80 ; keymatrixdown 8 0x01 }
after time 7.6 { keymatrixup 8 0x01 ; keymatrixup 8 0x80 }
after time 8.4 { dumpram g3 ; screenshot -raw ./build/g3.png ; exit }
