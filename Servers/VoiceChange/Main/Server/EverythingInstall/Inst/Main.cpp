#include <iostream>
#include <cstdio>
#include <string>
#include "file_lib.hpp"
#include "PowerShell_Call.hpp"
#include "Cmd_Call.hpp"


int main() {
    fs::path MY_DIR = get_my_parent_dir();
    fs::path ROOT_DIR = get_my_parent_dir().parent_path();
    fs::path TEMP_DIR = merge_dir_txt(MY_DIR, "Temp");
    std::string GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py";
    std::string PYTHON_313_7_EMBED_AMD64_ZIP_URL = "https://www.python.org/ftp/python/3.13.7/python-3.13.7-embed-amd64.zip";
    fs::path GET_PIP_FILE = "get-pip.py";
    fs::path PYTHON_313_7_EMBED_AMD64_ZIP = "python-3.13.7-embed-amd64.zip";
    fs::path BUILD_PY = "Build.py";
    fs::path EVERYTHING_URL = "https://www.voidtools.com/Everything-1.4.1.1032.x64.zip";
    fs::path EVERYTHING_ZIP = "Everything-1.4.1.1032.x64.zip";
    fs::path THIRD_PARTY_DIR = merge_dir_txt(MY_DIR, "ThirdParty");
    fs::path EVERYTHING_EXE_PATH = merge_dir_txt(MY_DIR, merge_dir_txt(THIRD_PARTY_DIR, merge_dir_txt("Everything", "Everything.exe")));
    fs::path everything_path = merge_dir_txt(TEMP_DIR, EVERYTHING_ZIP);
    int h = DownloadFile(EVERYTHING_URL.string(), everything_path.string());
    if (h != 0) {
        std::cout << "Failed to download Everything" << std::endl;
        return 1;
    }
    createFolder(merge_dir_txt(THIRD_PARTY_DIR, "Everything"));
    int i = Extract_zip(everything_path.string(), merge_dir_txt(THIRD_PARTY_DIR, "Everything").string());
    if (i != 0) {
        std::cout << "Failed to extract Everything" << std::endl;
        return 1;
    }
    std::cout << "Successfully installed Everything" << std::endl;
    bool j = delete_file(everything_path.string());
    if (!j) {
        std::cout << "Failed to delete Everything zip file" << std::endl;
        return 1;
    }
    std::cout << "Installing Everything Service..." << std::endl;
    std::string command = "\"" + EVERYTHING_EXE_PATH.string() + "\" -install-service";
    int k = Cmd_call(command);
    if (k != 0) {
        std::cout << "Failed to install Everything Service" << std::endl;
        return 1;
    }
    std::cout << "Successfully installed Everything Service" << std::endl;
    std::cout << "Successfully deleted temporary files." << std::endl;
    return 0;

}
