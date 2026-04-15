@echo off
title Control Depositos - Reiniciar Servidor
cd /d "%~dp0backend"
call "%APPDATA%\npm\pm2.cmd" restart control-depositos 2>nul
if errorlevel 1 (
    call "%APPDATA%\npm\pm2.cmd" start server.js --name "control-depositos"
    call "%APPDATA%\npm\pm2.cmd" save
)
echo.
echo  Servidor reiniciado correctamente.
echo  Accede desde cualquier equipo de la red usando la IP del servidor.
echo.
call "%APPDATA%\npm\pm2.cmd" list
pause
