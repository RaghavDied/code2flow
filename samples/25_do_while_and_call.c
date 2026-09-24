int square(int x) {
    return x * x;
}

int main() {
    int a = 5;
    do {
        a = square(a) - 20;
    } while (a > 0);
    printf("%d", a);
    return 0;
}
