proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
# row8: bit0=SPACE bit4=LEFT bit5=UP bit6=DOWN bit7=RIGHT
after time 6   { dumpram t0 ; screenshot -raw ./build/w0.png ; keymatrixdown 8 0x80 }
after time 7.5 { dumpram t1 ; screenshot -raw ./build/w1.png ; keymatrixup 8 0x80 ; keymatrixdown 8 0x20 }
after time 8.5 { dumpram t2 ; screenshot -raw ./build/w2.png ; keymatrixup 8 0x20 ; keymatrixdown 8 0x01 }
after time 8.8 { dumpram t3 ; screenshot -raw ./build/w3.png ; keymatrixup 8 0x01 }
after time 10  { dumpram t4 ; screenshot -raw ./build/w4.png ; exit }
