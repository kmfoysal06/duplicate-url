@echo off
title SEO Duplicate-Page Detection System Launcher
echo ========================================================
echo   Starting SEO Duplicate-Page Detection System
echo ========================================================
echo.

set "NODE_PATH=C:\Users\Mizan\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.20.0-win-x64"
set "PATH=%NODE_PATH%;C:\Users\Mizan\AppData\Local\Programs\Python\Python312;C:\Users\Mizan\AppData\Local\Programs\Python\Python312\Scripts;%PATH%"

echo [1/2] Starting Python FastAPI Backend on http://127.0.0.1:8000...
start "SEO Backend (Port 8000)" /D "%~dp0backend" "%~dp0backend\venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000

echo [2/2] Starting Next.js Frontend on http://localhost:3000...
start "SEO Frontend (Port 3000)" /D "%~dp0frontend" cmd /c "npm run dev -- -p 3000"

echo.
echo Application started!
echo Frontend: http://localhost:3000
echo Backend API Docs: http://127.0.0.1:8000/docs
echo.
echo Keep this window open or press any key to exit launcher.
pause
