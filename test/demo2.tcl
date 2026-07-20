after time 5    { record start ./build/demo2 -doublesize }
after time 6    { keymatrixdown 8 0x80 }
after time 6.4  { keymatrixdown 8 0x01 }
after time 6.8  { keymatrixup 8 0x01 }
after time 7.15 { keymatrixup 8 0x80 }
after time 8    { keymatrixdown 8 0x40 }
after time 8.6  { keymatrixup 8 0x40 ; keymatrixdown 8 0x80 }
after time 9.6  { keymatrixup 8 0x80 }
after time 10   { keymatrixdown 8 0x20 }
after time 10.8 { keymatrixup 8 0x20 }
after time 12   { record stop ; exit }
