' Enhanced BioDYM Validation Macro with Codelist Support
' This macro reads validation instructions from the 7_1_Comments_Validation sheet
' and applies them as comments and validation messages to the data sheets
' It also supports codelists stored in Excel tables

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
        Call ApplyValidationToColumn(targetSheet, targetColumn.Column, title, body, purpose, action, note, columnName)
        
NextRow:
    Next validationRow
    
    MsgBox "Validation instructions applied successfully!", vbInformation
End Sub

Sub ApplyValidationToColumn(ws As Worksheet, col As Long, title As String, body As String, purpose As String, action As String, note As String, columnName As String)
    Dim dataStartRow As Long
    Dim dataEndRow As Long
    Dim cell As Range
    Dim combinedNote As String
    Dim headerCell As Range
    Dim codelistFormula As String
    
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
    
    ' Check if there's a codelist for this column
    codelistFormula = GetCodelistFormula(columnName)
    
    ' Apply validation messages to data cells only
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
        ' Add validation message
        On Error Resume Next
        With cell.Validation
            .Delete
            
            ' Apply appropriate validation based on column type
            If codelistFormula <> "" Then
                ' Use codelist validation
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:=codelistFormula
            Else
                ' Use input-only validation
                .Add Type:=xlValidateInputOnly, AlertStyle:=xlValidAlertStop
            End If
            
            .InputTitle = title
            .InputMessage = body
            .ShowInput = True
            .ShowError = False
        End With
        On Error GoTo 0
    Next cell
End Sub

' Function to get codelist formula for a column
Function GetCodelistFormula(columnName As String) As String
    Dim codelistSheet As Worksheet
    Dim codelistTable As ListObject
    Dim codelistRange As Range
    Dim formula As String
    
    ' Check if codelist sheet exists
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        GetCodelistFormula = ""
        Exit Function
    End If
    
    ' Look for table with matching name
    For Each codelistTable In codelistSheet.ListObjects
        If codelistTable.Name = columnName Then
            ' Found matching codelist table
            Set codelistRange = codelistTable.DataBodyRange
            formula = "=" & codelistSheet.Name & "!" & codelistRange.Address
            GetCodelistFormula = formula
            Exit Function
        End If
    Next codelistTable
    
    ' If no table found, check for named ranges
    On Error Resume Next
    formula = "=" & columnName
    ThisWorkbook.Names(columnName).RefersTo
    If Err.Number = 0 Then
        GetCodelistFormula = formula
    Else
        GetCodelistFormula = ""
    End If
    On Error GoTo 0
End Function

' Function to create codelist table from existing data
Sub CreateCodelistTable(sheetName As String, columnName As String, tableName As String)
    Dim sourceSheet As Worksheet
    Dim sourceColumn As Range
    Dim codelistSheet As Worksheet
    Dim codelistRange As Range
    Dim uniqueValues As Collection
    Dim cell As Range
    Dim i As Long
    
    ' Get source sheet and column
    Set sourceSheet = ThisWorkbook.Worksheets(sheetName)
    Set sourceColumn = sourceSheet.Rows(1).Find(columnName, LookIn:=xlValues, LookAt:=xlWhole)
    
    If sourceColumn Is Nothing Then
        MsgBox "Column '" & columnName & "' not found in sheet '" & sheetName & "'", vbExclamation
        Exit Sub
    End If
    
    ' Get or create codelist sheet
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        Set codelistSheet = ThisWorkbook.Worksheets.Add
        codelistSheet.Name = "Codelists"
    End If
    
    ' Collect unique values from source column
    Set uniqueValues = New Collection
    For Each cell In sourceSheet.Range(sourceColumn, sourceSheet.Cells(sourceSheet.Rows.Count, sourceColumn.Column).End(xlUp))
        If cell.Value <> "" And cell.Row > 1 Then ' Skip header and empty cells
            On Error Resume Next
            uniqueValues.Add cell.Value, CStr(cell.Value)
            On Error GoTo 0
        End If
    Next cell
    
    ' Create codelist table
    Set codelistRange = codelistSheet.Range("A1")
    codelistRange.Value = tableName
    
    For i = 1 To uniqueValues.Count
        codelistSheet.Cells(i + 1, 1).Value = uniqueValues(i)
    Next i
    
    ' Convert to table
    Set codelistRange = codelistSheet.Range("A1:A" & (uniqueValues.Count + 1))
    codelistSheet.ListObjects.Add(xlSrcRange, codelistRange, , xlYes).Name = tableName
    
    MsgBox "Codelist table '" & tableName & "' created successfully!", vbInformation
