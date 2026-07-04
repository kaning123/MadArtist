#include <iostream>
#include <cstdio>
#include <string>

#include <vector>
#include <string>

std::string join(const std::vector<std::string>& parts, const std::string& delimiter) {
    if (parts.empty()) return "";
    size_t total_size = (parts.size() - 1) * delimiter.size();
    for (const auto& s : parts) total_size += s.size();
    
    std::string result;
    result.reserve(total_size);
    result += parts[0];
    for (size_t i = 1; i < parts.size(); ++i) {
        result += delimiter;
        result += parts[i];
    }
    return result;
}

int Cmd_call(std::string string_){
    std::string command = "cmd /c " + string_;
    std::cout << command << std::endl;
    return system(command.c_str());
}

int Cmd_call_list(std::vector<std::string> list_){
    std::string command = "cmd /c " + join(list_, " ");
    std::cout << command << std::endl;
    return system(command.c_str());
}