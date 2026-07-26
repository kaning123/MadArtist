// file_utils.hpp
#pragma once

#include <filesystem>
#include <string>
#include <stdexcept>
#include <initializer_list>
#include <windows.h>

namespace file_utils {

namespace fs = std::filesystem;

// 获取当前工作目录
inline fs::path get_current_working_directory() {
    return fs::current_path();
}

// 获取可执行文件所在目录（支持超长路径和 Unicode）
inline fs::path get_executable_directory() {
    // 初始缓冲区大小（通常足够，但支持动态增长）
    DWORD buffer_size = 4096;
    std::wstring wpath_buffer;
    
    while (true) {
        wpath_buffer.resize(buffer_size);
        DWORD ret = GetModuleFileNameW(
            NULL,
            &wpath_buffer[0],
            buffer_size
        );
        
        if (ret == 0) {
            DWORD error = GetLastError();
            throw std::runtime_error("GetModuleFileNameW 失败，错误码: " + std::to_string(error));
        }
        
        // 如果返回值小于缓冲区大小，说明成功且完整
        if (ret < buffer_size) {
            wpath_buffer.resize(ret);
            fs::path exe_full_path(wpath_buffer);
            return exe_full_path.parent_path();  // 返回目录部分
        }
        
        // 缓冲区不足，扩大一倍继续尝试
        buffer_size *= 2;
        // 防止恶意过大（可选）
        if (buffer_size > 65536) {
            throw std::runtime_error("GetModuleFileNameW 需要异常大的缓冲区，可能路径过长");
        }
    }
}

// 获取当前可执行文件的完整路径（如果需要）
inline fs::path get_executable_full_path() {
    // 复用上述逻辑，但返回完整路径
    DWORD buffer_size = 4096;
    std::wstring wpath_buffer;
    while (true) {
        wpath_buffer.resize(buffer_size);
        DWORD ret = GetModuleFileNameW(NULL, &wpath_buffer[0], buffer_size);
        if (ret == 0) {
            DWORD error = GetLastError();
            throw std::runtime_error("GetModuleFileNameW 失败，错误码: " + std::to_string(error));
        }
        if (ret < buffer_size) {
            wpath_buffer.resize(ret);
            return fs::path(wpath_buffer);
        }
        buffer_size *= 2;
        if (buffer_size > 65536) {
            throw std::runtime_error("缓冲区不足，路径过长");
        }
    }
}

// 获取当前可执行文件的父目录（即上一级目录）
inline fs::path get_executable_parent_directory() {
    return get_executable_directory().parent_path();
}

// 获取路径的父目录（向上 depth 级），使用迭代避免递归栈溢出
inline fs::path get_parent_directory(const fs::path& path, int depth) {
    if (depth < 0) {
        throw std::invalid_argument("depth 不能为负数");
    }
    fs::path current = path;
    for (int i = 0; i < depth; ++i) {
        fs::path parent = current.parent_path();
        // 如果已经到达根目录，parent_path() 可能返回自身，导致死循环
        if (parent == current) {
            // 已达根目录，无法继续向上
            return current;
        }
        current = parent;
    }
    return current;
}

// 路径拼接（两个）
inline fs::path join_paths(const fs::path& base, const fs::path& sub) {
    return base / sub;
}

// 路径拼接（多个）
inline fs::path join_paths(std::initializer_list<fs::path> paths) {
    fs::path result;
    for (const auto& p : paths) {
        result /= p;
    }
    return result;
}

// 删除文件，返回是否成功
inline bool delete_file(const fs::path& path) {
    return fs::remove(path);
}

// 为了保留原有函数名的兼容性（可选），可提供别名，但不推荐
// 如果确实需要，可以定义如下（但建议直接使用新命名）
// using get_my_work_dir = get_current_working_directory; // 不支持 using 别名模板? 可用内联转发
inline fs::path get_my_work_dir() { return get_current_working_directory(); }
inline fs::path get_my_dir2() { return get_executable_directory(); }
inline fs::path get_my_parent_dir() { return get_executable_parent_directory(); }
inline fs::path get_parent_dir(const fs::path& path, int depth) { return get_parent_directory(path, depth); }
inline fs::path merge_dir_txt(const fs::path& a, const fs::path& b) { return join_paths(a, b); }
inline fs::path merge_dir_txt2(std::initializer_list<fs::path> paths) { return join_paths(paths); }

} // namespace file_utils