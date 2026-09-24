int main() {
    int choice;
    scanf("%d", &choice);
    switch (choice) {
        case 1:
            printf("One");
        case 2:
            printf("Two");
            break;
        default:
            printf("Other");
    }
    return 0;
}
