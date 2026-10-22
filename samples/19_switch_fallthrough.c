int main() {
    int x = 1;
    int y = 0;
    switch (x) {
        case 1:
            y = y + 1;
        case 2:
            y = y + 2;
            break;
        case 3:
            y = y + 3;
            break;
        default:
            y = -1;
    }
    return y;
}
