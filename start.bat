@echo off
setlocal enabledelayedexpansion
title Lingshan AI Guide
set PYTHONUTF8=1
chcp 936 >nul 2>&1

echo.
echo   ==================================================
echo     Lingshan AI Digital Tour Guide System
echo   ==================================================
echo.

:: 进入项目根目录 —— 之后全部用相对路径，杜绝括号路径进入 if 块
pushd "%~dp0"

:: ========== 端口检查 ==========
set BACKEND_PORT=8000
set FRONTEND_PORT=5173
netstat -ano 2>nul | findstr ":%BACKEND_PORT%" >nul
if not errorlevel 1 echo [WARN] Port %BACKEND_PORT% is already in use!
netstat -ano 2>nul | findstr ":%FRONTEND_PORT%" >nul
if not errorlevel 1 echo [WARN] Port %FRONTEND_PORT% is already in use!

:: ========== 1/4 Python ==========
echo [1/4] Checking Python...
set "PY_EXE="
if exist "backend\python\python.exe" set "PY_EXE=backend\python\python.exe"
if defined PY_EXE goto :py_found
python --version >nul 2>&1
if errorlevel 1 goto :no_python
set "PY_EXE=python"
:py_found
echo        Using bundled portable Python ^(no install needed^)
echo        Python OK
:: 解析为绝对路径（供 start 命令使用，避免 /D 切目录后相对路径失效）
for %%A in ("%PY_EXE%") do set "PY_ABS=%%~fA"
goto :step2

:no_python
echo [FAIL] Python NOT found!
echo        Download: https://www.python.org/downloads/
pause
popd
exit /b 1

:: ========== 2/4 Node.js ==========
:step2
echo [2/4] Checking Node.js...
node --version >nul 2>&1
if not errorlevel 1 goto :node_ok
echo [FAIL] Node.js NOT found!
echo        Download: https://nodejs.org/
pause
popd
exit /b 1

:node_ok
echo        Node.js OK

:: ========== 3/4 Backend deps（子程序隔离） ==========
echo [3/4] Preparing backend...
call :do_backend_deps
echo        Backend OK

:: ========== 4/4 Frontend deps（goto 流控，零 if 括号块）==========
echo [4/4] Preparing frontend...
pushd frontend
if not exist node_modules goto :need_npm
echo        Frontend ready, skip
goto :frontend_done

:need_npm
echo        Installing frontend deps ^^(first time only^^^)...
call npm install
if errorlevel 1 (
    echo        [FAIL] npm install failed!
    pause
    popd
    popd
    exit /b 1
)

:frontend_done
popd

:: ========== 启动服务 ==========
echo.
echo   ==================================================
echo        Starting ... Browser will open automatically
echo        Visitor: http://localhost:%FRONTEND_PORT%
echo        Admin:   http://localhost:%FRONTEND_PORT%/login
echo        Account: admin / admin123
echo   ==================================================
echo.

:: 清理可能占用端口的旧进程（避免上次残留导致 uvicorn/vite 绑定失败）
echo        Cleaning up old processes on ports %BACKEND_PORT% / %FRONTEND_PORT%...
call :kill_port %BACKEND_PORT%
call :kill_port %FRONTEND_PORT%
timeout /t 2 /nobreak >nul

echo        Starting Backend on :%BACKEND_PORT%...
start "Backend" cmd /k "cd /d "%~dp0backend" && "%PY_ABS%" main.py"

echo        Starting Frontend on :%FRONTEND_PORT%...
start "Frontend" cmd /k "cd /d "%~dp0frontend" && npx vite --host"

:: ========== 等待后端就绪再开浏览器（避免 ECONNREFUSED 时序问题）==========
echo        Waiting for backend to be ready ^(max 60s^)...
call :wait_backend

echo        Opening browser now...
call :open_browser http://localhost:%FRONTEND_PORT%

echo.
echo        DONE! Services running in new windows.
pause
popd
exit /b 0


:: ================================================================
::  子程序区 —— 全部隔离执行，与主流程完全解耦
:: ================================================================

:do_backend_deps
if not defined PY_EXE goto :eof
"%PY_EXE%" -c "import fastapi" >nul 2>&1
if not errorlevel 1 goto :deps_ok
echo        [WARN] bundled Python missing deps, installing now...
"%PY_EXE%" -m pip install -r backend\requirements.txt
goto :eof
:deps_ok
echo        Backend deps OK ^(portable, skip install^)
goto :eof

:kill_port
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":%1" ^| findstr "LISTENING"') do taskkill /f /pid %%p >nul 2>&1
goto :eof

:wait_backend
set /a _tries=1
:wait_loop
netstat -ano 2>nul | findstr ":%BACKEND_PORT%" | findstr "LISTENING" >nul
if not errorlevel 1 goto :backend_ready
if !_tries! gtr 30 goto :backend_wait_fail
set /a _tries+=1
timeout /t 2 /nobreak >nul
goto :wait_loop

:backend_ready
echo        Backend is ready ^(checked !_tries! times^)!
goto :eof

:backend_wait_fail
echo        [WARN] Backend not listening after 60s. Check the Backend window for errors.
goto :eof

:open_browser
set "_URL=%~1"
set _CHROME=
set _EDGE=
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "_CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "_CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "_CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "_EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "_EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"

if defined _CHROME goto :use_chrome
if defined _EDGE goto :use_edge
echo        Using default browser
start "" "!_URL!"
goto :eof

:use_chrome
echo        Using Chrome
start "" "%_CHROME%" "!_URL!"
goto :eof

:use_edge
echo        Using Edge
start "" "%_EDGE%" "!_URL!"
goto :eof
