# Regression check: title -> Central Cavern (genuine SPACE press) ->
# boxed name card -> forced win -> boxed Cold Room name card ->
# extended gameplay sampling (frame counter must keep advancing, not
# freeze) -> debug letter-select ('B' = room 1 straight from title).

after time 6 {
    screenshot -raw ./build/r1_title.png
    keymatrixdown 8 0x01
}
after time 6.3 { keymatrixup 8 0x01 }
after time 8  { screenshot -raw ./build/r2_intro_room1_box.png }
after time 11 { screenshot -raw ./build/r3_gameplay_room1.png }
after time 12 {
    set nk [debug read memory 0xC070]
    set bx [debug read memory 0xC07A]
    set bz [debug read memory 0xC07B]
    set es [debug read memory 0xC07C]
    debug write memory 0xC00C $nk
    debug write memory 0xC004 $bx
    debug write memory 0xC005 $bz
    debug write memory 0xC006 0
    debug write memory 0xC007 $es
    debug write memory 0xC008 0
    debug write memory 0xC009 0
}
after time 15.5 { screenshot -raw ./build/r4_intro_room2_box.png }

set ::rout [open ./build/r_frames.txt w]
foreach t {17 18.5 20 21.5 23} {
    after time $t "puts \$::rout \"t=$t room=\[debug read memory 0xC069\] frame=\[debug read memory 0xC000\]\""
}
after time 23.5 {
    close $::rout
    screenshot -raw ./build/r5_gameplay_room2.png
    exit
}
