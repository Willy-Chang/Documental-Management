@echo off
chcp 65001 >nul
title 劦佑機械 - 業務管理系統
cd /d "%~dp0"
python main.py
if %errorlevel% neq 0 (
    echo.
    echo 程式異常結束，錯誤代碼: %errorlevel%
    pause
)
