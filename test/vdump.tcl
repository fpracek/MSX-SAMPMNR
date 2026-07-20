after time 6.0 { debug write memory 0xC00C 3 }
after time 7.0 {
    set f [open "./build/vram_flash.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block VRAM 0x0C00 0x200]
    puts -nonewline $f [debug read_block VRAM 0x2C00 0x200]
    set g [open "./build/exst.bin" "w"]
    fconfigure $g -translation binary
    puts -nonewline $g [debug read_block memory 0xC048 0x8]
    close $f ; close $g ; exit
}
