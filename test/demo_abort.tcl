proc shot {n} { screenshot -raw ./build/ashot$n.png }
after time 6    { debug write memory 0xC0A0 1 }
after time 6.6  { shot 1_incard }
after time 7    { keymatrixdown 8 0x01 }
after time 7.1  { keymatrixup 8 0x01 }
after time 7.3  { shot 2_after_abort }
after time 8    { shot 3_settled ; exit }
