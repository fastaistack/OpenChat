@chcp 65001 > nul
@echo off
setlocal enabledelayedexpansion

@REM taskkill /IM ollama_llama_server.exe /F /T 2>nul

:: ---------------------杀掉ollama_llama_server.exe进程----------------------------------
:kill_loop
taskkill /IM ollama_llama_server.exe /F /T >nul 2>&1
tasklist | findstr /i "ollama_llama_server.exe" >nul && (
    timeout /t 1 >nul
    goto :kill_loop
)

:: --------------------等待openchat.exe退出----------------------------------
timeout /t 15

:: 检查进程是否存在，存在这kill掉
taskkill /f /im openchat.exe

:: --------------------文件迁移----------------------------------
set "source=%~dp0download"
set "target=%~dp0"

echo "%source%"
echo "%target%"

if not exist "%source%" (
    echo 错误：未找到download目录
    pause
    exit /b 1
)

xcopy "%source%" "%target%" /e /y /i
if %errorlevel% neq 0 (
    echo 文件复制失败
    pause
    exit /b 1
)

rd /s /q "%source%"
if exist "%source%" (
    echo 错误：目录删除失败
    pause
    exit /b 1
)

echo 文件移动并清理完成

:: ---------------------------------数据库重命名----------------------------------
:: 自动定位用户文档目录
set "DB_DIR=%USERPROFILE%\.openchat"
set "SOURCE=%DB_DIR%\openchat.db"
set "TARGET=%DB_DIR%\openchat_old.db"

echo "%SOURCE%"

:: 验证源文件存在性
if not exist "%SOURCE%" (
    echo 错误：未找到 openchat.db 文件
    exit /b 1
)

:: 创建时间戳备份机制
set "TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%-%time:~0,2%%time:~3,2%"
if exist "%TARGET%" (
    echo 发现旧备份文件，创建时间戳备份...
    ren "%TARGET%" "openchat_old_%TIMESTAMP%.db" || (
        echo 备份失败！请手动检查文件权限
        exit /b 2
    )
)

:: 执行重命名操作
ren "%SOURCE%" "openchat_old.db" >nul 2>&1

:: 验证操作结果
if exist "%TARGET%" (
    echo 成功重命名路径：
    echo [%TARGET%]
) else (
    echo 重命名失败，错误码：%errorlevel%
    exit /b 3
)

@REM :: -----------------------------启动项目-----------------------------
@REM start "" "openchat.exe"