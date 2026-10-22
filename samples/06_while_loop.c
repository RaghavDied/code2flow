int main() {
    int i = 0;
    int sum = 0;
    while (i < 10) {
        sum = sum + i;
        if (sum > 20) {
            break;
        }
        i++;
    }
    return sum;
}
