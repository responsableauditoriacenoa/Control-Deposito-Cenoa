@echo off
title Control Integral de Depositos - Servidor
chcp 65001 >nul

echo ==========================================
echo   Control Integral de Depositos
echo   Grupo Cenoa
echo ==========================================
echo.

:: Verificar Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js no esta instalado.
    echo  Descargalo en: https://nodejs.org
    pause
    exit /b 1
)

:: Matar proceso previo en el mismo puerto (si quedó colgado)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000 "') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Ir al directorio del backend
cd /d "%~dp0backend"

:: Abrir el navegador después de 2 segundos (en segundo plano)
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

:: Iniciar servidor (bloquea aquí, muestra los logs)
node server.js

echo.
echo ==========================================
echo  Servidor detenido.
echo ==========================================
pause
