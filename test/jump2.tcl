proc dumpram {tag} {
    set f [open "./build/ram_$tag.bin" "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x50]
    close $f
}
# Test A: floor -> yellow platform (+16) must succeed.
# Sam starts (24,72,h8). Yellow platform x=2..4 z=4 y=2, surface 24.
# Place Sam just south of yellow at (40,88? no...) -- use teleport near it:
# Yellow at bx 2..4, bz 4 -> world x 32..79, z 64..95. Approach from south (z bigger)? z=4 is last row.
# Approach from east: stand at (88,72,h8) facing west toward x=79 edge... yellow z=64..95 so z=72 ok.
after time 6   { debug write memory 0xC004 90 ; debug write memory 0xC005 72 ; debug write memory 0xC006 0 ; debug write memory 0xC007 8 }
# jump while moving west (left key + space)
after time 6.5 { keymatrixdown 8 0x10 ; keymatrixdown 8 0x01 }
after time 6.9 { keymatrixup 8 0x01 }
after time 7.4 { keymatrixup 8 0x10 ; dumpram j1 }
# Test B: floor -> shelf (+24) must fail. Shelf bx 1..2 bz 0 y=3, surface 32.
# world x 16..47, z 0..31. Stand south of it at (24, 40, h8), jump moving north.
after time 8   { debug write memory 0xC004 24 ; debug write memory 0xC005 44 ; debug write memory 0xC006 0 ; debug write memory 0xC007 8 }
after time 8.5 { keymatrixdown 8 0x20 ; keymatrixdown 8 0x01 }
after time 8.9 { keymatrixup 8 0x01 }
after time 9.5 { keymatrixup 8 0x20 ; dumpram j2 }
# try again straight up to sample apex
after time 9.6 { keymatrixdown 8 0x01 }
after time 9.75 { keymatrixup 8 0x01 }
after time 10.0 { dumpram j3 }
after time 10.4 { dumpram j4 ; screenshot -raw ./build/j.png ; exit }
