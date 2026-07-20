proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x50]
    close $f
}
after time 6.0 { debug write memory 0xC004 84 ; debug write memory 0xC005 8 ; debug write memory 0xC006 0 ; debug write memory 0xC007 8 ; debug write memory 0xC00A 1 ; debug write memory 0xC00C 3 }
after time 6.5 { keymatrixdown 8 0x80 ; keymatrixdown 8 0x01 }
after time 6.8 { keymatrixup 8 0x01 ; keymatrixup 8 0x80 }
after time 7.6 { dumpram v1 ; screenshot -raw ./build/v1.png ; exit }
