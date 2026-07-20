proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
after time 6    { keymatrixdown 8 0x80 }
after time 6.4  { keymatrixdown 8 0x01 }
after time 6.8  { keymatrixup 8 0x01 }
after time 7.15 { keymatrixup 8 0x80 }
after time 8    { dumpram k0 ; screenshot -raw ./build/k0.png ; exit }
