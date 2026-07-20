after time 6.0 { debug write memory 0xC00C 3 }
after time 6.5 { screenshot -raw ./build/p1.png }
after time 6.65 { screenshot -raw ./build/p2.png }
after time 6.8 { screenshot -raw ./build/p3.png }
after time 6.95 { screenshot -raw ./build/p4.png ; exit }
