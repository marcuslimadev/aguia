@echo off
taskkill /F /IM python.exe /T 2>nul
timeout /t 2 /nobreak >nul
python fix_marcus_login.py
pause
