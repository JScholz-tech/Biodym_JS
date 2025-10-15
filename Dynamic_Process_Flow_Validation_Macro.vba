' Enhanced BioDYM Validation Macro with Dynamic Process/Flow References
' This macro creates validation lists that reference actual Process and Flow names
' from the definition sheets, ensuring data consistency

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
    Dim validationFormula As String
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
    
    ' Determine field type and get appropriate validation formula
    fieldType = DetermineFieldType(columnName)
    validationFormula = GetValidationFormula(columnName, fieldType)
    
    ' Apply validation to data cells
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
        On Error Resume Next
        With cell.Validation
            .Delete
            
            If validationFormula <> "" Then
                ' Apply list validation
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:=validationFormula
            Else
                ' Apply input-only validation
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

' Function to determine field type
Function DetermineFieldType(columnName As String) As String
    ' Process name fields
    If InStr(columnName, "Process_Name") > 0 Or InStr(columnName, "Process") > 0 Then
        DetermineFieldType = "ProcessName"
    ' Flow name fields
    ElseIf InStr(columnName, "Flow_Name") > 0 Or InStr(columnName, "Flow") > 0 Then
        DetermineFieldType = "FlowName"
    ' Yes/No fields
    ElseIf InStr(columnName, "?") > 0 Then
        DetermineFieldType = "YesNo"
    ' Configuration fields
    ElseIf InStr(columnName, "Process_Logic") > 0 Or InStr(columnName, "Configuration") > 0 Or InStr(columnName, "Complete") > 0 Then
        DetermineFieldType = "Configuration"
    ' Source fields
    ElseIf InStr(columnName, "Source") > 0 Or InStr(columnName, "Author") > 0 Then
        DetermineFieldType = "Source"
    Else
        DetermineFieldType = "InputOnly"
    End If
End Function

' Function to get validation formula based on field type
Function GetValidationFormula(columnName As String, fieldType As String) As String
    Select Case fieldType
        Case "ProcessName"
            GetValidationFormula = GetProcessNameFormula()
        Case "FlowName"
            GetValidationFormula = GetFlowNameFormula()
        Case "YesNo"
            GetValidationFormula = GetYesNoFormula()
        Case "Configuration"
            GetValidationFormula = GetConfigurationFormula(columnName)
        Case "Source"
            GetValidationFormula = GetSourceFormula()
        Case Else
            GetValidationFormula = ""
    End Select
End Function

' Function to get Process Name validation formula
Function GetProcessNameFormula() As String
    Dim processSheet As Worksheet
    Dim processRange As Range
    Dim formula As String
    
    ' Look for process definition sheet
    On Error Resume Next
    Set processSheet = ThisWorkbook.Worksheets("2_1_Definition_Processes")
    On Error GoTo 0
    
    If processSheet Is Nothing Then
        GetProcessNameFormula = ""
        Exit Function
    End If
    
    ' Find Process_Name column
    Set processRange = FindColumnInSheet(processSheet, "Process_Name")
    If processRange Is Nothing Then
        GetProcessNameFormula = ""
        Exit Function
    End If
    
    ' Create formula referencing the Process_Name column
    formula = "=" & processSheet.Name & "!" & processRange.Address
    GetProcessNameFormula = formula
End Function

' Function to get Flow Name validation formula
Function GetFlowNameFormula() As String
    Dim flowSheet As Worksheet
    Dim flowRange As Range
    Dim formula As String
    
    ' Look for flow definition sheet
    On Error Resume Next
    Set flowSheet = ThisWorkbook.Worksheets("1_1_Definition_Flows")
    On Error GoTo 0
    
    If flowSheet Is Nothing Then
        GetFlowNameFormula = ""
        Exit Function
    End If
    
    ' Find Flow_Name column
    Set flowRange = FindColumnInSheet(flowSheet, "Flow_Name")
    If flowRange Is Nothing Then
        GetFlowNameFormula = ""
        Exit Function
    End If
    
    ' Create formula referencing the Flow_Name column
    formula = "=" & flowSheet.Name & "!" & flowRange.Address
    GetFlowNameFormula = formula
End Function

' Function to get Yes/No validation formula
Function GetYesNoFormula() As String
    Dim codelistSheet As Worksheet
    Dim codelistTable As ListObject
    Dim codelistRange As Range
    
    ' Check if codelist sheet exists
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        ' Use simple Yes/No list
        GetYesNoFormula = "Yes,No"
        Exit Function
    End If
    
    ' Look for Yes/No table
    For Each codelistTable In codelistSheet.ListObjects
        If codelistTable.Name = "CL_YesNo" Then
            Set codelistRange = codelistTable.DataBodyRange.Columns(2) ' YesNo column
            GetYesNoFormula = "=" & codelistSheet.Name & "!" & codelistRange.Address
            Exit Function
        End If
    Next codelistTable
    
    ' Fallback to simple Yes/No
    GetYesNoFormula = "Yes,No"
End Function

' Function to get Configuration validation formula
Function GetConfigurationFormula(columnName As String) As String
    Dim codelistSheet As Worksheet
    Dim codelistTable As ListObject
    Dim codelistRange As Range
    Dim valueColumn As Long
    
    ' Check if codelist sheet exists
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        GetConfigurationFormula = ""
        Exit Function
    End If
    
    ' Look for table with matching name (with CL_ prefix)
    For Each codelistTable In codelistSheet.ListObjects
        If codelistTable.Name = "CL_" & columnName Then
            ' Found matching codelist table
            valueColumn = FindValueColumnInTable(codelistTable, columnName)
            If valueColumn > 0 Then
                Set codelistRange = codelistTable.DataBodyRange.Columns(valueColumn)
                GetConfigurationFormula = "=" & codelistSheet.Name & "!" & codelistRange.Address
                Exit Function
            End If
        End If
    Next codelistTable
    
    GetConfigurationFormula = ""
