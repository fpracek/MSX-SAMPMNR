after time 6.0 { debug write memory 0xC00C 3 }
proc trydump {} {
    set st [debug read memory 0xC048]
    if {$st == 16} {
        set f [open "./build/vram_flash2.bin" "w"]
        fconfigure $f -translation binary
        puts -nonewline $f [debug read_block VRAM 0x0C00 0x200]
        puts -nonewline $f [debug read_block VRAM 0x2C00 0x200]
        close $f
        exit
    }
    after time 0.03 { trydump }
}
after time 6.5 { trydump }
after time 12 { exit }
