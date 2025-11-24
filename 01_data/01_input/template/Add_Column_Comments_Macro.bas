Attribute VB_Name = "Add_Column_Comments"
' ============================================================================
' BioDYM Column Comment Macro
' ============================================================================
' Purpose: Add descriptive comments to column headers from validation file
' Usage: Run AddCommentsFromCSV() to apply all comments
' ============================================================================

Option Explicit

Sub AddCommentsFromCSV()
    '
    ' Main procedure to add comments to all columns
    ' Reads validation data from CSV and applies comments to template
    '
    Dim csvPath As String
    Dim csvWb As Workbook
    Dim csvWs As Worksheet
    Dim lastRow As Long
    Dim i As Long
    Dim sheetName As String
    Dim columnName As String
    Dim description As String
    Dim ws As Worksheet
    Dim headerRow As Long
    Dim colNum As Integer
    Dim successCount As Integer
    Dim errorCount As Integer
    Dim skipCount As Integer

    ' Initialize counters
    successCount = 0
    errorCount = 0
    skipCount = 0

    ' CSV file path (adjust if needed)
    csvPath = ThisWorkbook.Path & "\7_1_Comments_Validation_NEW.csv"

    ' Check if CSV file exists
    If Dir(csvPath) = "" Then
        MsgBox "Validation file not found at:" & vbCrLf & csvPath, vbCritical, "File Not Found"
        Exit Sub
    End If

    ' Disable screen updating for performance
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False

    ' Open CSV file
    On Error GoTo ErrorHandler
    Set csvWb = Workbooks.Open(csvPath)
    Set csvWs = csvWb.Sheets(1)

    ' Find last row with data
    lastRow = csvWs.Cells(csvWs.Rows.Count, "A").End(xlUp).Row

    ' Show progress
    Debug.Print "Processing " & lastRow - 1 & " validation entries..."

    ' Loop through each row (skip header)
    For i = 2 To lastRow
        ' Read validation data
        sheetName = csvWs.Cells(i, 1).Value    ' Column A: Sheet_Name
        columnName = csvWs.Cells(i, 2).Value   ' Column B: Column_Name
        description = csvWs.Cells(i, 5).Value  ' Column E: Description

        ' Skip SYSTEM entries (generic system columns)
        If sheetName = "SYSTEM" Then
            ' Apply to all sheets if column exists
            Call AddCommentToAllSheets(columnName, description, successCount, skipCount)
        Else
            ' Apply to specific sheet
            Call AddCommentToSheet(sheetName, columnName, description, successCount, errorCount, skipCount)
        End If
    Next i

    ' Close CSV without saving
    csvWb.Close SaveChanges:=False

    ' Re-enable display
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True

    ' Show results
    MsgBox "Comment addition complete!" & vbCrLf & vbCrLf & _
           "Successfully added: " & successCount & vbCrLf & _
           "Skipped (already exist): " & skipCount & vbCrLf & _
           "Errors: " & errorCount, vbInformation, "Complete"

    Exit Sub

ErrorHandler:
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    MsgBox "Error: " & Err.Description, vbCritical, "Error"
    If Not csvWb Is Nothing Then csvWb.Close SaveChanges:=False
End Sub

Private Sub AddCommentToSheet(sheetName As String, columnName As String, description As String, _
                              ByRef successCount As Integer, ByRef errorCount As Integer, _
                              ByRef skipCount As Integer)
    '
    ' Add comment to a specific column in a specific sheet
    '
    Dim ws As Worksheet
    Dim headerRow As Long
    Dim colNum As Integer
    Dim targetCell As Range

    On Error GoTo SkipEntry

    ' Check if sheet exists
    Set ws = Nothing
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets(sheetName)
    On Error GoTo SkipEntry

    If ws Is Nothing Then
        Debug.Print "Sheet not found: " & sheetName
        errorCount = errorCount + 1
        Exit Sub
    End If

    ' Find header row (assume row 1)
    headerRow = 1

    ' Handle pattern columns (E#_*)
    If InStr(columnName, "E#_") > 0 Then
        Call AddCommentToPatternColumns(ws, columnName, description, headerRow, successCount, skipCount)
        Exit Sub
    End If

    ' Find column number
    colNum = FindColumnNumber(ws, columnName, headerRow)

    If colNum = 0 Then
        Debug.Print "Column not found: " & columnName & " in sheet " & sheetName
        errorCount = errorCount + 1
        Exit Sub
    End If

    ' Get target cell
    Set targetCell = ws.Cells(headerRow, colNum)

    ' Check if comment already exists
    If Not targetCell.Comment Is Nothing Then
        Debug.Print "Skipped (comment exists): " & sheetName & "." & columnName
        skipCount = skipCount + 1
        Exit Sub
    End If

    ' Add comment
    targetCell.AddComment description

    ' Format comment
    With targetCell.Comment
        .Shape.TextFrame.AutoSize = True
        .Shape.Width = 300 ' Adjust width as needed
    End With

    successCount = successCount + 1
    Debug.Print "Added: " & sheetName & "." & columnName

    Exit Sub

SkipEntry:
    errorCount = errorCount + 1
    Debug.Print "Error on: " & sheetName & "." & columnName & " - " & Err.Description
End Sub

