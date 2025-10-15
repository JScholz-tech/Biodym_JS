' Enhanced BioDYM Validation Macro with Structured Codelist Support
' This macro reads validation instructions from the 7_1_Comments_Validation sheet
' and applies them as comments and validation messages to the data sheets
' It supports structured codelists with ID, Value, and Explanation columns

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
    
    ' Check if there's a structured codelist for this column
    codelistFormula = GetStructuredCodelistFormula(columnName)
    
    ' Apply validation messages to data cells only
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
        ' Add validation message
        On Error Resume Next
        With cell.Validation
            .Delete
            
            ' Apply appropriate validation based on column type
            If codelistFormula <> "" Then
                ' Use structured codelist validation
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

' Function to create structured codelist table
Sub CreateStructuredCodelistTable(tableName As String, values As String, explanations As String)
    Dim codelistSheet As Worksheet
    Dim codelistRange As Range
    Dim valueArray As Variant
    Dim explanationArray As Variant
    Dim i As Long
    
    ' Get or create codelist sheet
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        Set codelistSheet = ThisWorkbook.Worksheets.Add
        codelistSheet.Name = "Codelists"
    End If
    
    ' Split values and explanations
    valueArray = Split(values, ",")
    explanationArray = Split(explanations, ",")
    
    ' Find next available position
    Dim nextRow As Long
    nextRow = codelistSheet.Cells(codelistSheet.Rows.Count, 1).End(xlUp).Row + 2
    
    ' Create table headers
    codelistSheet.Cells(nextRow, 1).Value = "ID"
    codelistSheet.Cells(nextRow, 2).Value = tableName
    codelistSheet.Cells(nextRow, 3).Value = "Explanation"
    
    ' Add data rows
    For i = 0 To UBound(valueArray)
        codelistSheet.Cells(nextRow + 1 + i, 1).Value = i + 1  ' ID
        codelistSheet.Cells(nextRow + 1 + i, 2).Value = Trim(valueArray(i))  ' Value
        If i <= UBound(explanationArray) Then
            codelistSheet.Cells(nextRow + 1 + i, 3).Value = Trim(explanationArray(i))  ' Explanation
        End If
    Next i
    
    ' Convert to table
    Set codelistRange = codelistSheet.Range(codelistSheet.Cells(nextRow, 1), codelistSheet.Cells(nextRow + 1 + UBound(valueArray), 3))
    codelistSheet.ListObjects.Add(xlSrcRange, codelistRange, , xlYes).Name = tableName
    
    MsgBox "Structured codelist table '" & tableName & "' created successfully!", vbInformation
End Sub

' Function to show codelist table structure
Sub ShowCodelistStructure()
    Dim codelistSheet As Worksheet
    Dim table As ListObject
    Dim msg As String
    
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        msg = "No Codelists sheet found. Create one with the following structure:" & vbCrLf & vbCrLf & _
              "Table: CL_Process_Logic" & vbCrLf & _
              "ID | Process_Logic | Explanation" & vbCrLf & _
              "1  | Input        | Receives material flows only" & vbCrLf & _
              "2  | Output       | Produces material flows only" & vbCrLf & _
              "3  | Pass-through | No material transformation" & vbCrLf & _
              "4  | Transformation | Converts materials"
    Else
        msg = "Codelists sheet found with " & codelistSheet.ListObjects.Count & " tables:" & vbCrLf & vbCrLf
        
        For Each table In codelistSheet.ListObjects
            msg = msg & "Table: " & table.Name & vbCrLf
            msg = msg & "Columns: "
            Dim col As Long
            For col = 1 To table.ListColumns.Count
                msg = msg & table.HeaderRowRange.Cells(1, col).Value
                If col < table.ListColumns.Count Then msg = msg & " | "
            Next col
            msg = msg & vbCrLf & vbCrLf
        Next table
    End If
    
    MsgBox msg, vbInformation, "Codelist Structure"
End Sub

' Function to create example codelist tables
Sub CreateExampleCodelists()
    ' Process_Logic table
    Call CreateStructuredCodelistTable("CL_Process_Logic", _
        "Input,Output,Pass-through,Transformation", _
        "Receives material flows only,Produces material flows only,No material transformation,Converts materials")
    
    ' Complete? table
    Call CreateStructuredCodelistTable("CL_Complete?", _
        "Yes,No", _
        "All data verified and complete,Data entry in progress")
    
    ' TC_Configuration table
    Call CreateStructuredCodelistTable("CL_TC_Configuration", _
        "Static,Dynamic,None", _
        "Constant transfer coefficients,Time-varying transfer coefficients,No transfer coefficients")
    
    ' Stock_Configuration table
    Call CreateStructuredCodelistTable("CL_Stock_Configuration", _
        "Stock,None", _
        "Maintains material stocks,No stock calculations")
    
    ' Type_Source table
    Call CreateStructuredCodelistTable("CL_Type_Source", _
        "Literature,Measurement,Estimate,Database,Expert Knowledge", _
        "Published literature,Measured data,Estimated values,Database records,Expert opinion")
    
    MsgBox "Example codelist tables created successfully!", vbInformation
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
