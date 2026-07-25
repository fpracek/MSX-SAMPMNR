set ::out [open ./build/renzo_log.txt w]
proc snap {tag} {
    set il   [debug read memory 0xC0C1]
    set lives [debug read memory 0xC08F]
    set air  [debug read memory 0xC093]
    set fr   [debug read memory 0xC000]
    puts $::out "$tag: infinite_lives=$il lives=$lives air=$air frame=$fr"
}
proc shot {n} { screenshot -raw ./build/rzshot$n.png }

# type R E N Z O (R=row4/0x80, E=row3/0x04, N=row4/0x08, Z=row5/0x80, O=row4/0x10)
set letters {
    {4 0x80} {3 0x04} {4 0x08} {5 0x80} {4 0x10}
}
set t 6.0
foreach rm $letters {
    set row [lindex $rm 0]
    set mask [lindex $rm 1]
    after time $t [list keymatrixdown $row $mask]
    after time [expr {$t+0.05}] [list keymatrixup $row $mask]
    set t [expr {$t + 0.15}]
}
after time [expr {$t+0.2}] { snap after_renzo }

# press fire (row8 bit0) to start a real game (room0)
after time [expr {$t+0.5}] { keymatrixdown 8 0x01 }
after time [expr {$t+0.6}] { keymatrixup 8 0x01 }

# let room_enter's name-card clear (~2s), then force a near-death via air
after time [expr {$t+3.5}] {
    debug write memory 0xC093 1   ;# air = 1, about to run out
    debug write memory 0xC08F 3   ;# lives = 3
    snap before_air_out
    shot 1_before
}
after time [expr {$t+4.6}] { snap after_air_out ; shot 2_after ; close $::out ; exit }
