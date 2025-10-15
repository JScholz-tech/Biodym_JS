' BioDYM Validation Macro Installation Script
' This script helps install and configure the BioDYM validation macro
' Run this script once to set up the macro environment

Option Explicit

Sub InstallBioDYMValidationMacro()
    Dim response As VbMsgBoxResult
    Dim macroInstalled As Boolean
    
    ' Check if macro is already installed
    macroInstalled = CheckMacroInstallation()
    
    If macroInstalled Then
        response = MsgBox("BioDYM Validation Macro appears to be already installed." & vbCrLf & vbCrLf & _
                        "Do you want to reinstall it?", vbYesNo + vbQuestion, "Macro Installation")
        If response = vbNo Then Exit Sub
    End If
    
    ' Installation steps
    Call InstallMacroSteps
    
    ' Verify installation
    If CheckMacroInstallation() Then
        MsgBox "BioDYM Validation Macro installed successfully!" & vbCrLf & vbCrLf & _
               "You can now run 'ApplyValidationInstructions' to apply validation to your sheets.", _
               vbInformation, "Installation Complete"
    Else
        MsgBox "Installation may not have completed successfully. Please check the VBA Editor.", _
               vbExclamation, "Installation Warning"
    End If
End Sub

Function CheckMacroInstallation() As Boolean
    Dim vbProj As Object
    Dim vbComp As Object
    Dim macroFound As Boolean
    
    macroFound = False
    
    ' Check if the main macro function exists
    On Error Resume Next
    Application.Run "ApplyValidationInstructions"
    If Err.Number = 0 Then
        macroFound = True
    End If
    On Error GoTo 0
    
    CheckMacroInstallation = macroFound
End Function

Sub InstallMacroSteps()
    Dim steps As String
    
    steps = "BioDYM Validation Macro Installation Steps:" & vbCrLf & vbCrLf & _
            "1. Open VBA Editor (Alt + F11)" & vbCrLf & _
            "2. Right-click on your workbook name in Project Explorer" & vbCrLf & _
            "3. Select 'Insert' → 'Module'" & vbCrLf & _
            "4. Copy the macro code from 'BioDYM_Validation_Macro.vba'" & vbCrLf & _
            "5. Paste it into the new module" & vbCrLf & _
            "6. Save the workbook as .xlsm format" & vbCrLf & vbCrLf & _
            "Would you like to open the VBA Editor now?"
    
    If MsgBox(steps, vbYesNo + vbQuestion, "Installation Instructions") = vbYes Then
        Application.VBE.MainWindow.Visible = True
    End If
End Sub

Sub CreateMacroButtons()
    Dim ws As Worksheet
    Dim btnApply As Button
    Dim btnUpdate As Button
    Dim btnClear As Button
    Dim btnStatus As Button
    Dim btnRow As Long
    
    ' Get or create a macro control sheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("Macro Controls")
    On Error GoTo 0
    
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets.Add
        ws.Name = "Macro Controls"
    End If
    
    ' Clear existing buttons
    ws.Buttons.Delete
    
    ' Position buttons
    btnRow = 2
    
    ' Apply Validation Button
    Set btnApply = ws.Buttons.Add(10, btnRow * 20, 150, 20)
    btnApply.Caption = "Apply Validation Instructions"
    btnApply.OnAction = "ApplyValidationInstructions"
    
    ' Update Validation Button
    btnRow = btnRow + 1
    Set btnUpdate = ws.Buttons.Add(10, btnRow * 20, 150, 20)
    btnUpdate.Caption = "Update Validation Instructions"
    btnUpdate.OnAction = "UpdateValidationInstructions"
    
    ' Clear Validation Button
    btnRow = btnRow + 1
    Set btnClear = ws.Buttons.Add(10, btnRow * 20, 150, 20)
    btnClear.Caption = "Clear All Validation"
    btnClear.OnAction = "ClearAllValidation"
    
    ' Show Status Button
    btnRow = btnRow + 1
    Set btnStatus = ws.Buttons.Add(10, btnRow * 20, 150, 20)
    btnStatus.Caption = "Show Validation Status"
    btnStatus.OnAction = "ShowValidationStatus"
    
    ' Add instructions
    ws.Cells(1, 1).Value = "BioDYM Validation Macro Controls"
    ws.Cells(1, 1).Font.Bold = True
    ws.Cells(1, 1).Font.Size = 14
    
    ws.Cells(btnRow + 2, 1).Value = "Instructions:"
    ws.Cells(btnRow + 2, 1).Font.Bold = True
    
    ws.Cells(btnRow + 3, 1).Value = "1. Apply Validation Instructions - Applies validation to all sheets"
    ws.Cells(btnRow + 4, 1).Value = "2. Update Validation Instructions - Clears and reapplies validation"
    ws.Cells(btnRow + 5, 1).Value = "3. Clear All Validation - Removes all validation and comments"
    ws.Cells(btnRow + 6, 1).Value = "4. Show Validation Status - Displays current validation status"
    
    ' Format the sheet
    ws.Columns("A").AutoFit
    ws.Rows.AutoFit
    
    MsgBox "Macro control buttons created on 'Macro Controls' sheet!", vbInformation, "Buttons Created"
End Sub

Sub TestMacroInstallation()
    Dim testResult As String
    
    testResult = "BioDYM Validation Macro Test Results:" & vbCrLf & vbCrLf
    
    ' Test 1: Check if validation sheet exists
    If SheetExists("7_1_Comments_Validation") Then
        testResult = testResult & "✓ Validation sheet found" & vbCrLf
    Else
        testResult = testResult & "✗ Validation sheet not found" & vbCrLf
    End If
    
    ' Test 2: Check if main macro exists
    On Error Resume Next
    Application.Run "ApplyValidationInstructions"
    If Err.Number = 0 Then
        testResult = testResult & "✓ Main macro function found" & vbCrLf
    Else
        testResult = testResult & "✗ Main macro function not found" & vbCrLf
    End If
    On Error GoTo 0
    
    ' Test 3: Check if utility macros exist
    On Error Resume Next
    Application.Run "ClearAllValidation"
    If Err.Number = 0 Then
        testResult = testResult & "✓ Utility macros found" & vbCrLf
    Else
        testResult = testResult & "✗ Utility macros not found" & vbCrLf
    End If
    On Error GoTo 0
    
    ' Test 4: Check workbook format
    If ThisWorkbook.FileFormat = xlOpenXMLWorkbookMacroEnabled Then
        testResult = testResult & "✓ Workbook is macro-enabled (.xlsm)" & vbCrLf
    Else
        testResult = testResult & "✗ Workbook is not macro-enabled" & vbCrLf
    End If
    
    MsgBox testResult, vbInformation, "Macro Installation Test"
End Sub

Function SheetExists(sheetName As String) As Boolean
    Dim ws As Worksheet
    SheetExists = False
    For Each ws In ThisWorkbook.Worksheets
        If ws.Name = sheetName Then
            SheetExists = True
            Exit Function
        End If
    Next ws
End Function

Sub QuickStart()
    Dim response As VbMsgBoxResult
    
    response = MsgBox("BioDYM Validation Macro Quick Start" & vbCrLf & vbCrLf & _
                    "This will help you get started with the validation macro." & vbCrLf & vbCrLf & _
                    "Choose an option:", vbYesNoCancel + vbQuestion, "Quick Start")
    
    Select Case response
        Case vbYes
            Call InstallBioDYMValidationMacro
        Case vbNo
            Call TestMacroInstallation
        Case vbCancel
            Call CreateMacroButtons
    End Select
End Sub
