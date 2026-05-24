#include <iostream>
#include <cstdio>
#include <string>

int PowerShell_call(std::string string_){
    std::string command = "powershell -Command \"" + string_ + "\"";
    std::cout << command << std::endl;
    return system(command.c_str());
}

int Extract_zip(std::string zip_path, std::string extract_path){
    std::string command = "Expand-Archive -Path \"" + zip_path + "\" -DestinationPath \"" + extract_path + "\" -Force";
    return PowerShell_call(command);
}

int DownloadFile(std::string url, std::string path){
    std::string command = "Invoke-WebRequest " + url + " -OutFile " + path;
    return PowerShell_call(command);
}