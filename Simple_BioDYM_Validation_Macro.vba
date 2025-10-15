' Simple BioDYM Validation Macro
' This macro reads validation instructions from the 7_1_Comments_Validation sheet
' and applies them as comments and validation messages to the data sheets

Sub ApplyValidationInstructions()
    Dim validationSheet As Worksheet
    Dim validationData As Range
    Dim validationRow As Range
    Dim targetSheet As Worksheet
    Dim targetColumn As Range
    Dim targetCell As Range
    Dim i As Long
    
    ' Get validation sheet
    Set validationSheet = ThisWorkbook.Worksheets("7_1_Comments_Validation")
    
    ' Get validation data (starting from row 4, with headers in row 3)
    Set validationData = validationSheet.Range("A4:J" & validationSheet.Cells(validationSheet.Rows.Count, "A").End(xlUp).Row)
    
    ' Process each validation instruction
    For Each validationRow In validationData.Rows
        ' Skip empty rows
        If validationRow.Cells(1, 2).Value = "" Then GoTo NextRow
        
        ' Get target sheet and column
        Dim sheetName As String
        Dim columnName As String
        Dim title As String
        Dim body As String
        Dim purpose As String
        Dim action As String
        Dim note As String
        
        sheetName = validationRow.Cells(1, 2).Value  ' Name_sheet
        columnName = validationRow.Cells(1, 3).Value  ' Name_Column
        title = validationRow.Cells(1, 4).Value  ' Titel:
        body = validationRow.Cells(1, 5).Value  ' Body:
        purpose = validationRow.Cells(1, 7).Value  ' Purpose:
        action = validationRow.Cells(1, 8).Value  ' Action:
        note = validationRow.Cells(1, 9).Value  ' Note:
        
        ' Skip if essential data is missing
        If sheetName = "" Or columnName = "" Or title = "" Then GoTo NextRow
        
        ' Check if target sheet exists
        On Error Resume Next
        Set targetSheet = ThisWorkbook.Worksheets(sheetName)
        On Error GoTo 0
        
        If targetSheet Is Nothing Then GoTo NextRow
        
        ' Find the column in the target sheet
        Set targetColumn = Nothing
        On Error Resume Next
        Set targetColumn = targetSheet.Rows(1).Find(columnName, LookIn:=xlValues, LookAt:=xlWhole)
        On Error GoTo 0
        
        If targetColumn Is Nothing Then GoTo NextRow
        
        ' Apply validation to the column
        Call ApplyValidationToColumn(targetSheet, targetColumn.Column, title, body, purpose, action, note)
        
NextRow:
    Next validationRow
    
    MsgBox "Validation instructions applied successfully!", vbInformation
End Sub

Sub ApplyValidationToColumn(ws As Worksheet, col As Long, title As String, body As String, purpose As String, action As String, note As String)
    Dim dataStartRow As Long
    Dim dataEndRow As Long
    Dim cell As Range
    Dim combinedNote As String
    Dim headerCell As Range
    
    ' Find data range (skip header row)
    dataStartRow = 2
    dataEndRow = ws.Cells(ws.Rows.Count, col).End(xlUp).Row
    
    ' Skip if no data
    If dataEndRow < dataStartRow Then Exit Sub
    
    ' Create combined note
    combinedNote = title & vbCrLf & vbCrLf
    If purpose <> "" Then combinedNote = combinedNote & "Purpose: " & purpose & vbCrLf
    If action <> "" Then combinedNote = combinedNote & "Action: " & action & vbCrLf
    If note <> "" Then combinedNote = combinedNote & "Note: " & note
    
    ' Add comment ONLY to header cell (row 1)
    Set headerCell = ws.Cells(1, col)
    If headerCell.Comment Is Nothing Then
        headerCell.AddComment combinedNote
        headerCell.Comment.Visible = False
        ' Auto-size the comment
        Call AutoSizeComment(headerCell.Comment)
    End If
    
    ' Apply validation messages to data cells only
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
        ' Add validation message
        On Error Resume Next
        With cell.Validation
            .Delete
            .Add Type:=xlValidateInputOnly, AlertStyle:=xlValidAlertStop
            .InputTitle = title
            .InputMessage = body
            .ShowInput = True
            .ShowError = False
        End With
        On Error GoTo 0
    Next cell
End Sub

' Simple function to clear all validation
Sub ClearAllValidation()
    Dim ws As Worksheet
    Dim cell As Range
    
    For Each ws In ThisWorkbook.Worksheets
        If ws.Name <> "7_1_Comments_Validation" Then
            For Each cell In ws.UsedRange
                If Not cell.Validation Is Nothing Then
                    cell.Validation.Delete
                End If
                If Not cell.Comment Is Nothing Then
                    cell.Comment.Delete
                End If
            Next cell
        End If
    Next ws
    
    MsgBox "All validation cleared!", vbInformation
End Sub

' Simple function to update validation
Sub UpdateValidation()
    Call ClearAllValidation
    Call ApplyValidationInstructions
End Sub

' Function to automatically size comments
Sub AutoSizeComment(comment As Comment)
    Dim textLength As Long
    Dim lines As Long
    Dim maxWidth As Long
    Dim commentWidth As Long
    Dim commentHeight As Long
    
    ' Calculate text length and number of lines
    textLength = Len(comment.Text)
    lines = Len(comment.Text) - Len(Replace(comment.Text, vbCrLf, "")) + 1
    
    ' Set maximum width (in points)
    maxWidth = 300
    
    ' Calculate optimal width based on text length
    If textLength < 50 Then
        commentWidth = 150
    ElseIf textLength < 100 Then
        commentWidth = 200
    ElseIf textLength < 200 Then
        commentWidth = 250
    Else
        commentWidth = maxWidth
    End If
    
    ' Calculate height based on number of lines
    commentHeight = lines * 15 + 20  ' 15 points per line + 20 points padding
    
    ' Apply the size
    comment.Shape.Width = commentWidth
    comment.Shape.Height = commentHeight
End Sub
