
# Boot test: wait then screenshot and exit
after time 6 {
    screenshot -raw ./build/shot.png
    exit
}
