proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x40]
    close $f
}
proc shot {n} { screenshot -raw ./build/er$n.png }
# drop Sam onto the grey block and just STAND there
after time 6    { debug write memory 0xC004 72 ; debug write memory 0xC005 72 ; debug write memory 0xC006 0 ; debug write memory 0xC007 28 ; debug write memory 0xC00A 0 }
after time 7.5  { dumpram e1 ; shot 1 }
after time 8.3  { dumpram e2 ; shot 2 }
after time 9.5  { dumpram e3 ; shot 3 ; exit }
