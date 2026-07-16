Option Explicit
Dim shell, fso, projectDir, pythonw, launcher, command, quote, result
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
quote = Chr(34)
projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = projectDir
launcher = projectDir & "\BioDYM_Launcher.py"
If Not fso.FileExists(launcher) Then
    MsgBox "BioDYM_Launcher.py is missing. Extract all launcher files into the main BioDYM folder.", 16, "BioDYM Launcher"
    WScript.Quit 1
End If
pythonw = projectDir & "\.venv\Scripts\pythonw.exe"
If fso.FileExists(pythonw) Then
    command = quote & pythonw & quote & " " & quote & launcher & quote
Else
    result = shell.Run("cmd /c where uv >nul 2>&1", 0, True)
    If result = 0 Then
        command = "cmd /c uv run pythonw " & quote & launcher & quote
    Else
        result = shell.Run("cmd /c where conda >nul 2>&1", 0, True)
        If result = 0 Then
            command = "cmd /c conda run -n biodym_env pythonw " & quote & launcher & quote
        Else
            MsgBox "No BioDYM environment was found." & vbCrLf & vbCrLf & _
                "Install BioDYM with 'uv sync' or create the biodym_env Conda environment, then try again.", 16, "BioDYM Launcher"
            WScript.Quit 1
        End If
    End If
End If
On Error Resume Next
result = shell.Run(command, 0, False)
If Err.Number <> 0 Then
    MsgBox "BioDYM could not be started." & vbCrLf & vbCrLf & Err.Description & _
        vbCrLf & vbCrLf & "If this folder was moved, run 'uv sync' again.", 16, "BioDYM Launcher"
    WScript.Quit 1
End If
On Error GoTo 0
