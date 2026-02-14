@echo off
chcp 65001 >nul
title 劦佑機械 - 行政管理系統 安裝程式

echo ============================================
echo   劦佑機械 行政管理系統 - 安裝程式
echo ============================================
echo.

:: 檢查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 找不到 Python，請先安裝 Python 3.8 以上版本
    echo 下載網址: https://www.python.org/downloads/
    echo.
    echo 安裝時請務必勾選 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/3] 偵測到 Python:
python --version
echo.

:: 安裝依賴套件
echo [2/3] 安裝依賴套件...
echo.
pip install --upgrade pip >nul 2>&1
pip install ttkbootstrap>=1.10 Pillow>=10.0 PyMuPDF>=1.24 ezdxf>=0.19 matplotlib>=3.7 reportlab>=4.0

if %errorlevel% neq 0 (
    echo.
    echo [警告] 部分套件安裝可能失敗，請檢查上方訊息
) else (
    echo.
    echo [OK] 所有套件安裝完成
)

:: 建立必要目錄
echo.
echo [3/3] 建立必要目錄...
if not exist "data" mkdir data
if not exist "storage" mkdir storage
if not exist "storage\thumbnails" mkdir storage\thumbnails
if not exist "storage\drawings" mkdir storage\drawings

echo.
echo ============================================
echo   安裝完成！
echo ============================================
echo.
echo   啟動方式：
echo     1. 雙擊 run.bat
echo     2. 或執行: python main.py
echo.
pause
