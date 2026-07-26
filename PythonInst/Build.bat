@echo off
chcp 65001>nul
cd /d %~dp0
g++ -fdiagnostics-color=always -g PyInst.cpp -o PyInst.exe -lurlmon
:: 需要有g++才可运行