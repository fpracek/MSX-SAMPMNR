proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
}
proc shot {n} { screenshot -raw ./build/bt$n.png }
# put Sam ON the conveyor west end, let the belt carry him off the east
# end, then IMMEDIATELY press back (-x) while falling: must NOT re-enter
after time 6    { debug write memory 0xC004 82 ; debug write memory 0xC005 56 ; debug write memory 0xC007 24 ; debug write memory 0xC006 0 }
after time 9    { dumpram r1 ; keymatrixdown 8 0x10 }
after time 12   { dumpram r2 ; shot 1 ; keymatrixup 8 0x10 }
# regression: key jump test position intact
after time 12.5 { debug write memory 0xC004 24 ; debug write memory 0xC005 72 }
after time 13   { exit }
