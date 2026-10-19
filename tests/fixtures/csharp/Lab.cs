using System;

namespace Labs
{
    class Program
    {
        static int Factorial(int n) => n <= 1 ? 1 : n * Factorial(n - 1);

        static double Average(int[] a)
        {
            if (a.Length == 0)
                throw new ArgumentException("empty");
            double s = 0;
            foreach (var x in a)
                s += x;
            return s / a.Length;
        }

        static void Main(string[] args)
        {
            Console.Write("Введите n: ");
            int n = int.Parse(Console.ReadLine());
            var a = new int[n];
            for (int i = 0; i < n; ++i)
            {
                a[i] = int.Parse(Console.ReadLine());
            }
            Console.WriteLine($"Среднее: {Average(a):F2}");
            Console.WriteLine("{0}! = {1}", n, Factorial(n));
            switch (n % 3)
            {
                case 0:
                    Console.WriteLine("кратно 3");
                    break;
                case 1:
                case 2:
                    Console.WriteLine("остаток " + n % 3);
                    break;
                default:
                    return;
            }
            try
            {
                Console.WriteLine(a[n]);
            }
            catch (IndexOutOfRangeException e)
            {
                Console.WriteLine(e.Message);
            }
            using (var w = new System.IO.StringWriter())
            {
                w.Write(n);
            }
            Console.ReadKey();
        }
    }
}
