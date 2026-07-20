proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
# walk the north-wall corridor (lane 0) from east to west, behind conveyor
after time 6  { debug write memory 0xC004 120 ; debug write memory 0xC005 12 ; keymatrixdown 8 0x10 }
after time 10 { dumpram m1 ; screenshot -raw ./build/m1.png ; keymatrixup 8 0x10 ; exit }
