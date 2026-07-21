# Confirm the poison-puddle hazards still kill on contact via the
# plain hazard_check path, and take a full-room screenshot.

after time 6 { keymatrixdown 3 0x01 }
after time 6.3 { keymatrixup 3 0x01 }

set ::out [open ./build/puddle_log.txt w]
proc snap {label} {
    puts $::out "$label: lives=[debug read memory 0xC04C] room=[debug read memory 0xC06C]"
}

after time 9 {
    snap "baseline"
    screenshot -raw ./build/puddle_overview.png
}

# puddle0 sits at (bx=2,bz=3,surf=8) -> wx=40,wz=56. Kill ceiling is
# surf+10=18, so feet below that (sam_h+1 < 18) while standing on the
# same (bx,bz) cell triggers hazard_check's kill.
after time 9.5 {
    debug write memory 0xC004 40
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.7 { snap "on-puddle0" }
after time 10.5 { snap "settled" }

after time 11 {
    close $::out
    exit
}
