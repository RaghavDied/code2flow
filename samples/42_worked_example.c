int main() {
    int a = 2 * 3;
    int b = a + 4;
    int unused = 99;
    if (1) {
        printf("%d", b);
    } else {
        printf("never");
    }
    return 0;
}
