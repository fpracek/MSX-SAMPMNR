proc shot {n} { screenshot -raw ./build/gwshot$n.png }
proc snap {tag} {
    set air [debug read memory 0xC093]
    set room [debug read memory 0xC0B6]
    set vm  [debug read memory 0xC092]
    puts "TAG $tag air=$air room=$room victory_mode=$vm"
}
# select the LAST room (index 19, letter T = row5 bit1) from the title
after time 6   { keymatrixdown 5 0x02 }
after time 6.3 { keymatrixup 5 0x02 }
# let the name-card clear, then force the win immediately
after time 9    { debug write memory 0xC00D 1 }
after time 9.2  { shot 1_blink }
# won_t needs ~2.4s, then drain_air_fx ~0.4s, then the LEVELS COMPLETED card
after time 12.2 { shot 2_card }
after time 14   { shot 3_card_dancing }
after time 15.3 { shot 4_still_card }
after time 16   { shot 5_back_at_title ; exit }
