@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title 校园智导 · 一键演示启动

:: ============================================================
::  校园智导 AI 数字人新生校园导览 —— 一键启动脚本（Windows）
::  功能：① 自动安装缺失依赖  ② 启动前后端  ③ 自动打开首页
::  说明：项目已内置便携 Python（backend\python），评委机无需预装；
::        API Key 写在项目根 .env 中，脚本会自动同步到 backend\.env。
:: ============================================================

:: ---------- 路径 ----------
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
set "BACKEND=%PROJECT_ROOT%\backend"
set "FRONTEND=%PROJECT_ROOT%\frontend"
set "INDEX_FILE=%BACKEND%\indexes\lingshan.index"

echo ============================================================
echo   校园智导 AI 数字人 · 一键演示启动
echo ============================================================
echo.

:: ---------- 1/6 Python 环境 ----------
echo [1/6] 检查 Python 环境...
set "PY="
if exist "%BACKEND%\python\python.exe" (
    set "PY=%BACKEND%\python\python.exe"
    echo     使用项目内置 Python: %PY%
) else (
    where python >nul 2>nul && (set "PY=python" & echo     使用系统 Python)
    if not defined PY ( where py >nul 2>nul && (set "PY=py -3" & echo     使用 py launcher) )
)
if not defined PY (
    echo [错误] 未找到 Python，且项目未携带内置 Python。
    echo        请安装 Python 3.10+ 后重试，或恢复 backend\python 目录。
    pause & exit /b 1
)

:: 依赖自检：缺则安装
"%PY%" -c "import fastapi" >nul 2>nul
if errorlevel 1 (
    echo     未检测到后端依赖，正在安装 backend\requirements.txt ...
    "%PY%" -m pip install -r "%BACKEND%\requirements.txt"
) else (
    echo     后端依赖已就绪。
)
echo.

:: ---------- 2/6 API Key 配置 ----------
echo [2/6] 检查 API Key 配置...
if not exist "%BACKEND%\.env" (
    if exist "%PROJECT_ROOT%\.env" (
        copy /Y "%PROJECT_ROOT%\.env" "%BACKEND%\.env" >nul
        echo     已将项目根 .env 同步到 backend\.env
    ) else (
        echo [警告] 未找到 .env，将以“离线回放模式”运行（仅能回答内置常见问题）。
        echo         如需实时问答，请把含 API Key 的 .env 放到项目根目录后重跑本脚本。
        if exist "%PROJECT_ROOT%\.env.example" copy /Y "%PROJECT_ROOT%\.env.example" "%BACKEND%\.env" >nul
    )
) else (
    echo     backend\.env 已存在。
)
echo.

:: ---------- 3/6 FAISS 知识库索引 ----------
echo [3/6] 检查 FAISS 知识库索引...
if not exist "%INDEX_FILE%" (
    echo     索引缺失，正在自动构建（需要联网 + API Key）...
    pushd "%BACKEND%"
    "%PY%" -m app.knowledge.indexer
    if errorlevel 1 (
        echo [警告] 索引构建失败（可能无外网或无 Key）。
        echo         已内置离线回放库，常见问题仍可演示；请联网/配 Key 后重跑本脚本。
    ) else (
        echo     索引构建完成。
    )
    popd
) else (
    echo     索引已存在，跳过构建。
)
echo.

:: ---------- 4/6 Node.js 环境 ----------
echo [4/6] 检查 Node.js 环境...
set "NEED_NODE=1"
where node >nul 2>nul
if not errorlevel 1 (
    echo     已检测到 Node.js: 
    node -v
    set "NEED_NODE=0"
) else (
    echo     未检测到 Node.js，尝试自动下载便携版（约 30MB）...
    powershell -NoProfile -Command "$v='v20.18.0'; $url=\"https://nodejs.org/dist/$v/node-$v-win-x64.zip\"; $tmp=\"$env:TEMP\node_install.zip\"; try { Invoke-WebRequest -Uri $url -OutFile $tmp -TimeoutSec 150 -ErrorAction Stop; Expand-Archive -Path $tmp -DestinationPath \"%PROJECT_ROOT%\tools" -Force -ErrorAction Stop; Write-Host 'NODE_OK' } catch { Write-Host \"NODE_FAIL:$_\" }"
    if exist "%PROJECT_ROOT%\tools\node-v20.18.0-win-x64\node.exe" (
        set "PATH=%PROJECT_ROOT%\tools\node-v20.18.0-win-x64;%PATH%"
        echo     便携 Node.js 已就绪。
        set "NEED_NODE=0"
    ) else (
        echo [警告] 自动下载 Node.js 失败（可能无外网）。
        echo         请手动安装 Node.js 18+：https://nodejs.org ，装后重新运行本脚本。
    )
)
echo.

:: ---------- 5/6 前端依赖 ----------
if %NEED_NODE%==0 (
    if not exist "%FRONTEND%\node_modules" (
        echo [5/6] 安装前端依赖（首次较慢，请稍候）...
        pushd "%FRONTEND%"
        call npm install
        popd
    ) else (
        echo [5/6] 前端依赖已存在，跳过安装。
    )
) else (
    echo [5/6] 跳过前端依赖安装（Node.js 不可用）。
)
echo.

:: ---------- 6/6 释放端口并启动 ----------
echo [6/6] 释放端口 8000 / 5173（如被占用）...
powershell -NoProfile -Command "foreach($p in @(8000,5173)){ $c=Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue; if($c){ Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host \"  已释放端口 $p\" } }"
echo.

echo 正在启动后端服务（端口 8000）...
start "校园智导 · 后端(8000)" /D "%BACKEND%" cmd /k ""%PY%" main.py"

if %NEED_NODE%==0 (
    echo 正在启动前端服务（端口 5173）...
    start "校园智导 · 前端(5173)" /D "%FRONTEND%" cmd /k npm run dev
) else (
    echo 跳过前端服务启动（缺少 Node.js）。
)
echo.

:: ---------- 等待后端就绪并打开浏览器 ----------
echo 等待后端就绪...
set "HAVE_CURL=0"
where curl >nul 2>nul && set "HAVE_CURL=1"
set "READY=0"
for /L %%i in (1,1,40) do (
    if !HAVE_CURL!==1 (
        curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/health 2>nul | findstr "200" >nul && (set "READY=1" & goto :OPEN)
    )
    timeout /t 1 >nul
)
if !HAVE_CURL!==0 ( set "READY=1" )

:OPEN
if %READY%==1 (
    echo 后端已就绪。正在打开浏览器...
    if %NEED_NODE%==0 (
        start http://localhost:5173/
    ) else (
        echo [提示] 前端未启动，可手动访问后端接口文档：http://localhost:8000/docs
        start http://localhost:8000/docs
    )
) else (
    echo [警告] 后端未在预期时间内就绪，请查看“后端”窗口的日志排错。
)
echo.
echo 启动完成。后端/前端窗口已打开，关闭对应窗口即可停止服务。
echo 按任意键退出本启动器（服务窗口不受影响）...
pause >nul
endlocal
