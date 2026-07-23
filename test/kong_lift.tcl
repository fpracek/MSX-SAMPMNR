# Room 8 lift mechanic validation (real input, not teleport-only):
# (A) do nothing while riding - the forced conveyor-style push should
#     drift Sam off the lift's narrow footprint and drop him, and
# (B) counter-steer continuously - he should ride all the way to the
#     summit with his height tracking the lift.

after time 6 { keymatrixdown 3 0x20 }
after time 6.3 { keymatrixup 3 0x20 }

set ::out [open ./build/kong_lift_log.txt w]
proc snap {label} {
    puts $::out "$label: wx=[debug read memory 0xC004] wz=[debug read memory 0xC005] h=[debug read memory 0xC007] fl=[debug read memory 0xC00A] on_lift=[debug read memory 0xC04B] lift_h=[debug read memory 0xC049]"
}

# --- Test A: board the lift, then do nothing ---
after time 9 {
    debug write memory 0xC049 8
    debug write memory 0xC04A 0
    debug write memory 0xC004 72
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.05 { snap "A: boarded lift at floor level" }
foreach t {9.3 9.6 9.9 10.2 10.5} {
    after time $t "snap A-idle-t=$t"
}

# --- Test B: reset to lift base, hold LEFT (0x10) to counter the +x
# push, ride continuously all the way to the summit ---
after time 10.7 {
    debug write memory 0xC049 8
    debug write memory 0xC04A 0
    debug write memory 0xC004 72
    debug write memory 0xC005 56
    debug write memory 0xC006 0
    debug write memory 0xC007 8
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
    snap "B: reset, about to counter-steer"
}
after time 10.75 { keymatrixdown 8 0x10 }
foreach t {11.0 11.5 12.0 12.5 13.0 13.5 14.0} {
    after time $t "snap B-riding-t=$t"
}
after time 14.5 {
    keymatrixup 8 0x10
    snap "B: final (want lift_h near ymax=56, on_lift=1, sam still up there)"
    screenshot -raw ./build/kong_lift_top.png
}

after time 15.0 {
    close $::out
    exit
}
