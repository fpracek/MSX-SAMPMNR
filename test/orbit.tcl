after time 5   { record start ./build/orbit -doublesize }
# start SE of conveyor, orbit counter-clockwise touching every side
after time 6   { debug write memory 0xC004 120 ; debug write memory 0xC005 70 }
after time 6.5 { keymatrixdown 8 0x20 }
after time 8.3 { keymatrixup 8 0x20 ; keymatrixdown 8 0x10 }
after time 11  { keymatrixup 8 0x10 ; keymatrixdown 8 0x40 }
after time 12.8 { keymatrixup 8 0x40 ; keymatrixdown 8 0x80 }
after time 15.5 { keymatrixup 8 0x80 }
# then walk INTO the conveyor from east and from south (blocked, close)
after time 16  { keymatrixdown 8 0x10 }
after time 17.5 { keymatrixup 8 0x10 ; keymatrixdown 8 0x20 }
after time 19  { keymatrixup 8 0x20 }
after time 20  { record stop ; exit }
