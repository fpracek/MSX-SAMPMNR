proc shot {n} { screenshot -raw ./build/hd$n.png }
# 1: fully behind the conveyor at floor level (was invisible)
after time 6   { debug write memory 0xC004 88 ; debug write memory 0xC005 40 }
after time 7   { shot 1 }
# 2: behind conveyor other column
after time 7.2 { debug write memory 0xC004 104 ; debug write memory 0xC005 44 }
after time 8.2 { shot 2 }
# 3: behind yellow slab (head+torso before, check no regression)
after time 8.4 { debug write memory 0xC004 56 ; debug write memory 0xC005 52 }
after time 9.4 { shot 3 }
# 4: north corridor under the shelf (check head artifact acceptable)
after time 9.6 { debug write memory 0xC004 24 ; debug write memory 0xC005 12 }
after time 10.6 { shot 4 ; exit }
