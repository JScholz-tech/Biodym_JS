' Simple BioDYM Validation Macro with Column References
' This macro creates validation lists that reference entire Process and Flow columns
' No need to refresh validation when adding new processes/flows

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
        
        ' Apply ONLY validation messages (no validation rules)
        Call ApplyValidationMessagesOnly(targetSheet, targetColumn.Column, title, body, purpose, action, note, columnName)
        
NextRow:
    Next validationRow
    
    MsgBox "Validation messages applied successfully! (Existing validation rules preserved)", vbInformation
End Sub

' NEW FUNCTION: Apply ONLY validation messages (preserves existing validation rules)
Sub ApplyValidationMessagesOnly(ws As Worksheet, col As Long, title As String, body As String, purpose As String, action As String, note As String, columnName As String)
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
    
    ' Apply ONLY input messages to data cells (preserve existing validation rules)
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
        On Error Resume Next
        With cell.Validation
            ' Only update input message, don't change validation rules
            If Not .Validation Is Nothing Then
                .InputTitle = title
                .InputMessage = body
                .ShowInput = True
            End If
        End With
        On Error GoTo 0
    Next cell
End Sub

' FUNCTION: Apply ONLY validation rules (for initial setup)
Sub ApplyValidationRulesOnly()
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
        If validationRow.Cells(1, 2).Value = "" Then GoTo NextRuleRow
        
        ' Get target sheet and column
        Dim sheetName As String
        Dim columnName As String
        Dim title As String
        Dim body As String
        
        sheetName = validationRow.Cells(1, 2).Value  ' Name_sheet
        columnName = validationRow.Cells(1, 3).Value  ' Name_Column
        title = validationRow.Cells(1, 4).Value  ' Titel:
        body = validationRow.Cells(1, 5).Value  ' Body:
        
        ' Skip if essential data is missing
        If sheetName = "" Or columnName = "" Or title = "" Then GoTo NextRuleRow
        
        ' Check if target sheet exists
        On Error Resume Next
        Set targetSheet = ThisWorkbook.Worksheets(sheetName)
        On Error GoTo 0
        
        If targetSheet Is Nothing Then GoTo NextRuleRow
        
        ' Find the column in the target sheet
        Set targetColumn = Nothing
        On Error Resume Next
        Set targetColumn = targetSheet.Rows(1).Find(columnName, LookIn:=xlValues, LookAt:=xlWhole)
        On Error GoTo 0
        
        If targetColumn Is Nothing Then GoTo NextRuleRow
        
        ' Apply ONLY validation rules (no messages)
        Call ApplyValidationRulesToColumn(targetSheet, targetColumn.Column, title, body, columnName)
        
NextRuleRow:
    Next validationRow
    
    MsgBox "Validation rules applied successfully! (No messages added)", vbInformation
End Sub

' FUNCTION: Apply validation rules to a column (no messages)
Sub ApplyValidationRulesToColumn(ws As Worksheet, col As Long, title As String, body As String, columnName As String)
    Dim dataStartRow As Long
    Dim dataEndRow As Long
    Dim cell As Range
    Dim validationFormula As String
    Dim fieldType As String
    
    ' Find data range (skip header row)
    dataStartRow = 2
    dataEndRow = ws.Cells(ws.Rows.Count, col).End(xlUp).Row
    
    ' Skip if no data
    If dataEndRow < dataStartRow Then Exit Sub
    
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

' FUNCTION: Manual validation setup with hardcoded rules
Sub ApplyManualValidationRules()
    Dim ws As Worksheet
    Dim col As Long
    
    ' Process_Logic validation
    Set ws = ThisWorkbook.Worksheets("2_1_Definition_Processes")
    col = FindColumnNumber(ws, "Process_Logic")
    If col > 0 Then
        Call ApplyManualValidationToColumn(ws, col, "Process Logic Selection", _
            "Choose how this process handles material flows", _
            "Input,Output,Pass-through,Transformation")
    End If
    
    ' Process_Name validation
    col = FindColumnNumber(ws, "Process_Name")
    If col > 0 Then
        Call ApplyManualValidationToColumn(ws, col, "Process Name Selection", _
            "Select from available process names", _
            "=2_1_Definition_Processes!$C:$C")
    End If
    
    ' Flow_Name validation
    Set ws = ThisWorkbook.Worksheets("1_1_Definition_Flows")
    col = FindColumnNumber(ws, "Flow_Name")
    If col > 0 Then
        Call ApplyManualValidationToColumn(ws, col, "Flow Name Selection", _
            "Select from available flow names", _
            "=1_1_Definition_Flows!$D:$D")
    End If
    
    ' Yes/No fields validation
    Call ApplyYesNoValidationToAllSheets()
    
    ' Configuration fields validation
    Call ApplyConfigurationValidationToAllSheets()
    
    MsgBox "Manual validation rules applied successfully!", vbInformation
