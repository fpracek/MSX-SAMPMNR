proc shot {n} { screenshot -raw ./build/mq$n.png }
after time 6   { debug write memory 0xC004 56 ; debug write memory 0xC005 52 }
after time 7   { shot 1 }
after time 7.2 { debug write memory 0xC004 88 ; debug write memory 0xC005 56 }
after time 8.2 { shot 2 }
after time 8.4 { debug write memory 0xC004 88 ; debug write memory 0xC005 36 }
after time 9.4 { shot 3 }
after time 9.6 { debug write memory 0xC004 30 ; debug write memory 0xC005 20 }
after time 10.6 { shot 4 ; exit }
