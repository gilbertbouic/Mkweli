' Mkweli AML - Windows GUI Launcher
' VBScript launcher that provides a user-friendly interface without terminal windows
' Double-click to show menu, or run with arguments for direct actions

Option Explicit

' Constants
Const APP_NAME = "Mkweli AML"
Const APP_URL = "http://localhost:8000"
Const DOCKER_URL = "https://www.docker.com/products/docker-desktop/"

' Objects
Dim WshShell, FSO, objWMI
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
Set objWMI = GetObject("winmgmts:\\.\root\cimv2")

' Get script directory
Dim scriptPath, appDir
scriptPath = WScript.ScriptFullName
appDir = FSO.GetParentFolderName(scriptPath)

' Main entry point
Sub Main()
    Dim args, action
    Set args = WScript.Arguments
    
    If args.Count > 0 Then
        action = LCase(args(0))
    Else
        action = "menu"
    End If
    
    Select Case action
        Case "start"
            StartApplication
        Case "stop"
            StopApplication
        Case "restart"
            RestartApplication
        Case "open"
            OpenDashboard
        Case "logs"
            ViewLogs
        Case "status"
            ShowStatus
        Case Else
            ShowMainMenu
    End Select
End Sub

' Show main menu
Sub ShowMainMenu()
    Dim choice
    
    Do
        choice = InputBox( _
            APP_NAME & " Launcher" & vbCrLf & vbCrLf & _
            "Enter a number to select an action:" & vbCrLf & vbCrLf & _
            "1. Start Application" & vbCrLf & _
            "2. Stop Application" & vbCrLf & _
            "3. Restart Application" & vbCrLf & _
            "4. Open Dashboard (Browser)" & vbCrLf & _
            "5. View Logs" & vbCrLf & _
            "6. Check Status" & vbCrLf & _
            "7. Exit" & vbCrLf & vbCrLf & _
            "Current Status: " & GetQuickStatus(), _
            APP_NAME & " - Launcher", "1")
        
        If choice = "" Then Exit Do
        
        Select Case choice
            Case "1"
                StartApplication
            Case "2"
                StopApplication
            Case "3"
                RestartApplication
            Case "4"
                OpenDashboard
            Case "5"
                ViewLogs
            Case "6"
                ShowStatus
            Case "7"
                Exit Do
            Case Else
                MsgBox "Invalid selection. Please enter a number 1-7.", vbExclamation, APP_NAME
        End Select
    Loop
End Sub

' Check if Docker is installed
Function IsDockerInstalled()
    On Error Resume Next
    Dim result
    result = WshShell.Run("docker --version", 0, True)
    IsDockerInstalled = (result = 0)
    On Error GoTo 0
End Function

' Check if Docker is running
Function IsDockerRunning()
    On Error Resume Next
    Dim result
    result = WshShell.Run("docker info", 0, True)
    IsDockerRunning = (result = 0)
    On Error GoTo 0
End Function

' Check if application containers are running
Function IsAppRunning()
    On Error Resume Next
    Dim objExec, output
    Set objExec = WshShell.Exec("docker-compose ps --quiet")
    output = objExec.StdOut.ReadAll()
    IsAppRunning = (Len(Trim(output)) > 0)
    On Error GoTo 0
End Function

' Get quick status string
Function GetQuickStatus()
    If Not IsDockerInstalled() Then
        GetQuickStatus = "Docker not installed"
    ElseIf Not IsDockerRunning() Then
        GetQuickStatus = "Docker not running"
    ElseIf IsAppRunning() Then
        GetQuickStatus = "Running"
    Else
        GetQuickStatus = "Stopped"
    End If
End Function

' Start the application
Sub StartApplication()
    ' Check Docker installation
    If Not IsDockerInstalled() Then
        Dim result
        result = MsgBox("Docker Desktop is not installed." & vbCrLf & vbCrLf & _
            "Docker is required to run " & APP_NAME & "." & vbCrLf & vbCrLf & _
            "Would you like to download Docker Desktop now?", _
            vbYesNo + vbQuestion, APP_NAME)
        If result = vbYes Then
            WshShell.Run DOCKER_URL, 1, False
        End If
        Exit Sub
    End If
    
    ' Check if Docker is running
    If Not IsDockerRunning() Then
        MsgBox "Docker Desktop is not running." & vbCrLf & vbCrLf & _
            "Please start Docker Desktop from the Start Menu, " & _
            "wait for it to fully start (green icon in taskbar), " & _
            "then try again.", vbExclamation, APP_NAME
        
        ' Try to start Docker Desktop
        On Error Resume Next
        WshShell.Run """C:\Program Files\Docker\Docker\Docker Desktop.exe""", 1, False
        On Error GoTo 0
        Exit Sub
    End If
    
    ' Check if already running
    If IsAppRunning() Then
        Dim openResult
        openResult = MsgBox(APP_NAME & " is already running." & vbCrLf & vbCrLf & _
            "Would you like to open the dashboard?", vbYesNo + vbQuestion, APP_NAME)
        If openResult = vbYes Then
            OpenDashboard
        End If
        Exit Sub
    End If
    
    ' Start the application
    MsgBox "Starting " & APP_NAME & "..." & vbCrLf & vbCrLf & _
        "This may take a minute on first run." & vbCrLf & _
        "The dashboard will open automatically when ready.", _
        vbInformation, APP_NAME
    
    ' Change to app directory and start
    WshShell.CurrentDirectory = appDir
    Dim startResult
    startResult = WshShell.Run("docker-compose up -d", 0, True)
    
    If startResult = 0 Then
        ' Wait a moment for the container to start
        WScript.Sleep 5000
        
        MsgBox APP_NAME & " started successfully!" & vbCrLf & vbCrLf & _
            "Opening dashboard in your browser...", vbInformation, APP_NAME
        
        OpenDashboard
    Else
        MsgBox "Failed to start " & APP_NAME & "." & vbCrLf & vbCrLf & _
            "Please check the logs for more information.", vbCritical, APP_NAME
    End If
