after time 6 {
    set f [open "./build/vram.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block VRAM 0 0x4000]
    close $f
    set f2 [open "./build/ram.bin" "w"]
    fconfigure $f2 -translation binary
    puts -nonewline $f2 [debug read_block memory 0xC000 0x600]
    close $f2
    screenshot -raw ./build/shot.png
    exit
}
