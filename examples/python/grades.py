# Тот же пример, что grades.cpp, но на Python: код вне функций
# становится отдельной схемой, а range() — счётным циклом.
#
#     python -m blockwright examples/python --open

MAX_STUDENTS = 30


def verdict(score):
    """Словесная оценка по баллу — match превращается в ветвление."""
    match score // 10:
        case 10 | 9:
            return "отлично"
        case 8 | 7:
            return "хорошо"
        case 6 | 5:
            return "удовлетворительно"
        case _:
            return "неудовлетворительно"


def average(scores):
    if not scores:
        return 0.0
    total = 0
    for s in scores:
        total += s
    return total / len(scores)


count = int(input("Сколько студентов в группе? "))
if count < 1 or count > MAX_STUDENTS:
    print("Допустимо от 1 до", MAX_STUDENTS, "студентов")
    raise SystemExit(1)

scores = []
for i in range(count):
    score = int(input(f"Балл студента #{i + 1}: "))
    if score < 0 or score > 100:
        print("Балл вне диапазона 0..100, засчитан как 0")
        score = 0
    scores.append(score)

best = 0
for i in range(1, count):
    if scores[i] > scores[best]:
        best = i

print(f"Средний балл: {average(scores):.1f}")
print("Лучший результат:", scores[best], f"({verdict(scores[best])})")
