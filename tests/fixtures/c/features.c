#include <stdio.h>
#include <stdlib.h>

int square(int x);

int square(int x) { return x * x; }

static void report(FILE *out, int total, double avg) {
    fprintf(out, "Total: %d, avg: %.2f%%\n", total, avg);
    fputs("done\n", out);
    putchar('\n');
    puts("Bye");
}

int find(const int *a, int n, int key) {
    int i;
    for (i = 0; i < n; ++i) {
        if (a[i] == key)
            return i;
    }
    for (i = n - 1; i >= 0; i -= 2) {
        if (a[i] < 0) continue;
    }
    for (;;) {
        break;
    }
    for (i = 0; i < n && a[i]; i++) { }
    for (i = 10; i > 0; i = i - 1) { square(i); }
    return -1;
}

int main(void) {
    int n, k = 0;
    char name[32];
    printf("Enter n: ");
    scanf("%d", &n);
    fscanf(stdin, "%d %d", &n, &k);
    gets(name);
    printf("%d %s", n);
    printf(name);
    do {
        k++;
        if (k > 100) goto out;
    } while (k < n);
    while (n--) {
        switch (n % 3) {
        case 0:
            printf("zero\n");
        case 1:
            k += square(n);
            break;
        default:
            continue;
        }
    }
out:
    report(stdout, k, k / 2.0);
    if (k == 0) {
        return EXIT_FAILURE;
    } else if (k < 0) {
        exit(1);
    } else {
        ;
    }
    return EXIT_SUCCESS;
}
