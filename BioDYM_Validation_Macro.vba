' BioDYM Validation Instructions Macro
' This macro reads validation instructions from the 7_1_Comments_Validation sheet
' and applies them to all data sheets in the workbook
' 
' Author: AI Assistant
' Date: 2024
' Version: 1.0
'
' Features:
' - Reads validation instructions from validation sheet
' - Applies data validation and comments to all sheets
' - Supports updating when validation sheet changes
' - Handles different field types (Auto-generated, Manual Input, Configuration)
' - Provides troubleshooting tips and examples

Option Explicit

' Main subroutine to execute the validation plan
Sub ApplyValidationInstructions()
    Dim validationSheet As Worksheet
    Dim validationData As Range
    Dim currentSheet As Worksheet
    Dim validationRow As Range
    Dim targetSheet As String
    Dim targetColumn As String
    Dim validationTitle As String
    Dim validationBody As String
    Dim validationPurpose As String
    Dim validationAction As String
    Dim validationNote As String
    Dim combinedNote As String
    Dim fieldType As String
    Dim i As Long
    
    ' Error handling
    On Error GoTo ErrorHandler
    
    ' Initialize
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    ' Get validation sheet
    Set validationSheet = ThisWorkbook.Worksheets("7_1_Comments_Validation")
    
    ' Get validation data range (assuming data starts from row 4, with headers in row 3)
    Set validationData = validationSheet.Range("A4:J" & validationSheet.Cells(validationSheet.Rows.Count, "A").End(xlUp).Row)
    
    ' Process each validation instruction
    For Each validationRow In validationData.Rows
        ' Skip empty rows
        If validationRow.Cells(1, 2).Value = "" Then GoTo NextRow
        
        ' Extract validation data
        targetSheet = validationRow.Cells(1, 2).Value  ' Name_sheet
        targetColumn = validationRow.Cells(1, 3).Value  ' Name_Column
        validationTitle = validationRow.Cells(1, 4).Value  ' Titel:
        validationBody = validationRow.Cells(1, 5).Value  ' Body:
        validationPurpose = validationRow.Cells(1, 7).Value  ' Purpose:
        validationAction = validationRow.Cells(1, 8).Value  ' Action:
        validationNote = validationRow.Cells(1, 9).Value  ' Note:
        
        ' Skip if essential data is missing
        If targetSheet = "" Or targetColumn = "" Or validationTitle = "" Then GoTo NextRow
        
        ' Determine field type for appropriate handling
        fieldType = DetermineFieldType(targetColumn)
        
        ' Create combined note
        combinedNote = CreateCombinedNote(validationPurpose, validationAction, validationNote)
        
        ' Apply validation to target sheet
        Call ApplyValidationToSheet(targetSheet, targetColumn, validationTitle, validationBody, combinedNote, fieldType)
        
NextRow:
    Next validationRow
    
    ' Cleanup
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    
    MsgBox "Validation instructions applied successfully to all sheets!", vbInformation, "BioDYM Validation Complete"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    MsgBox "Error occurred: " & Err.Description & " (Line: " & Erl & ")", vbCritical, "BioDYM Validation Error"
End Sub

' Determine field type based on column name
Function DetermineFieldType(columnName As String) As String
    Dim fieldType As String
    
    ' Auto-generated fields
    If InStr(columnName, "ID") > 0 And InStr(columnName, "Process") = 0 And InStr(columnName, "Flow") = 0 Then
        fieldType = "Auto_Generated"
    ElseIf InStr(columnName, "Process_ID") > 0 Or InStr(columnName, "Flow_ID") > 0 Or InStr(columnName, "TC_ID") > 0 Then
        fieldType = "Auto_Generated"
    ' Configuration fields
    ElseIf InStr(columnName, "Complete") > 0 Or InStr(columnName, "Logic") > 0 Or InStr(columnName, "Configuration") > 0 Then
        fieldType = "Configuration"
    ' Percentage fields
    ElseIf InStr(columnName, "[%]") > 0 Or InStr(columnName, "WC") > 0 Or InStr(columnName, "DM") > 0 Or InStr(columnName, "CC") > 0 Then
        fieldType = "Percentage"
    ' Name fields
    ElseIf InStr(columnName, "Name") > 0 Or InStr(columnName, "Description") > 0 Then
        fieldType = "Name"
    ' Value fields
    ElseIf InStr(columnName, "Value") > 0 Or InStr(columnName, "Material") > 0 Or InStr(columnName, "Year") > 0 Then
        fieldType = "Value"
    ' Source fields
    ElseIf InStr(columnName, "Source") > 0 Or InStr(columnName, "Author") > 0 Then
        fieldType = "Source"
    Else
        fieldType = "General"
    End If
    
    DetermineFieldType = fieldType
