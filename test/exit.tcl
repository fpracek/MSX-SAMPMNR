proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x50]
    close $f
}
# phase 1: no keys, stand on cube -> nothing happens
after time 5.8 { debug write memory 0xC004 104 ; debug write memory 0xC005 8 ; debug write memory 0xC006 0 ; debug write memory 0xC007 16 ; debug write memory 0xC00A 1 }
after time 6.2 { dumpram a1 ; screenshot -raw ./build/x0.png }
# phase 2: off the cube, all keys -> cube must blink
after time 6.4 { debug write memory 0xC004 24 ; debug write memory 0xC005 72 ; debug write memory 0xC007 8 ; debug write memory 0xC00C 3 }
after time 6.9  { screenshot -raw ./build/f1.png }
after time 7.15 { screenshot -raw ./build/f2.png ; dumpram b1 }
# phase 3: walk east into the cube side -> blocked
after time 7.3 { debug write memory 0xC004 80 ; debug write memory 0xC005 8 }
after time 7.4 { keymatrixdown 8 0x80 }
after time 8.4 { dumpram w1 }
# phase 4: jump onto the cube -> victory
after time 8.5 { keymatrixdown 8 0x01 }
after time 8.8 { keymatrixup 8 0x01 }
after time 9.6 { keymatrixup 8 0x80 ; dumpram w2 ; screenshot -raw ./build/f3.png ; exit }
