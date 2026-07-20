proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
after time 6  { keymatrixdown 8 0x80 }
after time 9  { dumpram w0 ; screenshot -raw ./build/wa.png ; keymatrixup 8 0x80 ; keymatrixdown 8 0x40 }
after time 10 { keymatrixup 8 0x40 ; keymatrixdown 8 0x80 }
after time 12 { dumpram w1 ; screenshot -raw ./build/wb.png ; exit }
