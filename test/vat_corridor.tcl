# Room7 corridor feasibility check (real movement, not teleport): walks
# the actual player-input path from the safe west corridor, through the
# hazard field's carved orthogonal corridor, collecting both field keys,
# to the exit column - with the guardian pinned out of the way so this
# run isolates "is the hazard corridor itself walkable", matching the
# project's established split between physical-path and live-enemy
# feasibility checks.

after time 6 { keymatrixdown 3 0x10 }
after time 6.3 { keymatrixup 3 0x10 }

set ::out [open ./build/vat_corridor_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] keys=[debug read memory 0xC00C] lives=[debug read memory 0xC04C]"
}

after time 9 {
    debug write memory 0xC08E 250
    debug write memory 0xC08F 250
    debug write memory 0xC046 250
    debug write memory 0xC047 0
    debug write memory 0xC004 40
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.1 { snap "start (2,3)" }

after time 9.15 { keymatrixdown 8 0x80 }
after time 9.47 { keymatrixup 8 0x80 }
after time 9.5 { snap "leg1 RIGHT (want bx=3)" }

after time 9.55 { keymatrixdown 8 0x80 }
after time 9.87 { keymatrixup 8 0x80 }
after time 9.9 { snap "leg2 RIGHT (want bx=4=key2, keys=1)" }

after time 9.95 { keymatrixdown 8 0x40 }
after time 10.27 { keymatrixup 8 0x40 }
after time 10.3 { snap "leg3 DOWN (want bz=4)" }

after time 10.35 { keymatrixdown 8 0x80 }
after time 10.67 { keymatrixup 8 0x80 }
after time 10.7 { snap "leg4 RIGHT (want bx=5=key3, keys=2)" }

after time 10.75 { keymatrixdown 8 0x80 }
after time 11.07 { keymatrixup 8 0x80 }
after time 11.1 { snap "leg5 RIGHT (want bx=6)" }

after time 11.15 { keymatrixdown 8 0x80 }
after time 11.47 { keymatrixup 8 0x80 }
after time 11.5 { snap "leg6 RIGHT (want bx=7, clear of field)" }

after time 11.55 { keymatrixdown 8 0x40 }
after time 11.87 { keymatrixup 8 0x40 }
after time 11.9 { snap "leg7 DOWN (want bz=5, at exit)" }
after time 12.0 { screenshot -raw ./build/vat_corridor_final.png }

after time 12.3 {
    close $::out
    exit
}
