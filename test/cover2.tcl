proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
# 1: -x in lane 1 behind conveyor: blocked before covered cells
after time 6   { debug write memory 0xC004 120 ; debug write memory 0xC005 24 ; keymatrixdown 8 0x10 }
after time 9   { dumpram d1 ; screenshot -raw ./build/dv1.png ; keymatrixup 8 0x10 }
# 2: +x from west toward yellow slab lane (wz=72): tuck still works
after time 9.5 { debug write memory 0xC004 12 ; debug write memory 0xC005 72 ; keymatrixdown 8 0x80 }
after time 12  { dumpram d2 ; keymatrixup 8 0x80 }
# 3: +x from west in lane 1 (behind conveyor from WEST): must stop before image
after time 12.5 { debug write memory 0xC004 12 ; debug write memory 0xC005 24 ; keymatrixdown 8 0x80 }
after time 15.5 { dumpram d3 ; screenshot -raw ./build/dv3.png ; keymatrixup 8 0x80 ; exit }
