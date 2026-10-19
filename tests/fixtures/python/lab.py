"""Лабораторная: обработка массива."""
import random


class Stats:
    def __init__(self, data):
        self.data = data

    def mean(self) -> float:
        if not self.data:
            raise ValueError("пусто")
        return sum(self.data) / len(self.data)


def bubble(a):
    n = len(a)
    for i in range(n - 1):
        swapped = False
        for j in range(0, n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break
    return a


def find(a, key):
    for i, x in enumerate(a):
        if x == key:
            print("Найдено на позиции", i)
            break
    else:
        print("Не найдено")
    k = 10
    while k > 0:
        k -= 3
    else:
        k = 0
    for t in range(10, 0, -2):
        pass


def classify(code):
    match code:
        case 200 | 201:
            return "ok"
        case 404:
            return "not found"
        case _:
            return "error"


def main():
    n = int(input("Сколько чисел? "))
    a = [random.randint(1, 100) for _ in range(n)]
    print("Исходный:", a)
    bubble(a)
    print(f"Отсортированный: {a}")
    try:
        print("Среднее: %.2f" % Stats(a).mean())
    except ValueError as e:
        print("Ошибка:", e)
    except Exception:
        raise
    finally:
        print()
    with open("out.txt", "w") as fh:
        fh.write(str(a))
    find(a, 42)


n = int(input())
total = 0
for i in range(1, n + 1):
    total += i
print("Сумма:", total)

if __name__ == "__main__":
    main()
