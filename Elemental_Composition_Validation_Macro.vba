' Enhanced BioDYM Validation Macro with Elemental Composition Support
' This macro handles different field types including Yes/No fields and checkboxes

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
    Dim fieldType As String
    
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
    
    ' Determine field type and apply appropriate validation
    fieldType = DetermineFieldType(columnName)
    
    Select Case fieldType
        Case "YesNo"
            ' Apply Yes/No dropdown validation
            Call ApplyYesNoValidation(ws, col, dataStartRow, dataEndRow, title, body)
        Case "Checkbox"
            ' Apply checkbox validation (True/False)
            Call ApplyCheckboxValidation(ws, col, dataStartRow, dataEndRow, title, body)
        Case "ElementalComposition"
            ' Apply elemental composition validation
            Call ApplyElementalCompositionValidation(ws, col, dataStartRow, dataEndRow, title, body)
        Case "Codelist"
            ' Apply codelist validation
            codelistFormula = GetStructuredCodelistFormula(columnName)
            Call ApplyCodelistValidation(ws, col, dataStartRow, dataEndRow, title, body, codelistFormula)
        Case Else
            ' Apply input-only validation
            Call ApplyInputOnlyValidation(ws, col, dataStartRow, dataEndRow, title, body)
    End Select
End Sub

' Function to determine field type
Function DetermineFieldType(columnName As String) As String
    ' Yes/No fields
    If InStr(columnName, "?") > 0 And (InStr(columnName, "WC") > 0 Or InStr(columnName, "DM") > 0 Or InStr(columnName, "CC") > 0) Then
        DetermineFieldType = "ElementalComposition"
    ElseIf InStr(columnName, "?") > 0 Then
        DetermineFieldType = "YesNo"
    ' Checkbox fields
    ElseIf InStr(columnName, "Checkbox") > 0 Or InStr(columnName, "Flag") > 0 Then
        DetermineFieldType = "Checkbox"
    ' Configuration fields with codelists
    ElseIf InStr(columnName, "Process_Logic") > 0 Or InStr(columnName, "Configuration") > 0 Or InStr(columnName, "Complete") > 0 Then
        DetermineFieldType = "Codelist"
    Else
        DetermineFieldType = "InputOnly"
    End If
End Function

' Apply Yes/No validation
Sub ApplyYesNoValidation(ws As Worksheet, col As Long, dataStartRow As Long, dataEndRow As Long, title As String, body As String)
    Dim cell As Range
    
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
        On Error Resume Next
        With cell.Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:="Yes,No"
            .InputTitle = title
            .InputMessage = body
            .ShowInput = True
            .ShowError = False
        End With
        On Error GoTo 0
    Next cell
End Sub

' Apply checkbox validation (True/False)
Sub ApplyCheckboxValidation(ws As Worksheet, col As Long, dataStartRow As Long, dataEndRow As Long, title As String, body As String)
    Dim cell As Range
    
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
        On Error Resume Next
        With cell.Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:="TRUE,FALSE"
            .InputTitle = title
            .InputMessage = body
            .ShowInput = True
            .ShowError = False
        End With
        On Error GoTo 0
    Next cell
End Sub

' Apply elemental composition validation (combined approach)
Sub ApplyElementalCompositionValidation(ws As Worksheet, col As Long, dataStartRow As Long, dataEndRow As Long, title As String, body As String)
    Dim cell As Range
    
    ' Option 1: Use Yes/No dropdown
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
        On Error Resume Next
        With cell.Validation
            .Delete
            .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:="Yes,No"
            .InputTitle = title
            .InputMessage = body
            .ShowInput = True
            .ShowError = False
        End With
        On Error GoTo 0
    Next cell
    
    ' Option 2: You could also use checkboxes here
    ' Uncomment the lines below if you prefer checkboxes
    'For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
    '    On Error Resume Next
    '    With cell.Validation
    '        .Delete
    '        .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:="TRUE,FALSE"
    '        .InputTitle = title
    '        .InputMessage = body
    '        .ShowInput = True
    '        .ShowError = False
    '    End With
    '    On Error GoTo 0
    'Next cell
End Sub

' Apply codelist validation
Sub ApplyCodelistValidation(ws As Worksheet, col As Long, dataStartRow As Long, dataEndRow As Long, title As String, body As String, codelistFormula As String)
    Dim cell As Range
    
    If codelistFormula <> "" Then
        For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
            On Error Resume Next
            With cell.Validation
                .Delete
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:=codelistFormula
                .InputTitle = title
                .InputMessage = body
                .ShowInput = True
                .ShowError = False
            End With
            On Error GoTo 0
        Next cell
    Else
        ' Fallback to input-only if no codelist found
        Call ApplyInputOnlyValidation(ws, col, dataStartRow, dataEndRow, title, body)
    End If
End Sub

' Apply input-only validation
Sub ApplyInputOnlyValidation(ws As Worksheet, col As Long, dataStartRow As Long, dataEndRow As Long, title As String, body As String)
    Dim cell As Range
    
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
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

