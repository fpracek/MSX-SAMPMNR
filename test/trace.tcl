set n 0
proc dumpram {} {
    global n
    set f [open [format "./build/tr_%02d.bin" $n] "w"]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block memory 0xC000 0x20]
    close $f
    incr n
}
after time 6   { keymatrixdown 8 0x20 }
after time 7   { keymatrixup 8 0x20 ; keymatrixdown 8 0x01 }
after time 7.3 { keymatrixup 8 0x01 }
for {set t 0} {$t < 20} {incr t} {
    after time [expr {7.3 + $t*0.1}] { dumpram }
}
after time 9.5 { exit }
