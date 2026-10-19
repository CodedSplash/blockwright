#pragma once
#include <string>

class Widget {
public:
    std::string label() const {
        if (name_.empty()) return "<none>";
        return name_;
    }
private:
    std::string name_;
};
