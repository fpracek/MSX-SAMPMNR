proc shot {n} { screenshot -raw ./build/fsshot$n.png }
set ::out [open ./build/force_select_log.txt w]
proc snap {tag} {
    set room [debug read memory 0xC0C2]
    set fm   [debug read memory 0xC0BF]
    puts $::out "$tag: current_room=$room force_mode=$fm"
}

# type F O R C E T (row,mask pairs computed from row_bases: F=row3/0x08,
# O=row4/0x10, R=row4/0x80, C=row3/0x01, E=row3/0x04, T=row5/0x02)
set letters {
    {3 0x08} {4 0x10} {4 0x80} {3 0x01} {3 0x04} {5 0x02}
}
set t 6.0
foreach rm $letters {
    set row [lindex $rm 0]
    set mask [lindex $rm 1]
    set td [expr {$t}]
    set tu [expr {$t + 0.05}]
    after time $td [list keymatrixdown $row $mask]
    after time $tu [list keymatrixup $row $mask]
    set t [expr {$t + 0.15}]
}
after time [expr {$t + 0.3}] { snap after_typing ; shot 1_after_force_t }
after time [expr {$t + 0.6}] { snap settled ; shot 2_settled ; close $::out ; exit }
