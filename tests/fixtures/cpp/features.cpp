#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
#include <stdexcept>

namespace geo {

struct Point {
    double x, y;
    double norm2() const { return x * x + y * y; }
};

class Shape {
public:
    virtual ~Shape() {}
    virtual double area() const = 0;
    bool operator<(const Shape &o) const { return area() < o.area(); }
};

double total(const std::vector<Shape *> &shapes) {
    double sum = 0;
    for (const auto &s : shapes) {
        sum += s->area();
    }
    for (auto *s : shapes) delete s;
    return sum;
}

}  // namespace geo

template <typename T>
T maxOf(T a, T b) { return a > b ? a : b; }

int parse(const std::string &s) {
    try {
        int v = std::stoi(s);
        if (v < 0) throw std::invalid_argument("negative");
        return v;
    } catch (const std::invalid_argument &e) {
        std::cerr << "bad: " << e.what() << std::endl;
    } catch (...) {
        throw;
    }
    return 0;
}

void table(int n) {
    std::cout << std::fixed << std::setprecision(2);
    for (int i = 1; i <= n; i++) {
        for (int j = n; j > 0; --j)
            std::cout << std::setw(4) << i * j;
        std::cout << '\n';
    }
    std::cout << std::endl;
}

int main() {
    std::string line;
    int n = 0;
    std::getline(std::cin, line);
    std::cin >> n >> line;
    n = parse(line);
    table(n);
    std::cout << "max = " << maxOf(n, 3) << ", text \"" << line << "\"\n";
    std::vector<int> v{1, 2, 3};
    for (int x : v) {
        if (x % 2) {
            std::cout << x;
        } else {
            continue;
        }
    }
    int i = 0;
    while (true) {
        if (++i > 10) break;
    }
    switch (n) {
    case 1:
    case 2: {
        std::cout << "small" << std::endl;
        break;
    }
    case 3:
        return 3;
    }
    printf("%s\n", line.c_str());
    return 0;
}