End Function

' Create combined note from purpose, action, and note
Function CreateCombinedNote(purpose As String, action As String, note As String) As String
    Dim combined As String
    
    combined = ""
    
    If purpose <> "" Then
        combined = combined & "PURPOSE: " & purpose & vbCrLf
    End If
    
    If action <> "" Then
        combined = combined & "ACTION: " & action & vbCrLf
    End If
    
    If note <> "" Then
        combined = combined & "NOTE: " & note
    End If
    
    CreateCombinedNote = Trim(combined)
End Function

' Apply validation to specific sheet and column
Sub ApplyValidationToSheet(sheetName As String, columnName As String, title As String, body As String, note As String, fieldType As String)
    Dim targetWorksheet As Worksheet
    Dim targetColumnRange As Range
    Dim headerRow As Long
    Dim dataStartRow As Long
    Dim dataEndRow As Long
    Dim validationFormula As String
    Dim errorMessage As String
    Dim inputMessage As String
    
    ' Check if target sheet exists
    If Not SheetExists(sheetName) Then
        Debug.Print "Sheet '" & sheetName & "' not found. Skipping..."
        Exit Sub
    End If
    
    Set targetWorksheet = ThisWorkbook.Worksheets(sheetName)
    
    ' Find the column
    Set targetColumnRange = FindColumnInSheet(targetWorksheet, columnName)
    If targetColumnRange Is Nothing Then
        Debug.Print "Column '" & columnName & "' not found in sheet '" & sheetName & "'. Skipping..."
        Exit Sub
    End If
    
    ' Determine header row (usually row 1 or 2)
    headerRow = 1
    If targetWorksheet.Cells(2, targetColumnRange.Column).Value <> "" Then
        headerRow = 2
    End If
    
    ' Determine data range
    dataStartRow = headerRow + 1
    dataEndRow = targetWorksheet.Cells(targetWorksheet.Rows.Count, targetColumnRange.Column).End(xlUp).Row
    
    ' Skip if no data rows
    If dataEndRow <= dataStartRow Then Exit Sub
    
    ' Set data range
    Set targetColumnRange = targetWorksheet.Range(targetWorksheet.Cells(dataStartRow, targetColumnRange.Column), targetWorksheet.Cells(dataEndRow, targetColumnRange.Column))
    
    ' Create validation based on field type
    Select Case fieldType
        Case "Auto_Generated"
            ' For auto-generated fields, only add comment, no data validation
            Call AddCommentToRange(targetColumnRange, title, note)
            
        Case "Configuration"
            ' For configuration fields, add dropdown validation
            Call AddDropdownValidation(targetColumnRange, title, body, note, columnName)
            
        Case "Percentage"
            ' For percentage fields, add percentage validation
            Call AddPercentageValidation(targetColumnRange, title, body, note)
            
        Case "Name"
            ' For name fields, add text validation
            Call AddTextValidation(targetColumnRange, title, body, note)
            
        Case "Value"
            ' For value fields, add number validation
            Call AddNumberValidation(targetColumnRange, title, body, note, columnName)
            
        Case "Source"
            ' For source fields, add text validation
            Call AddTextValidation(targetColumnRange, title, body, note)
            
        Case Else
            ' For general fields, add basic validation
            Call AddGeneralValidation(targetColumnRange, title, body, note)
    End Select
    
    Debug.Print "Applied validation to " & sheetName & "." & columnName & " (" & fieldType & ")"
