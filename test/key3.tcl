after time 6 {
    debug write memory 0xC004 24
    debug write memory 0xC005 8
    debug write memory 0xC006 0
    debug write memory 0xC007 40
}
after time 7 {
    set f [open "./build/ram_k3.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
    screenshot -raw ./build/k3.png
    exit
}