End Sub

' Function to manually add codelist validation
Sub AddManualCodelistValidation(sheetName As String, columnName As String, codelistValues As String)
    Dim targetSheet As Worksheet
    Dim targetColumn As Range
    Dim dataStartRow As Long
    Dim dataEndRow As Long
    Dim cell As Range
    
    ' Get target sheet and column
    Set targetSheet = ThisWorkbook.Worksheets(sheetName)
    Set targetColumn = targetSheet.Rows(1).Find(columnName, LookIn:=xlValues, LookAt:=xlWhole)
    
    If targetColumn Is Nothing Then
        MsgBox "Column '" & columnName & "' not found in sheet '" & sheetName & "'", vbExclamation
        Exit Sub
    End If
    
    ' Find data range
    dataStartRow = 2
    dataEndRow = targetSheet.Cells(targetSheet.Rows.Count, targetColumn.Column).End(xlUp).Row
    
    ' Apply validation to data cells
    For Each cell In targetSheet.Range(targetSheet.Cells(dataStartRow, targetColumn.Column), targetSheet.Cells(dataEndRow, targetColumn.Column))
        On Error Resume Next
        With cell.Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:=codelistValues
            .ShowInput = True
            .ShowError = True
        End With
        On Error GoTo 0
    Next cell
    
    MsgBox "Manual codelist validation applied to " & sheetName & "." & columnName, vbInformation
End Sub

' Simple function to clear all validation
Sub ClearAllValidation()
    Dim ws As Worksheet
    Dim cell As Range
    
    For Each ws In ThisWorkbook.Worksheets
        If ws.Name <> "7_1_Comments_Validation" And ws.Name <> "Codelists" Then
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

' Utility function to show codelist management options
Sub ShowCodelistOptions()
    Dim response As VbMsgBoxResult
    
    response = MsgBox("Codelist Management Options:" & vbCrLf & vbCrLf & _
                    "1. Create codelist from existing data" & vbCrLf & _
                    "2. Add manual codelist validation" & vbCrLf & _
                    "3. View current codelists" & vbCrLf & vbCrLf & _
                    "Choose an option:", vbYesNoCancel + vbQuestion, "Codelist Management")
    
    Select Case response
        Case vbYes
            Call CreateCodelistFromData
        Case vbNo
            Call AddManualCodelist
        Case vbCancel
            Call ViewCodelists
    End Select
End Sub

Sub CreateCodelistFromData()
    Dim sheetName As String
    Dim columnName As String
    Dim tableName As String
    
    sheetName = InputBox("Enter sheet name:", "Create Codelist")
    If sheetName = "" Then Exit Sub
    
    columnName = InputBox("Enter column name:", "Create Codelist")
    If columnName = "" Then Exit Sub
    
    tableName = InputBox("Enter table name for codelist:", "Create Codelist")
    If tableName = "" Then Exit Sub
    
    Call CreateCodelistTable(sheetName, columnName, tableName)
End Sub

Sub AddManualCodelist()
    Dim sheetName As String
    Dim columnName As String
    Dim codelistValues As String
    
    sheetName = InputBox("Enter sheet name:", "Add Manual Codelist")
    If sheetName = "" Then Exit Sub
    
    columnName = InputBox("Enter column name:", "Add Manual Codelist")
    If columnName = "" Then Exit Sub
    
    codelistValues = InputBox("Enter codelist values (comma-separated):", "Add Manual Codelist")
    If codelistValues = "" Then Exit Sub
    
    Call AddManualCodelistValidation(sheetName, columnName, codelistValues)
End Sub

Sub ViewCodelists()
    Dim codelistSheet As Worksheet
    Dim msg As String
    
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        msg = "No codelist sheet found."
    Else
        msg = "Codelist sheet found with " & codelistSheet.ListObjects.Count & " tables."
    End If
    
    MsgBox msg, vbInformation, "Codelist Status"
End Sub