End Sub

' Check if sheet exists
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

' Find column in sheet
Function FindColumnInSheet(ws As Worksheet, columnName As String) As Range
    Dim headerRow As Long
    Dim col As Long
    
    ' Check row 1 first
    Set FindColumnInSheet = ws.Rows(1).Find(columnName, LookIn:=xlValues, LookAt:=xlWhole)
    If Not FindColumnInSheet Is Nothing Then Exit Function
    
    ' Check row 2 if row 1 didn't work
    Set FindColumnInSheet = ws.Rows(2).Find(columnName, LookIn:=xlValues, LookAt:=xlWhole)
End Function

' Add comment to range
Sub AddCommentToRange(rng As Range, title As String, note As String)
    Dim cell As Range
    Dim commentText As String
    
    commentText = title & vbCrLf & vbCrLf & note
    
    For Each cell In rng
        If cell.Comment Is Nothing Then
            cell.AddComment commentText
            cell.Comment.Visible = False
        End If
    Next cell
End Sub

' Add dropdown validation
Sub AddDropdownValidation(rng As Range, title As String, body As String, note As String, columnName As String)
    Dim validationFormula As String
    Dim inputMessage As String
    Dim errorMessage As String
    
    ' Create validation formula based on column type
    Select Case columnName
        Case "Complete?"
            validationFormula = "Yes,No"
        Case "Process_Logic"
            validationFormula = "Input,Output,Pass-through,Transformation"
        Case "TC_Configuration"
            validationFormula = "Static,Dynamic,None"
        Case "Stock_Configuration"
            validationFormula = "Stock,None"
        Case "Type_Source"
            validationFormula = "Literature,Measurement,Estimate,Database,Expert Knowledge"
        Case "WC?", "DM?", "CC?"
            validationFormula = "Yes,No"
        Case Else
            validationFormula = "Yes,No"  ' Default dropdown
    End Select
    
    inputMessage = title & vbCrLf & vbCrLf & body
    errorMessage = "Please select a valid option from the dropdown list."
    
    ' Apply validation
    With rng.Validation
        .Delete
        .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:=validationFormula
        .InputTitle = title
        .InputMessage = inputMessage
        .ErrorTitle = "Invalid Input"
        .ErrorMessage = errorMessage
        .ShowInput = True
        .ShowError = True
    End With
    
    ' Add comment
    Call AddCommentToRange(rng, title, note)
End Sub

' Add percentage validation
Sub AddPercentageValidation(rng As Range, title As String, body As String, note As String)
    Dim inputMessage As String
    Dim errorMessage As String
    
    inputMessage = title & vbCrLf & vbCrLf & body
    errorMessage = "Please enter a percentage value between 0 and 100."
    
    ' Apply validation
    With rng.Validation
        .Delete
        .Add Type:=xlValidateDecimal, AlertStyle:=xlValidAlertStop, _
             Operator:=xlBetween, Formula1:="0", Formula2:="100"
        .InputTitle = title
        .InputMessage = inputMessage
        .ErrorTitle = "Invalid Percentage"
        .ErrorMessage = errorMessage
        .ShowInput = True
        .ShowError = True
    End With
    
    ' Add comment
    Call AddCommentToRange(rng, title, note)
End Sub

' Add text validation
Sub AddTextValidation(rng As Range, title As String, body As String, note As String)
    Dim inputMessage As String
    Dim errorMessage As String
    
    inputMessage = title & vbCrLf & vbCrLf & body
    errorMessage = "Please enter a valid text value."
    
    ' Apply validation
    With rng.Validation
        .Delete
        .Add Type:=xlValidateTextLength, AlertStyle:=xlValidAlertStop, _
             Operator:=xlGreaterEqual, Formula1:="1"
        .InputTitle = title
        .InputMessage = inputMessage
        .ErrorTitle = "Invalid Text"
        .ErrorMessage = errorMessage
        .ShowInput = True
        .ShowError = True
    End With
    
    ' Add comment
    Call AddCommentToRange(rng, title, note)
