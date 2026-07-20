after time 6    { keymatrixdown 8 0x80 }
after time 6.4  { keymatrixdown 8 0x01 }
after time 6.8  { keymatrixup 8 0x01 }
after time 7.15 { keymatrixup 8 0x80 }
after time 8 {
    set f [open "./build/vram2.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block VRAM 0 0x4000]
    close $f
    exit
}
