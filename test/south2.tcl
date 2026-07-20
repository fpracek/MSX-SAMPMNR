after time 6 { debug write memory 0xC004 48 ; debug write memory 0xC005 88 ; keymatrixdown 8 0x20 }
after time 8 {
    set f [open "./build/ram_s3.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
    screenshot -raw ./build/y3.png
    exit
}
