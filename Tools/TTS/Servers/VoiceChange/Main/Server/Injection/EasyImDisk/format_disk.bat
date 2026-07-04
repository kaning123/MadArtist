@echo off
chcp 65001 >nul 
setlocal enabledelayedexpansion

:: 检测当前是否为管理员权限，若非则请求提升
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 正在请求管理员权限...
    goto UACPrompt
) else (
    goto gotAdmin
)

:UACPrompt
:: 创建临时VBS脚本实现自动提权（无需手动点击"是"）
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "%*", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
:: 确认已获取管理员权限，切换到脚本所在目录
    chcp 65001 >nul 
    pushd "%CD%"
    CD /D "%~dp0"

:: ====================== 第一步：参数校验 ======================
:: 检查是否传入命令行参数
if "%~1"=="" (
    echo 错误：未指定要格式化的盘符！
    echo 使用方法：%0 [盘符] （示例：%0 E: 或 %0 F:）
    pause
    exit /b 1
)

:: 提取并标准化盘符（确保格式为 X:）
set "TARGET_DRIVE=%~1"
:: 去除盘符后的多余字符（如用户输入 E:\ 则转为 E:）
if "!TARGET_DRIVE:~2,1!"=="\" set "TARGET_DRIVE=!TARGET_DRIVE:~0,2!"
:: 检查盘符格式是否合法（必须是 字母+冒号）



cls

:: ======================== 执行格式化 ========================
echo.
echo 正在格式化 !TARGET_DRIVE! ...
echo 格式化参数：NTFS 文件系统，快速格式化，卷标为 "RamDisk"
:: format 命令说明：
:: /FS:NTFS   - 文件系统为NTFS（可改为 FAT32、exFAT）
:: /Q         - 快速格式化（取消则为完整格式化，耗时久）
:: /V:LABEL   - 卷标（自定义名称）
:: /Y         - 跳过格式化确认（已通过上方手动确认，此处可自动执行）
format !TARGET_DRIVE! /FS:NTFS /Q /V:RamDisk /Y

:: ====================== 第四步：结果校验 ======================
if errorlevel 1 (
    echo.
    echo 错误：格式化 !TARGET_DRIVE! 失败！
    pause
    exit /b 1
) else (
    echo.
    echo 成功：!TARGET_DRIVE! 已完成格式化！
    exit /b 0
)

endlocal