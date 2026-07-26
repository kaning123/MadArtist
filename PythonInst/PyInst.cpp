
#include <iostream>
#include <string>
#include <vector>
#include <cstdlib>
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <array>
#include <fstream>
#include "file_lib.hpp"

namespace fs = std::filesystem;


// 执行命令行命令并返回输出（Windows 下使用 _popen）
std::string exec_command(const std::string& cmd) {
    std::array<char, 128> buffer;
    std::string result;
#ifdef _WIN32
    std::unique_ptr<FILE, decltype(&_pclose)> pipe(_popen(cmd.c_str(), "r"), _pclose);
#else
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);
#endif
    if (!pipe) {
        throw std::runtime_error("popen() 失败!");
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    return result;
}

// 使用 WinHTTP 或 URLDownloadToFile 下载文件（简单实现）
bool download_file(const std::string& url, const fs::path& dest) {
    // 使用 Windows API URLDownloadToFile
    HRESULT hr = URLDownloadToFileA(
        nullptr,
        url.c_str(),
        dest.string().c_str(),
        0,
        nullptr
    );
    return SUCCEEDED(hr);
}

// 解压 ZIP 文件（使用 PowerShell 的 Expand-Archive）
bool extract_zip(const fs::path& zip_path, const fs::path& dest_dir) {
    // 确保目标目录存在
    fs::create_directories(dest_dir);
    
    std::string cmd = "powershell -Command \"Expand-Archive -Path '" 
                    + zip_path.string() + "' -DestinationPath '" 
                    + dest_dir.string() + "' -Force\"";
    
    int ret = system(cmd.c_str());
    return ret == 0;
}

// ---------- 主要逻辑 ----------

int main() {
    try {
        std::cout << "=== Python 3.13.0 Embed + pip 自动安装工具 ===" << std::endl;
        
        // 1. 获取当前工作目录（使用 file_utils）
        fs::path work_dir = file_utils::get_current_working_directory();
        std::cout << "工作目录: " << work_dir << std::endl;
        
        // 2. 设置下载目录
        fs::path download_dir = work_dir / "python_download";
        fs::create_directories(download_dir);
        
        // 3. 定义下载 URL
        // 根据系统架构选择（这里默认使用 64 位）
        std::string python_url = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-embed-amd64.zip";
        std::string pip_url = "https://bootstrap.pypa.io/get-pip.py";
        
        // 4. 下载 Python embed 压缩包
        fs::path python_zip = download_dir / "python-3.13.0-embed-amd64.zip";
        std::cout << "正在下载 Python 3.13.0 embed (64-bit) ..." << std::endl;
        if (!download_file(python_url, python_zip)) {
            throw std::runtime_error("下载 Python 失败！");
            return 1;
        }
        std::cout << "下载完成: " << python_zip << std::endl;
        
        // 5. 解压 Python
        fs::path python_dir = work_dir / "python313_embed";
        std::cout << "正在解压 Python 到: " << python_dir << std::endl;
        if (!extract_zip(python_zip, python_dir)) {
            throw std::runtime_error("解压 Python 失败！");
            return 2;
        }
        std::cout << "解压完成！" << std::endl;
        
        // 6. 修改 python313._pth 文件，启用 site 模块
        // 注意：版本号 3.13 对应 python313._pth
        fs::path pth_file = python_dir / "python313._pth";
        if (fs::exists(pth_file)) {
            std::cout << "正在配置 python313._pth ..." << std::endl;
            // 读取文件内容
            std::ifstream in_file(pth_file);
            std::string content;
            std::string line;
            while (std::getline(in_file, line)) {
                // 取消注释 import site
                if (line.find("#import site") != std::string::npos) {
                    line = "import site";
                }
                content += line + "\n";
            }
            in_file.close();
            
            // 写回文件
            std::ofstream out_file(pth_file);
            out_file << content;
            out_file.close();
            std::cout << "python313._pth 配置完成！" << std::endl;
        } else {
            std::cerr << "警告: 未找到 python313._pth 文件" << std::endl;
        }
        
        // 7. 下载 get-pip.py
        fs::path pip_script = python_dir / "get-pip.py";
        std::cout << "正在下载 get-pip.py ..." << std::endl;
        if (!download_file(pip_url, pip_script)) {
            throw std::runtime_error("下载 get-pip.py 失败！");
            return 3;
        }
        std::cout << "下载完成: " << pip_script << std::endl;
        
        // 8. 运行 get-pip.py 安装 pip
        fs::path python_exe = python_dir / "python.exe";
        std::cout << "正在安装 pip ..." << std::endl;
        fs::path cmd = work_dir / "GetPip.bat";
        std::string cmd_ = cmd.string();
        std::cout << "命令: " << cmd << std::endl;
        int ret = system(cmd_.c_str());
        if (ret != 0) {
            throw std::runtime_error("安装 pip 失败！");
            return 4;
        }
        std::cout << "pip 安装完成！" << std::endl;
        
        // 9. 验证 pip 是否可用
        std::cout << "验证 pip 安装 ..." << std::endl;
        std::string verify_cmd = "\"" + python_exe.string() + "\" -m pip --version";
        std::string version = exec_command(verify_cmd);
        std::cout << version << std::endl;
        
        // 10. 清理临时文件（可选）
        // std::cout << "清理临时文件 ..." << std::endl;
        // 删除下载的 zip 和 get-pip.py
        // file_utils::delete_file(python_zip);
        // file_utils::delete_file(pip_script);
        
        std::cout << "\n=== 安装成功！ ===" << std::endl;
        std::cout << "Python 目录: " << python_dir << std::endl;
        std::cout << "使用方法: " << python_dir << "\\python.exe your_script.py" << std::endl;
        std::cout << "或使用 pip: " << python_dir << "\\python.exe -m pip install 包名" << std::endl;
        
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "错误: " << e.what() << std::endl;
        return 1;
    }
}