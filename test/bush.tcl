proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x50]
    close $f
}
after time 6   { screenshot -raw ./build/bu1.png ; dumpram u1 }
after time 6.2 { keymatrixdown 8 0x20 }
after time 7.4 { keymatrixup 8 0x20 ; dumpram u2 }
after time 7.6 { debug write memory 0xC004 24 ; debug write memory 0xC005 56 ; debug write memory 0xC006 0 ; debug write memory 0xC007 8 ; debug write memory 0xC00A 1 }
after time 7.8 { keymatrixdown 8 0x20 ; keymatrixdown 8 0x01 }
after time 8.1 { keymatrixup 8 0x01 }
after time 8.6 { keymatrixup 8 0x20 ; dumpram u3 ; screenshot -raw ./build/bu2.png ; exit }
