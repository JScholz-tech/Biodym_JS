Attribute VB_Name = "Remove_All_Comments"
' ============================================================================
' Remove All Comments - Quick Cleanup Macro
' ============================================================================
' Purpose: Remove all comments from all sheets in the workbook
' Usage: Run RemoveAllComments() to clean the workbook
' ============================================================================

Sub RemoveAllComments()
    '
    ' Remove all comments from entire workbook
    '
    Dim ws As Worksheet
    Dim totalRemoved As Long
    Dim response As VbMsgBoxResult

    ' Count comments before removal
    totalRemoved = 0
    For Each ws In ThisWorkbook.Worksheets
        totalRemoved = totalRemoved + ws.Comments.Count
    Next ws

    ' Confirm action
    If totalRemoved > 0 Then
        response = MsgBox("This will remove " & totalRemoved & " comments from ALL sheets." & vbCrLf & vbCrLf & _
                          "Are you sure?", vbYesNo + vbExclamation, "Confirm Delete")

        If response = vbNo Then
            MsgBox "Cancelled - no comments removed.", vbInformation, "Cancelled"
            Exit Sub
        End If
    Else
        MsgBox "No comments found in workbook.", vbInformation, "Nothing to Remove"
        Exit Sub
    End If

    ' Disable screen updating for performance
    Application.ScreenUpdating = False

    ' Remove all comments from all sheets
    For Each ws In ThisWorkbook.Worksheets
        ws.Cells.ClearComments
    Next ws

    ' Re-enable screen updating
    Application.ScreenUpdating = True

    ' Show result
    MsgBox "Successfully removed " & totalRemoved & " comments from " & _
           ThisWorkbook.Worksheets.Count & " sheets!", vbInformation, "Complete"
End Sub
