// The same demo as grades.cpp, with English prompts — handy for building
// English-language charts:
//
//     python -m blockwright examples/grades.en.cpp --ui-lang en --open

#include <iostream>
#include <string>

const int MAX_STUDENTS = 30;

// A verdict for a score — becomes a switch with one column per case.
std::string verdict(int score) {
    switch (score / 10) {
        case 10:
        case 9:
            return "excellent";
        case 8:
        case 7:
            return "good";
        case 6:
        case 5:
            return "satisfactory";
        default:
            return "failed";
    }
}

// Mean of an array — a counting loop becomes a preparation block.
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

    std::cout << "How many students are in the group? ";
    std::cin >> count;
    if (count < 1 || count > MAX_STUDENTS) {
        std::cout << "Expected 1 to " << MAX_STUDENTS << " students" << std::endl;
        return 1;
    }

    for (int i = 0; i < count; i++) {
        std::cout << "Score of student #" << i + 1 << ": ";
        std::cin >> scores[i];
        if (scores[i] < 0 || scores[i] > 100) {
            std::cout << "Score is out of 0..100, counted as 0" << std::endl;
            scores[i] = 0;
        }
    }

    int best = 0;
    for (int i = 1; i < count; i++) {
        if (scores[i] > scores[best]) best = i;
    }

    std::cout << "Average score: " << average(scores, count) << std::endl;
    std::cout << "Best result: " << scores[best]
              << " (" << verdict(scores[best]) << ")" << std::endl;
    return 0;
}
