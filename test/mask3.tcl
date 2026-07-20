proc shot {n} { screenshot -raw ./build/mr$n.png }
after time 6   { debug write memory 0xC004 44 ; debug write memory 0xC005 72 }
after time 7   { shot 1 }
after time 7.2 { debug write memory 0xC004 56 ; debug write memory 0xC005 76 }
after time 8.2 { shot 2 }
after time 8.4 { debug write memory 0xC004 56 ; debug write memory 0xC005 52 }
after time 9.4 { shot 3 }
after time 9.6 { debug write memory 0xC004 88 ; debug write memory 0xC005 40 }
after time 10.6 { shot 4 ; exit }
