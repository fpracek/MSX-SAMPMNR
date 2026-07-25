set ::out [open ./build/renzo_chime_log.txt w]
proc snap {tag} {
    set il  [debug read memory 0xC0C1]
    set st  [debug read memory 0xC00E]
    set f0  [debug read memory 0xC00F]
    set f1  [debug read memory 0xC010]
    puts $::out "$tag: infinite_lives=$il sfx_t=$st sfx_freq=$f0,$f1"
}
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
after time [expr {$t+0.05}] { snap right_after_renzo }
after time [expr {$t+0.2}]  { snap mid_chime }
after time [expr {$t+0.6}]  { snap chime_done ; close $::out ; exit }