End Function

' Function to get Source validation formula
Function GetSourceFormula() As String
    Dim codelistSheet As Worksheet
    Dim codelistTable As ListObject
    Dim codelistRange As Range
    
    ' Check if codelist sheet exists
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        GetSourceFormula = ""
        Exit Function
    End If
    
    ' Look for Type_Source table
    For Each codelistTable In codelistSheet.ListObjects
        If codelistTable.Name = "CL_Type_Source" Then
            Set codelistRange = codelistTable.DataBodyRange.Columns(2) ' Type_Source column
            GetSourceFormula = "=" & codelistSheet.Name & "!" & codelistRange.Address
            Exit Function
        End If
    Next codelistTable
    
    GetSourceFormula = ""
End Function

' Function to find column in sheet
Function FindColumnInSheet(ws As Worksheet, columnName As String) As Range
    Dim headerRow As Long
    Dim col As Long
    
    ' Check row 1 first
    Set FindColumnInSheet = ws.Rows(1).Find(columnName, LookIn:=xlValues, LookAt:=xlWhole)
    If Not FindColumnInSheet Is Nothing Then Exit Function
    
    ' Check row 2 if row 1 didn't work
    Set FindColumnInSheet = ws.Rows(2).Find(columnName, LookIn:=xlValues, LookAt:=xlWhole)
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

' Function to create dynamic validation lists
Sub CreateDynamicValidationLists()
    Dim processSheet As Worksheet
    Dim flowSheet As Worksheet
    Dim codelistSheet As Worksheet
    Dim processRange As Range
    Dim flowRange As Range
    Dim nextRow As Long
    
    ' Get or create codelist sheet
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If codelistSheet Is Nothing Then
        Set codelistSheet = ThisWorkbook.Worksheets.Add
        codelistSheet.Name = "Codelists"
    End If
    
    ' Find next available position
    nextRow = codelistSheet.Cells(codelistSheet.Rows.Count, 1).End(xlUp).Row + 2
    
    ' Create Process Names validation list
    Set processSheet = ThisWorkbook.Worksheets("2_1_Definition_Processes")
    If Not processSheet Is Nothing Then
        Set processRange = FindColumnInSheet(processSheet, "Process_Name")
        If Not processRange Is Nothing Then
            ' Create named range for process names
            ThisWorkbook.Names.Add Name:="ProcessNames", RefersTo:="=" & processSheet.Name & "!" & processRange.Address
            codelistSheet.Cells(nextRow, 1).Value = "Process Names"
            codelistSheet.Cells(nextRow, 2).Value = "=ProcessNames"
            nextRow = nextRow + 1
        End If
    End If
    
    ' Create Flow Names validation list
    Set flowSheet = ThisWorkbook.Worksheets("1_1_Definition_Flows")
    If Not flowSheet Is Nothing Then
        Set flowRange = FindColumnInSheet(flowSheet, "Flow_Name")
        If Not flowRange Is Nothing Then
            ' Create named range for flow names
            ThisWorkbook.Names.Add Name:="FlowNames", RefersTo:="=" & flowSheet.Name & "!" & flowRange.Address
            codelistSheet.Cells(nextRow, 1).Value = "Flow Names"
            codelistSheet.Cells(nextRow, 2).Value = "=FlowNames"
            nextRow = nextRow + 1
        End If
    End If
    
    MsgBox "Dynamic validation lists created successfully!", vbInformation
End Sub

' Function to show validation status
Sub ShowValidationStatus()
    Dim processSheet As Worksheet
    Dim flowSheet As Worksheet
    Dim codelistSheet As Worksheet
    Dim msg As String
    
    msg = "BioDYM Validation Status:" & vbCrLf & vbCrLf
    
    ' Check Process Names
    On Error Resume Next
    Set processSheet = ThisWorkbook.Worksheets("2_1_Definition_Processes")
    On Error GoTo 0
    
    If Not processSheet Is Nothing Then
        msg = msg & "✓ Process definition sheet found" & vbCrLf
        msg = msg & "  Process Names: " & processSheet.Cells(processSheet.Rows.Count, 1).End(xlUp).Row - 1 & " processes" & vbCrLf
    Else
        msg = msg & "✗ Process definition sheet not found" & vbCrLf
    End If
    
    ' Check Flow Names
    On Error Resume Next
    Set flowSheet = ThisWorkbook.Worksheets("1_1_Definition_Flows")
    On Error GoTo 0
    
    If Not flowSheet Is Nothing Then
        msg = msg & "✓ Flow definition sheet found" & vbCrLf
        msg = msg & "  Flow Names: " & flowSheet.Cells(flowSheet.Rows.Count, 1).End(xlUp).Row - 1 & " flows" & vbCrLf
    Else
        msg = msg & "✗ Flow definition sheet not found" & vbCrLf
    End If
    
    ' Check Codelists
    On Error Resume Next
    Set codelistSheet = ThisWorkbook.Worksheets("Codelists")
    On Error GoTo 0
    
    If Not codelistSheet Is Nothing Then
        msg = msg & "✓ Codelist sheet found" & vbCrLf
        msg = msg & "  Tables: " & codelistSheet.ListObjects.Count & " codelist tables" & vbCrLf
    Else
        msg = msg & "✗ Codelist sheet not found" & vbCrLf
    End If
    
    MsgBox msg, vbInformation, "Validation Status"
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
