#include <iostream>
#include <filesystem>
#include <initializer_list>
#include <windows.h>
#include <iostream>

namespace fs = std::filesystem;

fs::path get_my_work_dir(){
    return fs::current_path();
}

fs::path get_my_dir(){
    char szPath[MAX_PATH] = {0};
    GetModuleFileName(NULL, szPath, MAX_PATH);
    std::string strPath = szPath;
    fs::path path_ = fs::path(strPath);
    return path_;
}

fs::path get_my_dir2(){
    // 用宽字符缓冲区（wchar_t），更好支持中文路径和Windows Unicode接口
    // 分配4096字符缓冲区，抛弃MAX_PATH，应对超长路径场景
    std::wstring wpath_buffer(4096, L'\0');
    
    // 使用宽字符版本API GetModuleFileNameW（Windows推荐优先使用Unicode接口）
    DWORD ret = GetModuleFileNameW(
        NULL,                // 获取当前进程主模块
        &wpath_buffer[0],    // 宽字符缓冲区首地址
        static_cast<DWORD>(wpath_buffer.size()) // 缓冲区大小
    );
    
    if (ret == 0) {
        // 调用失败，获取错误码并抛出异常
        DWORD error_code = GetLastError();
        throw std::runtime_error("GetModuleFileNameW调用失败，错误码：" + std::to_string(error_code));
    }
    if (ret >= wpath_buffer.size()) {
        // 极少数情况：缓冲区仍不足，抛出异常提示
        throw std::runtime_error("GetModuleFileNameW：缓冲区大小不足，无法容纳完整路径");
    }
    
    // 截断缓冲区，去除多余的空字符（仅保留有效路径长度）
    wpath_buffer.resize(ret);
    
    // 转换为fs::path，并提取可执行文件所在目录（修正函数名语义）
    fs::path exe_full_path(wpath_buffer);  // 可执行文件完整路径（如D:\test\myapp.exe）
    fs::path exe_dir = exe_full_path;
    
    return exe_dir;
}

fs::path get_my_parent_dir(){
    return get_my_dir2().parent_path();
}

fs::path get_parent_dir(fs::path path_, int depth){
    if(depth == 0){
        return path_;
    }
    return get_parent_dir(path_.parent_path(), depth-1);
}

fs::path merge_dir_txt(fs::path a, fs::path b){
    return a / b;
}

fs::path merge_dir_txt2(std::initializer_list<fs::path> paths){
    fs::path Temp;
    for(fs::path p : paths){
        Temp /= p;
    }
    return Temp;
}

bool delete_file(fs::path path_){
        fs::remove(path_);
        return true;
}

bool createFolder(const fs::path& folderPath) {
    std::error_code ec;
    if (fs::create_directories(folderPath, ec)) {
        std::cout << "Successfully created: " << folderPath << std::endl;
        return true;
    }
    
    if (ec) {
        std::cerr << "Create directory failed: " << folderPath 
                  << ",Error code: " << ec.value() << ",Message: " << ec.message() << std::endl;
        return false;
    }
    
    // 目录已存在时 ec 值为 0
    std::cout << "Folder already exists: " << folderPath << std::endl;
    return true;
}