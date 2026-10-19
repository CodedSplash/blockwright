int n = int.Parse(Console.ReadLine()!);
for (int i = 1; i <= n; i++)
{
    if (i % 15 == 0) Console.WriteLine("FizzBuzz");
    else if (i % 3 == 0) Console.WriteLine("Fizz");
    else Console.WriteLine(i);
}
