#include <stdio.h>
#include <stdbool.h>

bool isPrime(int n) {
    if (n <= 1) return false;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}

int main() {
    int n, count, num;
    printf("Enter the value of N (the number of first prime numbers to display): ");
    scanf("%d", &n);

    if (n <= 0) {
        printf("N must be a positive integer.\n");
        return 1;
    }

    printf("The first %d prime numbers are:\n", n);

    count = 0;
    num = 2;

    while (count < n) {
        if (isPrime(num)) {
            printf("%d ", num);
            count++;
        }
        num++;
    }

    printf("\n");
    return 0;
}