End Sub

' FUNCTION: Apply manual validation to a specific column
Sub ApplyManualValidationToColumn(ws As Worksheet, col As Long, title As String, message As String, formula As String)
    Dim dataStartRow As Long
    Dim dataEndRow As Long
    Dim cell As Range
    
    ' Find data range (skip header row)
    dataStartRow = 2
    dataEndRow = ws.Cells(ws.Rows.Count, col).End(xlUp).Row
    
    ' Skip if no data
    If dataEndRow < dataStartRow Then Exit Sub
    
    ' Apply validation to data cells
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
        On Error Resume Next
        With cell.Validation
            .Delete
            
            If Left(formula, 1) = "=" Then
                ' Reference formula (e.g., =Sheet!$C:$C)
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:=formula
            Else
                ' Simple list (e.g., "Yes,No")
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:=formula
            End If
            
            .InputTitle = title
            .InputMessage = message
            .ShowInput = True
            .ShowError = True
            .ErrorTitle = "Invalid Entry"
            .ErrorMessage = "Please select a valid option from the dropdown"
        End With
        On Error GoTo 0
    Next cell
End Sub

' FUNCTION: Find column number by name
Function FindColumnNumber(ws As Worksheet, columnName As String) As Long
    Dim headerCell As Range
    
    ' Check row 1 first
    Set headerCell = ws.Rows(1).Find(columnName, LookIn:=xlValues, LookAt:=xlWhole)
    If Not headerCell Is Nothing Then
        FindColumnNumber = headerCell.Column
        Exit Function
    End If
    
    ' Check row 2 if row 1 didn't work
    Set headerCell = ws.Rows(2).Find(columnName, LookIn:=xlValues, LookAt:=xlWhole)
    If Not headerCell Is Nothing Then
        FindColumnNumber = headerCell.Column
        Exit Function
    End If
    
    FindColumnNumber = 0
End Function

' FUNCTION: Apply Yes/No validation to all sheets
Sub ApplyYesNoValidationToAllSheets()
    Dim ws As Worksheet
    Dim col As Long
    Dim sheetNames As Variant
    Dim i As Long
    
    ' List of sheets to check
    sheetNames = Array("2_1_Definition_Processes", "2_2_static_TCs", "2_3_dynamic_TCs", "2_4_Initial_Stock")
    
    For i = 0 To UBound(sheetNames)
        On Error Resume Next
        Set ws = ThisWorkbook.Worksheets(sheetNames(i))
        On Error GoTo 0
        
        If Not ws Is Nothing Then
            ' Check for Yes/No columns
            col = FindColumnNumber(ws, "Complete?")
            If col > 0 Then
                Call ApplyManualValidationToColumn(ws, col, "Complete Status", _
                    "Mark if this entry is complete", "Yes,No")
            End If
            
            col = FindColumnNumber(ws, "WC?")
            If col > 0 Then
                Call ApplyManualValidationToColumn(ws, col, "WC Element", _
                    "Include WC element in this flow", "Yes,No")
            End If
            
            col = FindColumnNumber(ws, "DM?")
            If col > 0 Then
                Call ApplyManualValidationToColumn(ws, col, "DM Element", _
                    "Include DM element in this flow", "Yes,No")
            End If
            
            col = FindColumnNumber(ws, "CC?")
            If col > 0 Then
                Call ApplyManualValidationToColumn(ws, col, "CC Element", _
                    "Include CC element in this flow", "Yes,No")
            End If
        End If
    Next i
