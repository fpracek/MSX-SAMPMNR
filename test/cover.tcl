proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
# 1: walk -x (east->west) in lane BEHIND conveyor (wz=24): must stop before its columns
after time 6   { debug write memory 0xC004 120 ; debug write memory 0xC005 24 ; keymatrixdown 8 0x10 }
after time 9   { dumpram c1 ; screenshot -raw ./build/cv1.png ; keymatrixup 8 0x10 }
# 2: walk -x in footprint lane (wz=40): stop at footprint
after time 9.5 { debug write memory 0xC004 120 ; debug write memory 0xC005 40 ; keymatrixdown 8 0x10 }
after time 12  { dumpram c2 ; keymatrixup 8 0x10 }
# 3: walk -x in lane SOUTH of conveyor (wz=56): must pass
after time 12.5 { debug write memory 0xC004 120 ; debug write memory 0xC005 56 ; keymatrixdown 8 0x10 }
after time 15.5 { dumpram c3 ; keymatrixup 8 0x10 ; exit }
