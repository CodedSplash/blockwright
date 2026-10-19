import java.util.Scanner;

public class Lab {
    static int gcd(int a, int b) {
        while (b != 0) {
            int t = a % b;
            a = b;
            b = t;
        }
        return a;
    }

    static String grade(int score) {
        switch (score / 10) {
            case 10:
            case 9:
                return "A";
            case 8:
                return "B";
            default:
                return "C";
        }
    }

    static String day(int d) {
        return switch (d) {
            case 6, 7 -> "weekend";
            default -> "weekday";
        };
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.print("n = ");
        int n = sc.nextInt();
        int[] a = new int[n];
        for (int i = 0; i < n; i++) {
            a[i] = sc.nextInt();
        }
        int sum = 0;
        for (int x : a) sum += x;
        System.out.println("Сумма: " + sum);
        System.out.printf("НОД(%d, %d) = %d%n", a[0], a[1], gcd(a[0], a[1]));
        outer:
        for (int i = n - 1; i >= 0; i -= 2) {
            if (a[i] < 0) break outer;
        }
        try {
            System.out.println(a[n]);
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("вне массива");
        } finally {
            sc.close();
        }
        do {
            n--;
        } while (n > 0);
        System.out.println(grade(sum));
    }
}
