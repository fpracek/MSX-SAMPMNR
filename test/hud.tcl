proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x50]
    close $f
}
after time 6   { screenshot -raw ./build/h1.png ; dumpram h1 }
# fake a collected key then die on the enemy
after time 6.5 { debug write memory 0xC00C 1 ; debug write memory 0xC004 60 ; debug write memory 0xC005 40 ; debug write memory 0xC006 0 ; debug write memory 0xC007 24 ; debug write memory 0xC00A 1 }
after time 7.5 { dumpram h2 }
after time 12  { screenshot -raw ./build/h3.png ; dumpram h3 ; exit }