Private Sub AddCommentToPatternColumns(ws As Worksheet, pattern As String, description As String, _
                                       headerRow As Long, ByRef successCount As Integer, _
                                       ByRef skipCount As Integer)
    '
    ' Add comments to all columns matching a pattern (e.g., E#_TC_Value)
    '
    Dim col As Integer
    Dim colName As String
    Dim patternBase As String
    Dim targetCell As Range

    ' Extract pattern base (remove E#_)
    patternBase = Replace(pattern, "E#_", "")

    ' Loop through all columns in header row
    For col = 1 To ws.UsedRange.Columns.Count
        colName = ws.Cells(headerRow, col).Value

        ' Check if column matches pattern (E1_, E2_, ... E6_)
        If (InStr(colName, "E1_" & patternBase) > 0 Or _
            InStr(colName, "E2_" & patternBase) > 0 Or _
            InStr(colName, "E3_" & patternBase) > 0 Or _
            InStr(colName, "E4_" & patternBase) > 0 Or _
            InStr(colName, "E5_" & patternBase) > 0 Or _
            InStr(colName, "E6_" & patternBase) > 0) Then

            Set targetCell = ws.Cells(headerRow, col)

            ' Skip if comment exists
            If Not targetCell.Comment Is Nothing Then
                skipCount = skipCount + 1
            Else
                ' Add comment
                targetCell.AddComment description
                With targetCell.Comment
                    .Shape.TextFrame.AutoSize = True
                    .Shape.Width = 300
                End With
                successCount = successCount + 1
            End If
        End If
    Next col
End Sub

Private Sub AddCommentToAllSheets(columnName As String, description As String, _
                                  ByRef successCount As Integer, ByRef skipCount As Integer)
    '
    ' Add comment to a column in all sheets where it exists
    ' Used for system columns (Complete?, ID, ODYM_*)
    '
    Dim ws As Worksheet
    Dim colNum As Integer
    Dim targetCell As Range
    Dim headerRow As Long

    headerRow = 1

    ' Loop through all sheets
    For Each ws In ThisWorkbook.Worksheets
        ' Handle ODYM wildcard pattern
        If columnName = "ODYM_*" Then
            Call AddCommentToODYMColumns(ws, description, headerRow, successCount, skipCount)
        Else
            ' Normal column
            colNum = FindColumnNumber(ws, columnName, headerRow)

            If colNum > 0 Then
                Set targetCell = ws.Cells(headerRow, colNum)

                ' Skip if comment exists
                If Not targetCell.Comment Is Nothing Then
                    skipCount = skipCount + 1
                Else
                    targetCell.AddComment description
                    With targetCell.Comment
                        .Shape.TextFrame.AutoSize = True
                        .Shape.Width = 300
                    End With
                    successCount = successCount + 1
                End If
            End If
        End If
    Next ws
End Sub

Private Sub AddCommentToODYMColumns(ws As Worksheet, description As String, headerRow As Long, _
                                    ByRef successCount As Integer, ByRef skipCount As Integer)
    '
    ' Add comments to all ODYM columns (ODYM_*)
    '
    Dim col As Integer
    Dim colName As String
    Dim targetCell As Range

    ' Loop through all columns
    For col = 1 To ws.UsedRange.Columns.Count
        colName = ws.Cells(headerRow, col).Value

        ' Check if column starts with ODYM_
        If Left(colName, 5) = "ODYM_" Then
            Set targetCell = ws.Cells(headerRow, col)

            ' Skip if comment exists
            If Not targetCell.Comment Is Nothing Then
                skipCount = skipCount + 1
            Else
                targetCell.AddComment description
                With targetCell.Comment
                    .Shape.TextFrame.AutoSize = True
                    .Shape.Width = 300
                End With
                successCount = successCount + 1
            End If
        End If
    Next col
End Sub

Private Function FindColumnNumber(ws As Worksheet, columnName As String, headerRow As Long) As Integer
    '
    ' Find column number by name in header row
    ' Returns 0 if not found
    '
    Dim col As Integer

    FindColumnNumber = 0

    ' Search header row
    For col = 1 To ws.UsedRange.Columns.Count
        If ws.Cells(headerRow, col).Value = columnName Then
            FindColumnNumber = col
            Exit Function
        End If
    Next col
End Function

' ============================================================================
' OPTIONAL: Remove all comments (useful for testing/resetting)
' ============================================================================

Sub RemoveAllComments()
    '
    ' Remove all comments from all sheets
    ' WARNING: This will delete ALL comments in the workbook!
    '
    Dim ws As Worksheet
    Dim response As VbMsgBoxResult

    ' Confirm action
    response = MsgBox("This will remove ALL comments from ALL sheets." & vbCrLf & vbCrLf & _
                      "Are you sure?", vbYesNo + vbExclamation, "Confirm Delete")

    If response = vbNo Then Exit Sub

    Application.ScreenUpdating = False

    ' Loop through all sheets
    For Each ws In ThisWorkbook.Worksheets
        ws.Cells.ClearComments
    Next ws

    Application.ScreenUpdating = True

    MsgBox "All comments removed!", vbInformation, "Complete"
End Sub

' ============================================================================
' OPTIONAL: Force update (overwrite existing comments)
' ============================================================================

Sub ForceUpdateComments()
    '
    ' Remove all comments and re-add from validation file
    '
    Dim response As VbMsgBoxResult

    response = MsgBox("This will REPLACE all existing comments with new ones from validation file." & vbCrLf & vbCrLf & _
                      "Continue?", vbYesNo + vbQuestion, "Force Update")

    If response = vbNo Then Exit Sub

    ' Remove existing
    Call RemoveAllComments

    ' Add new
    Call AddCommentsFromCSV
End Sub