End Sub

' Stop the application
Sub StopApplication()
    If Not IsAppRunning() Then
        MsgBox APP_NAME & " is not running.", vbInformation, APP_NAME
        Exit Sub
    End If
    
    Dim confirm
    confirm = MsgBox("Are you sure you want to stop " & APP_NAME & "?", _
        vbYesNo + vbQuestion, APP_NAME)
    
    If confirm = vbYes Then
        WshShell.CurrentDirectory = appDir
        Dim result
        result = WshShell.Run("docker-compose down", 0, True)
        
        If result = 0 Then
            MsgBox APP_NAME & " has been stopped.", vbInformation, APP_NAME
        Else
            MsgBox "Failed to stop " & APP_NAME & ".", vbExclamation, APP_NAME
        End If
    End If
End Sub

' Restart the application
Sub RestartApplication()
    If Not IsDockerRunning() Then
        MsgBox "Docker Desktop is not running." & vbCrLf & _
            "Please start Docker Desktop first.", vbExclamation, APP_NAME
        Exit Sub
    End If
    
    MsgBox "Restarting " & APP_NAME & "..." & vbCrLf & _
        "This may take a moment.", vbInformation, APP_NAME
    
    WshShell.CurrentDirectory = appDir
    Dim result
    result = WshShell.Run("docker-compose restart", 0, True)
    
    If result = 0 Then
        WScript.Sleep 3000
        MsgBox APP_NAME & " restarted successfully!", vbInformation, APP_NAME
    Else
        MsgBox "Failed to restart " & APP_NAME & ".", vbExclamation, APP_NAME
    End If
End Sub

' Open dashboard in browser
Sub OpenDashboard()
    If Not IsAppRunning() Then
        Dim startResult
        startResult = MsgBox(APP_NAME & " is not running." & vbCrLf & vbCrLf & _
            "Would you like to start it now?", vbYesNo + vbQuestion, APP_NAME)
        If startResult = vbYes Then
            StartApplication
        End If
        Exit Sub
    End If
    
    WshShell.Run APP_URL, 1, False
End Sub

' View logs in notepad
Sub ViewLogs()
    If Not IsDockerRunning() Then
        MsgBox "Docker Desktop is not running.", vbExclamation, APP_NAME
        Exit Sub
    End If
    
    ' Get logs and save to temp file
    Dim tempFile, objExec, output
    tempFile = FSO.GetSpecialFolder(2) & "\mkweli_logs.txt"
    
    WshShell.CurrentDirectory = appDir
    Set objExec = WshShell.Exec("docker-compose logs --tail=100")
    output = objExec.StdOut.ReadAll()
    
    ' Write to temp file
    Dim objFile
    Set objFile = FSO.CreateTextFile(tempFile, True)
    objFile.WriteLine APP_NAME & " - Recent Logs"
    objFile.WriteLine String(50, "=")
    objFile.WriteLine ""
    objFile.WriteLine output
    objFile.Close
    
    ' Open in notepad
    WshShell.Run "notepad """ & tempFile & """", 1, False
End Sub

' Show detailed status
Sub ShowStatus()
    Dim status, msg
    
    msg = APP_NAME & " Status" & vbCrLf & String(30, "-") & vbCrLf & vbCrLf
    
    ' Docker installation
    If IsDockerInstalled() Then
        msg = msg & "Docker: Installed" & vbCrLf
    Else
        msg = msg & "Docker: NOT INSTALLED" & vbCrLf
        MsgBox msg & vbCrLf & "Please install Docker Desktop to use " & APP_NAME, _
            vbExclamation, APP_NAME
        Exit Sub
    End If
    
    ' Docker running
    If IsDockerRunning() Then
        msg = msg & "Docker Status: Running" & vbCrLf
    Else
        msg = msg & "Docker Status: NOT RUNNING" & vbCrLf
        MsgBox msg & vbCrLf & "Please start Docker Desktop", vbExclamation, APP_NAME
        Exit Sub
    End If
    
    ' App status
    If IsAppRunning() Then
        msg = msg & "Application: Running" & vbCrLf
        msg = msg & vbCrLf & "Dashboard URL: " & APP_URL
    Else
        msg = msg & "Application: Stopped" & vbCrLf
    End If
    
    MsgBox msg, vbInformation, APP_NAME
End Sub

' Run main
Main
