proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x40]
    close $f
}
proc shot {n} { screenshot -raw ./build/ce$n.png }
# drop Sam on the EAST cell of the shelf and stand still
after time 6    { debug write memory 0xC004 40 ; debug write memory 0xC005 8 ; debug write memory 0xC006 0 ; debug write memory 0xC007 36 ; debug write memory 0xC00A 0 }
after time 7.4  { dumpram c1 ; shot 1 }
after time 8.4  { dumpram c2 ; shot 2 }
after time 9.5  { dumpram c3 ; shot 3 ; exit }
