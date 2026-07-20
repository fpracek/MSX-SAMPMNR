proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
# corridor between conveyor east side and right wall: walk north at wx=116
after time 6  { debug write memory 0xC004 116 ; debug write memory 0xC005 60 ; keymatrixdown 8 0x20 }
after time 9  { dumpram k1 ; keymatrixup 8 0x20 }
# same at wx=120 (clamp east)
after time 9.5 { debug write memory 0xC004 120 ; debug write memory 0xC005 60 ; keymatrixdown 8 0x20 }
after time 12  { dumpram k2 ; keymatrixup 8 0x20 }
# and at wx=112
after time 12.5 { debug write memory 0xC004 112 ; debug write memory 0xC005 60 ; keymatrixdown 8 0x20 }
after time 15  { dumpram k3 ; screenshot -raw ./build/corr.png ; exit }
