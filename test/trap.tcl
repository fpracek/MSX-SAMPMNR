proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
# 1: tuck under conveyor from south, then walk back OUT (down) - no trap
after time 6   { debug write memory 0xC004 88 ; debug write memory 0xC005 80 ; keymatrixdown 8 0x20 }
after time 8.5 { dumpram t0 ; keymatrixup 8 0x20 ; keymatrixdown 8 0x40 }
after time 10  { dumpram t1 ; keymatrixup 8 0x40 }
# 2: walk +x along the lane in front of the yellow slab (wz=85): must pass
after time 10.5 { debug write memory 0xC004 16 ; debug write memory 0xC005 85 ; keymatrixdown 8 0x80 }
after time 13.5 { dumpram t2 ; keymatrixup 8 0x80 }
# 3: approach yellow slab from south (-z at x=48): closer stop now
after time 14  { debug write memory 0xC004 48 ; debug write memory 0xC005 95 ; keymatrixdown 8 0x20 }
after time 16  { dumpram t3 ; screenshot -raw ./build/y2.png ; exit }
