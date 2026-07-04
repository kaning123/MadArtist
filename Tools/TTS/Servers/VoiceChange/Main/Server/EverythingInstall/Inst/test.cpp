#include <windows.h>
#include <iostream>
#include <string>
#include <filesystem>
#include <string>
#include <stdexcept>

// 命名空间别名，简化std::filesystem的使用
namespace fs = std::filesystem;

fs::path get_my_dir() {
    // 1. 改用宽字符缓冲区（wchar_t），更好支持中文路径和Windows Unicode接口
    // 分配4096字符缓冲区，抛弃MAX_PATH，应对超长路径场景
    std::wstring wpath_buffer(4096, L'\0');
    
    // 2. 使用宽字符版本API GetModuleFileNameW（Windows推荐优先使用Unicode接口）
    DWORD ret = GetModuleFileNameW(
        NULL,                // 获取当前进程主模块
        &wpath_buffer[0],    // 宽字符缓冲区首地址
        static_cast<DWORD>(wpath_buffer.size()) // 缓冲区大小
    );
    
    // 3. 增加完整错误处理
    if (ret == 0) {
        // 调用失败，获取错误码并抛出异常，方便调用者排查问题
        DWORD error_code = GetLastError();
        throw std::runtime_error("GetModuleFileNameW调用失败，错误码：" + std::to_string(error_code));
    }
    if (ret >= wpath_buffer.size()) {
        // 极少数情况：缓冲区仍不足，抛出异常提示
        throw std::runtime_error("GetModuleFileNameW：缓冲区大小不足，无法容纳完整路径");
    }
    
    // 4. 截断缓冲区，去除多余的空字符（仅保留有效路径长度）
    wpath_buffer.resize(ret);
    
    // 5. 转换为fs::path，并提取可执行文件所在目录（修正函数名语义）
    fs::path exe_full_path(wpath_buffer);  // 可执行文件完整路径（如D:\test\myapp.exe）
    fs::path exe_dir = exe_full_path;
    
    // 6. 返回目录路径，匹配函数名get_my_dir
    return exe_dir;
}
int main() {
   std::cout << "程序路径: " << get_my_dir() << std::endl;
   return 0;
}