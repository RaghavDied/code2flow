int main() {
    int x = 0;
    while (x < 10) {
        int y = 0;
        while (y < 10) {
            if (y == 5)
                break;
            y++;
        }
        if (x == 7)
            break;
        x++;
    }
    return 0;
}
