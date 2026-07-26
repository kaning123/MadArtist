@echo off
chcp 65001>nul
cd /d %~dp0
cd /d python313_embed
python.exe get-pip.py