End Sub

' Add number validation
Sub AddNumberValidation(rng As Range, title As String, body As String, note As String, columnName As String)
    Dim inputMessage As String
    Dim errorMessage As String
    
    inputMessage = title & vbCrLf & vbCrLf & body
    errorMessage = "Please enter a valid number."
    
    ' Apply validation based on column type
    With rng.Validation
        .Delete
        If InStr(columnName, "Year") > 0 Then
            ' Year validation
            .Add Type:=xlValidateWholeNumber, AlertStyle:=xlValidAlertStop, _
                 Operator:=xlBetween, Formula1:="2000", Formula2:="2100"
            errorMessage = "Please enter a valid year between 2000 and 2100."
        ElseIf InStr(columnName, "Value") > 0 Then
            ' Value validation (positive numbers)
            .Add Type:=xlValidateDecimal, AlertStyle:=xlValidAlertStop, _
                 Operator:=xlGreaterEqual, Formula1:="0"
            errorMessage = "Please enter a positive number."
        Else
            ' General number validation
            .Add Type:=xlValidateDecimal, AlertStyle:=xlValidAlertStop
        End If
        
        .InputTitle = title
        .InputMessage = inputMessage
        .ErrorTitle = "Invalid Number"
        .ErrorMessage = errorMessage
        .ShowInput = True
        .ShowError = True
    End With
    
    ' Add comment
    Call AddCommentToRange(rng, title, note)
End Sub

' Add general validation
Sub AddGeneralValidation(rng As Range, title As String, body As String, note As String)
    Dim inputMessage As String
    
    inputMessage = title & vbCrLf & vbCrLf & body
    
    ' Add comment only for general fields
    Call AddCommentToRange(rng, title, note)
End Sub

' Utility subroutine to clear all validation (for testing/updating)
Sub ClearAllValidation()
    Dim ws As Worksheet
    Dim rng As Range
    
    Application.ScreenUpdating = False
    
    For Each ws In ThisWorkbook.Worksheets
        If ws.Name <> "7_1_Comments_Validation" Then  ' Skip validation sheet
            For Each rng In ws.UsedRange
                If Not rng.Validation Is Nothing Then
                    rng.Validation.Delete
                End If
                If Not rng.Comment Is Nothing Then
                    rng.Comment.Delete
                End If
            Next rng
        End If
    Next ws
    
    Application.ScreenUpdating = True
    MsgBox "All validation cleared from data sheets!", vbInformation, "BioDYM Validation Cleared"
End Sub

' Utility subroutine to update validation (clear and reapply)
Sub UpdateValidationInstructions()
    Call ClearAllValidation
    Call ApplyValidationInstructions
End Sub

' Utility subroutine to show validation status
Sub ShowValidationStatus()
    Dim ws As Worksheet
    Dim rng As Range
    Dim validationCount As Long
    Dim commentCount As Long
    Dim statusMessage As String
    
    validationCount = 0
    commentCount = 0
    
    For Each ws In ThisWorkbook.Worksheets
        If ws.Name <> "7_1_Comments_Validation" Then
            For Each rng In ws.UsedRange
                If Not rng.Validation Is Nothing Then
                    validationCount = validationCount + 1
                End If
                If Not rng.Comment Is Nothing Then
                    commentCount = commentCount + 1
                End If
            Next rng
        End If
    Next ws
    
    statusMessage = "BioDYM Validation Status:" & vbCrLf & vbCrLf & _
                   "Data Validations Applied: " & validationCount & vbCrLf & _
                   "Comments Added: " & commentCount & vbCrLf & vbCrLf & _
                   "Sheets Processed: " & (ThisWorkbook.Worksheets.Count - 1)
    
    MsgBox statusMessage, vbInformation, "BioDYM Validation Status"
End Sub
