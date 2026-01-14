@echo off
title AI Ethical Hacking Lab - All In One Launcher
echo =====================================================
echo        AI ETHICAL HACKING LAB - ONE CLICK MENU
echo =====================================================

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Installing modules...
pip install -r requirements.txt >nul

:MENU
cls
echo =====================================================
echo                 MAIN MENU
echo =====================================================
echo 1) Fast Scan
echo 2) Custom Port Scan
echo 3) Network Device Discovery
echo 4) Run Dashboard (Flask)
echo 5) Exit
echo =====================================================
set /p choice=Choose an option: 

if "%choice%"=="1" goto FAST
if "%choice%"=="2" goto CUSTOM
if "%choice%"=="3" goto DISCOVER
if "%choice%"=="4" goto DASH
if "%choice%"=="5" exit
goto MENU

:FAST
cls
echo =======================
echo       FAST SCAN
echo =======================
set /p target=Enter target (IP or domain): 
python main.py scan --target %target% --fast
pause
goto MENU

:CUSTOM
cls
echo =======================
echo     CUSTOM PORT SCAN
echo =======================
set /p target=Enter target (IP or domain): 
set /p ports=Enter ports (ex: 1-1024 or 22,80,443): 
python main.py scan --target %target% --ports %ports%
pause
goto MENU

:DISCOVER
cls
echo =============================
echo     NETWORK DISCOVERY
echo =============================
set /p net=Enter network range (ex: 192.168.1.0/24): 
python main.py discover --target %net%
pause
goto MENU

:DASH
cls
echo Starting Flask dashboard...
python -m webapp.app
pause
goto MENU
