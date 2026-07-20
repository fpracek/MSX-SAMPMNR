proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x50]
    close $f
}
proc shot {n} { screenshot -raw ./build/en$n.png }
after time 6   { shot 1 ; dumpram n1 }
after time 8   { shot 2 ; dumpram n2 }
# teleport Sam onto the belt right of the enemy -> contact -> respawn
after time 8.5 { debug write memory 0xC004 60 ; debug write memory 0xC005 40 ; debug write memory 0xC006 0 ; debug write memory 0xC007 24 ; debug write memory 0xC00A 1 }
after time 10  { dumpram n3 ; shot 3 ; exit }
