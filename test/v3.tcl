proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
proc shot {n} { screenshot -raw ./build/v3$n.png }
# 1: behind the conveyor (lane 2): head must peek naturally over the belt
after time 6   { debug write memory 0xC004 88 ; debug write memory 0xC005 40 }
after time 7   { shot 1 }
# 2: walk INTO the conveyor from south: blocked at edge
after time 7.2 { debug write memory 0xC004 88 ; debug write memory 0xC005 80 ; keymatrixdown 8 0x20 }
after time 9   { dumpram a ; shot 2 ; keymatrixup 8 0x20 }
# 3: jump onto the shelf from the floor below (lane 1, x=24): +24 jump
after time 9.5 { debug write memory 0xC004 24 ; debug write memory 0xC005 30 }
after time 10  { keymatrixdown 8 0x21 }
after time 10.5 { keymatrixup 8 0x01 }
after time 11  { keymatrixup 8 0x20 ; dumpram b ; shot 3 }
after time 12  { dumpram c ; shot 4 ; exit }