End Sub

' FUNCTION: Apply configuration validation to all sheets
Sub ApplyConfigurationValidationToAllSheets()
    Dim ws As Worksheet
    Dim col As Long
    
    ' TC_Configuration validation
    Set ws = ThisWorkbook.Worksheets("2_1_Definition_Processes")
    col = FindColumnNumber(ws, "TC_Configuration")
    If col > 0 Then
        Call ApplyManualValidationToColumn(ws, col, "Transfer Coefficient Configuration", _
            "Choose how transfer coefficients are handled", "Static,Dynamic,None")
    End If
    
    ' Stock_Configuration validation
    col = FindColumnNumber(ws, "Stock_Configuration")
    If col > 0 Then
        Call ApplyManualValidationToColumn(ws, col, "Stock Configuration", _
            "Choose if this process maintains stocks", "Stock,None")
    End If
    
    ' Type_Source validation
    Set ws = ThisWorkbook.Worksheets("1_2_Data_Flows")
    col = FindColumnNumber(ws, "Type_Source")
    If col > 0 Then
        Call ApplyManualValidationToColumn(ws, col, "Source Type", _
            "Select the type of data source", "Literature,Measurement,Estimate,Database,Expert Knowledge")
    End If
End Sub

' FUNCTION: Apply custom validation to specific fields
Sub ApplyCustomValidationRules()
    Dim ws As Worksheet
    Dim col As Long
    
    ' Example: Custom validation for specific fields
    
    ' Process_Logic with custom options
    Set ws = ThisWorkbook.Worksheets("2_1_Definition_Processes")
    col = FindColumnNumber(ws, "Process_Logic")
    If col > 0 Then
        Call ApplyCustomValidationToColumn(ws, col, "Process Logic Selection", _
            "Choose how this process handles material flows", _
            "Input,Output,Pass-through,Transformation", _
            "Please select a valid process logic type")
    End If
    
    ' Custom Yes/No with different options
    col = FindColumnNumber(ws, "Complete?")
    If col > 0 Then
        Call ApplyCustomValidationToColumn(ws, col, "Completion Status", _
            "Mark the completion status of this entry", _
            "Complete,In Progress,Not Started", _
            "Please select a valid completion status")
    End If
End Sub

' FUNCTION: Apply custom validation with full control
Sub ApplyCustomValidationToColumn(ws As Worksheet, col As Long, title As String, message As String, formula As String, errorMessage As String)
    Dim dataStartRow As Long
    Dim dataEndRow As Long
    Dim cell As Range
    
    ' Find data range (skip header row)
    dataStartRow = 2
    dataEndRow = ws.Cells(ws.Rows.Count, col).End(xlUp).Row
    
    ' Skip if no data
    If dataEndRow < dataStartRow Then Exit Sub
    
    ' Apply validation to data cells
    For Each cell In ws.Range(ws.Cells(dataStartRow, col), ws.Cells(dataEndRow, col))
        On Error Resume Next
        With cell.Validation
            .Delete
            
            If Left(formula, 1) = "=" Then
                ' Reference formula (e.g., =Sheet!$C:$C)
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:=formula
            Else
                ' Simple list (e.g., "Yes,No")
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:=formula
            End If
            
            ' Input message settings
            .InputTitle = title
            .InputMessage = message
            .ShowInput = True
            
            ' Error message settings
            .ShowError = True
            .ErrorTitle = "Invalid Entry"
            .ErrorMessage = errorMessage
            .ErrorStyle = xlValidAlertStop
        End With
        On Error GoTo 0
    Next cell
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
    ' Process_Logic fields (must be checked first to avoid Process_Name conflict)
    If InStr(columnName, "Process_Logic") > 0 Then
        DetermineFieldType = "Configuration"
    ' Process_Name fields (exact match to avoid Process_Logic conflict)
    ElseIf columnName = "Process_Name" Or InStr(columnName, "Process_Name") > 0 Then
        DetermineFieldType = "ProcessName"
    ' Flow_Name fields (exact match)
    ElseIf columnName = "Flow_Name" Or InStr(columnName, "Flow_Name") > 0 Then
        DetermineFieldType = "FlowName"
    ' Yes/No fields
    ElseIf InStr(columnName, "?") > 0 Then
        DetermineFieldType = "YesNo"
    ' Configuration fields
    ElseIf InStr(columnName, "Configuration") > 0 Or InStr(columnName, "Complete") > 0 Then
        DetermineFieldType = "Configuration"
    ' Source fields
    ElseIf InStr(columnName, "Source") > 0 Or InStr(columnName, "Author") > 0 Then
        DetermineFieldType = "Source"
    ' Other Process fields (but not Process_Name or Process_Logic)
    ElseIf InStr(columnName, "Process") > 0 Then
        DetermineFieldType = "ProcessName"
    ' Other Flow fields (but not Flow_Name)
    ElseIf InStr(columnName, "Flow") > 0 Then
        DetermineFieldType = "FlowName"
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

