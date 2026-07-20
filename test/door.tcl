after time 6 {
    debug write memory 0xC00D 3
    debug write memory 0xC004 0xBC
}
after time 7 {
    set f [open "./build/ram_door.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
    screenshot -raw ./build/door.png
    exit
}
