@echo off
REM Script para registrar la tarea de arranque del sistema
REM Ejecutar como Administrador para que funcione

echo Registrando tarea de arranque del servidor...

REM Eliminar tarea anterior si existe
schtasks /delete /tn "ControlDepositos-SistemaArranque" /f 2>nul

REM Crear tarea para arrancar al iniciar Windows
schtasks /create ^
    /tn "ControlDepositos-SistemaArranque" ^
    /tr "C:\Users\Usuario\Documents\GitHub\Control-Depositos\INICIO-SERVIDOR-SISTEMA.bat" ^
    /sc onstart ^
    /rl highest ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo ✓ Tarea registrada exitosamente.
    echo   El servidor arrancara automaticamente al iniciar Windows.
    echo.
    schtasks /query /tn "ControlDepositos-SistemaArranque" /fo list
) else (
    echo.
    echo ✗ Error al registrar la tarea. Intenta ejecutar este archivo como Administrador.
    echo.
)

pause
