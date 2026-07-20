proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
# approach conveyor from SOUTH (walk up/-z at x=88 mid-conveyor)
after time 6  { debug write memory 0xC004 88 ; debug write memory 0xC005 70 ; keymatrixdown 8 0x20 }
after time 8  { dumpram s ; screenshot -raw ./build/vs.png ; keymatrixup 8 0x20 }
# approach conveyor from WEST (walk right at z=40 conveyor lane)
after time 8.5 { debug write memory 0xC004 40 ; debug write memory 0xC005 40 ; keymatrixdown 8 0x80 }
after time 11 { dumpram w ; screenshot -raw ./build/vw.png ; keymatrixup 8 0x80 }
# jump onto conveyor from beside it (from south, jump while pushing up)
after time 11.5 { debug write memory 0xC004 88 ; debug write memory 0xC005 52 }
after time 12 { keymatrixdown 8 0x20 ; keymatrixdown 8 0x01 }
after time 12.5 { keymatrixup 8 0x01 }
after time 13.5 { keymatrixup 8 0x20 ; dumpram j ; screenshot -raw ./build/vj.png ; exit }
