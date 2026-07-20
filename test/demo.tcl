# record a short gameplay demo
after time 5   { record start ./build/demo -doublesize }
after time 6   { keymatrixdown 8 0x80 }
after time 7   { keymatrixdown 8 0x01 }
after time 7.4 { keymatrixup 8 0x01 }
after time 8.6 { keymatrixdown 8 0x01 }
after time 9.0 { keymatrixup 8 0x01 }
after time 10.2 { keymatrixdown 8 0x01 }
after time 10.6 { keymatrixup 8 0x01 }
after time 12  { keymatrixup 8 0x80 ; keymatrixdown 8 0x10 }
after time 13  { keymatrixup 8 0x10 }
after time 14  { record stop ; exit }
