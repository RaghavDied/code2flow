int main() {
    int a = 5;
    int b = 10;
    int r = 0;
    if (a < b && a > 0) {
        r = 1;
    }
    if (a == 5 || b != 10) {
        r = r + 1;
    }
    if (!(a >= b)) {
        r = r + 1;
    }
    return r;
}
