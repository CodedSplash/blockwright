// Небольшой пример, на котором удобно посмотреть, что умеет blockwright:
// ввод-вывод, счётный цикл, ветвление, switch и вызов своей функции.
//
//     python -m blockwright examples --open

#include <iostream>
#include <string>

const int MAX_STUDENTS = 30;

// Словесная оценка по баллу — на схеме превращается в switch с ветвями.
std::string verdict(int score) {
    switch (score / 10) {
        case 10:
        case 9:
            return "отлично";
        case 8:
        case 7:
            return "хорошо";
        case 6:
        case 5:
            return "удовлетворительно";
        default:
            return "неудовлетворительно";
    }
}

// Среднее по массиву — счётный цикл превращается в блок «подготовка».
double average(const int scores[], int count) {
    if (count <= 0) return 0.0;
    int sum = 0;
    for (int i = 0; i < count; i++) {
        sum += scores[i];
    }
    return static_cast<double>(sum) / count;
}

int main() {
    int scores[MAX_STUDENTS];
    int count = 0;

    std::cout << "Сколько студентов в группе? ";
    std::cin >> count;
    if (count < 1 || count > MAX_STUDENTS) {
        std::cout << "Допустимо от 1 до " << MAX_STUDENTS << " студентов" << std::endl;
        return 1;
    }

    for (int i = 0; i < count; i++) {
        std::cout << "Балл студента #" << i + 1 << ": ";
        std::cin >> scores[i];
        if (scores[i] < 0 || scores[i] > 100) {
            std::cout << "Балл вне диапазона 0..100, засчитан как 0" << std::endl;
            scores[i] = 0;
        }
    }

    int best = 0;
    for (int i = 1; i < count; i++) {
        if (scores[i] > scores[best]) best = i;
    }

    std::cout << "Средний балл: " << average(scores, count) << std::endl;
    std::cout << "Лучший результат: " << scores[best]
              << " (" << verdict(scores[best]) << ")" << std::endl;
    return 0;
}
