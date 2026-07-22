# Room 3 mechanic verification, v2: the first attempt (room3mech.tcl)
# conflated real chicken kills (it patrols the exact same lane/height as
# the crumbling platforms - working as intended) with the crumble state
# checks. This version neutralizes the chicken (parks it out of range
# via room_enxmin/enxmax/en_x) while checking platforms/keys, then
# re-enables it for a dedicated kill-zone check at the end.

after time 6 { keymatrixdown 3 0x01 }
after time 6.3 { keymatrixup 3 0x01 }

set ::out [open ./build/r3m2_log.txt w]
proc snap {label} {
    set nk    [debug read memory 0xC00C]
    set c0    [debug read memory 0xC021]
    set c1    [debug read memory 0xC022]
    set c2    [debug read memory 0xC023]
    set c3    [debug read memory 0xC024]
    set c4    [debug read memory 0xC025]
    set cprv  [debug read memory 0xC029]
    set lives [debug read memory 0xC04C]
    set room  [debug read memory 0xC06C]
    set fl    [debug read memory 0xC00A]
    puts $::out "$label: keys=$nk cells(0..4)=$c0,$c1,$c2,$c3,$c4 cr_prev=$cprv lives=$lives room=$room sam_fl=$fl"
}

after time 9 {
    snap "baseline"
    # park the chicken far out of the platform lane so it can't
    # interfere with the crumble/key checks below
    debug write memory 0xC08E 200
    debug write memory 0xC08F 208
    debug write memory 0xC046 204
    screenshot -raw ./build/r3m2_00_intro.png
}

# ---- platform A (bx=3,bz=2,y=3) cell id=0, key0 at y=4 above it ----
after time 9.3 {
    debug write memory 0xC004 56
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 32
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 9.35 { snap "A-touch1 (want cell0=1, keys=1, still grounded)" }
after time 9.4  { screenshot -raw ./build/r3m2_01_A_half.png }

# step off onto solid floor (bx=1,bz=1,y=0) - clears cr_prev
after time 9.6 {
    debug write memory 0xC004 24
    debug write memory 0xC005 24
    debug write memory 0xC007 8
}
after time 9.75 { snap "A-off (cell0 should stay 1)" }

# back onto A: second touch -> cell reaches "gone", Sam then has no
# floor left and starts falling (expected: this IS the crumble-then-
# drop design, not a bug) - snapshot fast, before the fall completes
after time 10 {
    debug write memory 0xC004 56
    debug write memory 0xC005 40
    debug write memory 0xC007 32
}
after time 10.05 { snap "A-touch2 immediate (want cell0=2, sam_fl still grounded this same frame)" }
after time 10.3  { snap "A-touch2 settling (falling or already respawned - both prove destruction)" }

# ---- platform C (bx=5,bz=2,y=3) cell id=4: the one that used to
#      overflow into cr_prev before the RESB4->RESB8 fix ----
after time 11 {
    debug write memory 0xC004 88
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 32
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 11.05 { snap "C-touch1 immediate (want cell4=1, cr_prev=4, NOT aliased into some other var)" }
after time 11.4  { screenshot -raw ./build/r3m2_02_C_half.png }

after time 11.6 {
    debug write memory 0xC004 24
    debug write memory 0xC005 24
    debug write memory 0xC007 8
}
after time 11.75 { snap "C-off (cell4 should stay 1)" }

after time 12 {
    debug write memory 0xC004 88
    debug write memory 0xC005 40
    debug write memory 0xC007 32
}
after time 12.05 { snap "C-touch2 immediate (want cell4=2)" }

# ---- fixed platform key3 (bx=6,bz=1,y=1), key sits at y=2 ----
after time 13 {
    debug write memory 0xC04C 5
    debug write memory 0xC00C 0
    debug write memory 0xC004 104
    debug write memory 0xC005 24
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 13.1 { snap "key3 (fixed platform, non-crumbling, key should collect)" }
after time 13.2 { screenshot -raw ./build/r3m2_03_key3.png }

# ---- re-enable the chicken and deliberately test its kill-zone ----
after time 13.5 {
    debug write memory 0xC04C 5
    debug write memory 0xC08E 48
    debug write memory 0xC08F 96
}
after time 14.5 {
    set ex [debug read memory 0xC046]
    puts $::out "chicken en_x after re-enable=$ex"
    debug write memory 0xC004 $ex
    debug write memory 0xC005 40
    debug write memory 0xC006 0
    debug write memory 0xC007 32
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 14.8 { snap "chicken-contact (want lives dropped by 1, or respawn already happened)" }
after time 15.5 { screenshot -raw ./build/r3m2_04_chicken.png }

# ---- exit: restore keys/lives, stand on the exit cube ----
after time 16 {
    debug write memory 0xC04C 5
    debug write memory 0xC00C 3
    debug write memory 0xC004 104
    debug write memory 0xC005 72
    debug write memory 0xC006 0
    debug write memory 0xC007 16
    debug write memory 0xC008 0
    debug write memory 0xC009 0
    debug write memory 0xC00A 1
}
after time 16.3 { snap "at-exit" }
after time 16.4 { screenshot -raw ./build/r3m2_05_exit.png }
after time 19   {
    set wond [debug read memory 0xC06A]
    set room [debug read memory 0xC06C]
    puts $::out "exit-settled: won_t=$wond room=$room (Room4 now exists, so finishing Room3 correctly ADVANCES to room=3 instead of blinking forever - won_t resets to 0 as part of the room_enter transition)"
    screenshot -raw ./build/r3m2_06_exit_settled.png
}

after time 19.5 {
    close $::out
    exit
}
