proc shot {n} { screenshot -raw ./build/mk$n.png }
# 1: Sam behind the yellow slab (lane 3), walking east->west
after time 6  { debug write memory 0xC004 100 ; debug write memory 0xC005 52 ; keymatrixdown 8 0x10 }
after time 8  { shot 1 }
after time 9  { shot 2 ; keymatrixup 8 0x10 }
# 2: Sam under the conveyor lane (z=3): walk +x under it
after time 9.5 { debug write memory 0xC004 40 ; debug write memory 0xC005 56 ; keymatrixdown 8 0x80 }
after time 11.5 { shot 3 ; keymatrixup 8 0x80 }
# 3: in front of yellow (lane 5): no mask
after time 12 { debug write memory 0xC004 40 ; debug write memory 0xC005 88 }
after time 13 { shot 4 ; exit }