' Function to get structured codelist formula for a column
Function GetStructuredCodelistFormula(columnName As String) As String
    Dim codelistSheet As Worksheet
    Dim codelistTable As ListObject
    Dim codelistRange As Range
    Dim formula As String
    Dim valueColumn As Long
    
    ' Check if codelist sheet exists
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        GetStructuredCodelistFormula = ""
        Exit Function
    End If
    
    ' Look for table with matching name (with CL_ prefix)
    For Each codelistTable In codelistSheet.ListObjects
        If codelistTable.Name = "CL_" & columnName Then
            ' Found matching codelist table
            ' Find the value column (Process_Logic, Complete?, etc.)
            valueColumn = FindValueColumnInTable(codelistTable, columnName)
            If valueColumn > 0 Then
                Set codelistRange = codelistTable.DataBodyRange.Columns(valueColumn)
                formula = "=" & codelistSheet.Name & "!" & codelistRange.Address
                GetStructuredCodelistFormula = formula
                Exit Function
            End If
        End If
    Next codelistTable
    
    GetStructuredCodelistFormula = ""
End Function

' Function to find the value column in a structured table
Function FindValueColumnInTable(table As ListObject, columnName As String) As Long
    Dim col As Long
    Dim headerCell As Range
    
    ' Look for column that matches the columnName
    For col = 1 To table.ListColumns.Count
        Set headerCell = table.HeaderRowRange.Cells(1, col)
        If headerCell.Value = columnName Then
            FindValueColumnInTable = col
            Exit Function
        End If
    Next col
    
    ' If not found, look for common value column names
    For col = 1 To table.ListColumns.Count
        Set headerCell = table.HeaderRowRange.Cells(1, col)
        If InStr(UCase(headerCell.Value), "VALUE") > 0 Or _
           InStr(UCase(headerCell.Value), "NAME") > 0 Or _
           InStr(UCase(headerCell.Value), "OPTION") > 0 Then
            FindValueColumnInTable = col
            Exit Function
        End If
    Next col
    
    ' Default to second column (assuming ID is first)
    If table.ListColumns.Count >= 2 Then
        FindValueColumnInTable = 2
    Else
        FindValueColumnInTable = 0
    End If
End Function

' Function to create combined Yes/No codelist table
Sub CreateCombinedYesNoCodelist()
    Dim codelistSheet As Worksheet
    Dim codelistRange As Range
    
    ' Get or create codelist sheet
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        Set codelistSheet = ThisWorkbook.Worksheets.Add
        codelistSheet.Name = "Codelists"
    End If
    
    ' Find next available position
    Dim nextRow As Long
    nextRow = codelistSheet.Cells(codelistSheet.Rows.Count, 1).End(xlUp).Row + 2
    
    ' Create combined Yes/No table
    codelistSheet.Cells(nextRow, 1).Value = "ID"
    codelistSheet.Cells(nextRow, 2).Value = "YesNo"
    codelistSheet.Cells(nextRow, 3).Value = "Explanation"
    
    ' Add data rows
    codelistSheet.Cells(nextRow + 1, 1).Value = 1
    codelistSheet.Cells(nextRow + 1, 2).Value = "Yes"
    codelistSheet.Cells(nextRow + 1, 3).Value = "Element data available"
    
    codelistSheet.Cells(nextRow + 2, 1).Value = 2
    codelistSheet.Cells(nextRow + 2, 2).Value = "No"
    codelistSheet.Cells(nextRow + 2, 3).Value = "No element data"
    
    ' Convert to table
    Set codelistRange = codelistSheet.Range(codelistSheet.Cells(nextRow, 1), codelistSheet.Cells(nextRow + 2, 3))
    codelistSheet.ListObjects.Add(xlSrcRange, codelistRange, , xlYes).Name = "CL_YesNo"
    
    MsgBox "Combined Yes/No codelist table created successfully!", vbInformation
End Sub

' Function to create elemental composition codelist
Sub CreateElementalCompositionCodelist()
    Dim codelistSheet As Worksheet
    Dim codelistRange As Range
    
    ' Get or create codelist sheet
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        Set codelistSheet = ThisWorkbook.Worksheets.Add
        codelistSheet.Name = "Codelists"
    End If
    
    ' Find next available position
    Dim nextRow As Long
    nextRow = codelistSheet.Cells(codelistSheet.Rows.Count, 1).End(xlUp).Row + 2
    
    ' Create elemental composition table
    codelistSheet.Cells(nextRow, 1).Value = "ID"
    codelistSheet.Cells(nextRow, 2).Value = "ElementalComposition"
    codelistSheet.Cells(nextRow, 3).Value = "Explanation"
    
    ' Add data rows
    codelistSheet.Cells(nextRow + 1, 1).Value = 1
    codelistSheet.Cells(nextRow + 1, 2).Value = "Yes"
    codelistSheet.Cells(nextRow + 1, 3).Value = "Element composition data available"
    
    codelistSheet.Cells(nextRow + 2, 1).Value = 2
    codelistSheet.Cells(nextRow + 2, 2).Value = "No"
    codelistSheet.Cells(nextRow + 2, 3).Value = "No element composition data"
    
    ' Convert to table
    Set codelistRange = codelistSheet.Range(codelistSheet.Cells(nextRow, 1), codelistSheet.Cells(nextRow + 2, 3))
    codelistSheet.ListObjects.Add(xlSrcRange, codelistRange, , xlYes).Name = "CL_ElementalComposition"
    
    MsgBox "Elemental composition codelist table created successfully!", vbInformation
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
