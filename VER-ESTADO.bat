@echo off
title Control Depositos - Ver Estado
call "%APPDATA%\npm\pm2.cmd" list
echo.
echo  Para acceder al sistema abre el navegador en http://localhost:5000
echo.
pause
