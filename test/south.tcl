proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
after time 6 { debug write memory 0xC004 88 ; debug write memory 0xC005 80 ; keymatrixdown 8 0x20 }
after time 9 { dumpram s ; screenshot -raw ./build/s2.png ; exit }