' Function to get Process Name validation formula (entire column)
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
    
    ' Create formula referencing the ENTIRE Process_Name column (from row 2 to end)
    formula = "=" & processSheet.Name & "!" & processRange.Address
    GetProcessNameFormula = formula
End Function

' Function to get Flow Name validation formula (entire column)
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
    
    ' Create formula referencing the ENTIRE Flow_Name column (from row 2 to end)
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
        ' Fallback to hardcoded values for common configuration fields
        If columnName = "Process_Logic" Then
            GetConfigurationFormula = "Input,Output,Pass-through,Transformation"
        ElseIf InStr(columnName, "Complete") > 0 Then
            GetConfigurationFormula = "Yes,No"
        ElseIf InStr(columnName, "Configuration") > 0 Then
            GetConfigurationFormula = "Static,Dynamic,None"
        Else
            GetConfigurationFormula = ""
        End If
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
    
    ' Fallback to hardcoded values if no codelist table found
    If columnName = "Process_Logic" Then
        GetConfigurationFormula = "Input,Output,Pass-through,Transformation"
    ElseIf InStr(columnName, "Complete") > 0 Then
        GetConfigurationFormula = "Yes,No"
    ElseIf InStr(columnName, "Configuration") > 0 Then
        GetConfigurationFormula = "Static,Dynamic,None"
    Else
        GetConfigurationFormula = ""
    End If
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

' Debug function to show what validation is being applied
Sub DebugValidation()
    Dim validationSheet As Worksheet
    Dim validationData As Range
    Dim validationRow As Range
    Dim sheetName As String
    Dim columnName As String
    Dim fieldType As String
    Dim validationFormula As String
    Dim msg As String
    
    ' Get validation sheet
    Set validationSheet = ThisWorkbook.Worksheets("7_1_Comments_Validation")
    
    ' Get validation data (starting from row 4, with headers in row 3)
    Set validationData = validationSheet.Range("A4:J" & validationSheet.Cells(validationSheet.Rows.Count, "A").End(xlUp).Row)
    
    msg = "Validation Debug Info:" & vbCrLf & vbCrLf
    
    ' Process first few validation instructions
    Dim count As Long
    count = 0
    For Each validationRow In validationData.Rows
        If count >= 5 Then Exit For ' Only show first 5 for debugging
        
        ' Skip empty rows
        If validationRow.Cells(1, 2).Value = "" Then GoTo NextDebugRow
        
        sheetName = validationRow.Cells(1, 2).Value  ' Name_sheet
        columnName = validationRow.Cells(1, 3).Value  ' Name_Column
        
        ' Skip if essential data is missing
        If sheetName = "" Or columnName = "" Then GoTo NextDebugRow
        
        fieldType = DetermineFieldType(columnName)
        validationFormula = GetValidationFormula(columnName, fieldType)
        
        msg = msg & "Sheet: " & sheetName & vbCrLf
        msg = msg & "Column: " & columnName & vbCrLf
        msg = msg & "Field Type: " & fieldType & vbCrLf
        msg = msg & "Formula: " & validationFormula & vbCrLf
        msg = msg & "---" & vbCrLf
        
        count = count + 1
        
NextDebugRow:
    Next validationRow
    
    MsgBox msg, vbInformation, "Debug Validation"
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
