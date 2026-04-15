@echo off
REM Script para arrancar el servidor Control Depósitos al iniciar Windows
REM Este script se ejecuta automáticamente sin interfaz visible

setlocal enabledelayedexpansion

REM Directorio del servidor
set BACKEND_DIR=C:\Users\Usuario\Documents\GitHub\Control-Depósitos\backend
set LOG_FILE=%BACKEND_DIR%\server.log

REM Navegar al directorio del backend
cd /d "%BACKEND_DIR%"

REM Terminar procesos Node anteriores si existen
taskkill /F /IM node.exe /T >nul 2>&1

REM Esperar un segundo para limpiar
timeout /t 1 /nobreak >nul 2>&1

REM Iniciar el servidor y redirigir output a archivo de log
start "" /B node server.js >> "%LOG_FILE%" 2>&1

REM Registrar hora de inicio
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)
echo [%mydate% %mytime%] Servidor iniciado >> "%LOG_FILE%"

exit /b 0
