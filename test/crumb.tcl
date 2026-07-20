proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x40]
    close $f
}
proc shot {n} { screenshot -raw ./build/cr$n.png }
# drop Sam onto the grey block (4,4)
after time 6    { debug write memory 0xC004 72 ; debug write memory 0xC005 72 ; debug write memory 0xC006 0 ; debug write memory 0xC007 28 ; debug write memory 0xC00A 0 }
after time 7    { shot 0 ; keymatrixdown 8 0x10 }
after time 7.5  { keymatrixup 8 0x10 }
after time 8    { dumpram s1 ; shot 1 ; keymatrixdown 8 0x80 }
after time 8.6  { keymatrixup 8 0x80 ; keymatrixdown 8 0x10 }
after time 9.2  { keymatrixup 8 0x10 }
after time 9.7  { dumpram s2 ; shot 2 ; keymatrixdown 8 0x80 }
after time 11   { keymatrixup 8 0x80 ; dumpram s3 ; shot 3 ; exit }
