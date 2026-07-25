proc shot {n} { screenshot -raw ./build/dshot$n.png }

# force the waltz-looped flag so title_loop enters demo_mode right away
# instead of waiting through a real ~27s loop of the tune. Room load
# (big bg/color blit) takes real emulated time before the first frame
# tick, so give it a moment before screenshotting.
after time 6    { debug write memory 0xC0A0 1 }
after time 6.5  { shot 1_room1_card }
after time 8.5  { shot 2_room1_bare }

# fast-forward: skip straight to the LAST room (index 19) by poking
# current_room during room1's bare-hold phase, so the natural room1->
# advance check at ~11.1s lands on room 19 instead of room 2
after time 10.5 { debug write memory 0xC0B3 18 }
after time 11.6 { shot 3_room20_card }
after time 13.7 { shot 4_room20_bare }
after time 16.8 { shot 5_back_at_title ; exit }
