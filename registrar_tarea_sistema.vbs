Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Ruta del script batch
strBatchPath = "C:\Users\Usuario\Documents\GitHub\Control-Depósitos\INICIO-SERVIDOR-SISTEMA.bat"

' Verificar que el archivo existe
If Not objFSO.FileExists(strBatchPath) Then
    WScript.Echo "Error: No se encontró " & strBatchPath
    WScript.Quit 1
End If

' Crear la tarea usando schtasks
strCommand = "schtasks /create /tn ControlDepositos-SistemaArranque /tr """ & strBatchPath & """ /sc onstart /rl highest /f"
objShell.Run strCommand, 0, True

' Verificar resultado
strVerify = "schtasks /query /tn ControlDepositos-SistemaArranque /fo list"
Set objExec = objShell.Exec(strVerify)
strOutput = objExec.StdOut.ReadAll()

If InStr(strOutput, "ControlDepositos-SistemaArranque") > 0 Then
    WScript.Echo "✓ Tarea registrada exitosamente"
    WScript.Echo "La tarea arrancará el servidor automáticamente al iniciar Windows."
Else
    WScript.Echo "Error al registrar la tarea"
End If
