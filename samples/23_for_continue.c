int main() {
    int i;
    int sum = 0;
    for (i = 0; i < 10; i++) {
        if (i % 2 == 0)
            continue;
        sum += i;
    }
    printf("%d", sum);
    return 0;
}
