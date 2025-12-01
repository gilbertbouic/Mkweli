; Mkweli AML - Windows Installer Script
; Inno Setup 6.x Configuration
; Build with: iscc setup.iss

#define MyAppName "Mkweli AML"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Mkweli"
#define MyAppURL "https://mkweli.tech"
#define MyAppExeName "MkweliLauncher.vbs"

[Setup]
; Application Info
AppId={{E5A7F3C1-9B2D-4E8F-A1C3-7D5E9F2B4A6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL=https://github.com/gilbertbouic/Mkweli/releases

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=MkweliAML-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes

; Visual settings
SetupIconFile=..\static\favicon.ico
WizardStyle=modern
WizardImageFile=wizard-image.bmp
WizardSmallImageFile=wizard-small-image.bmp

; Privileges and compatibility
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; License
LicenseFile=..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Welcome to Mkweli AML Setup
WelcomeLabel2=This will install [name/ver] on your computer.%n%nMkweli AML is a free, open-source sanctions screening tool for KYC/AML compliance.%n%nClick Next to continue.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Create a Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked

[Files]
; Main application files
Source: "..\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,__pycache__,*.db,*.sqlite,venv,env,.git,.github,.env,instance,uploads,*.log,windows-installer\output"

; Windows-specific launcher and config
Source: "MkweliLauncher.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup-config.bat"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\instance"; Permissions: users-modify
Name: "{app}\uploads"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "wscript.exe"; Parameters: """{app}\{#MyAppExeName}"""; WorkingDir: "{app}"; Comment: "Launch Mkweli AML"
Name: "{group}\Mkweli Dashboard"; Filename: "http://localhost:8000"; Comment: "Open Mkweli in Browser"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "wscript.exe"; Parameters: """{app}\{#MyAppExeName}"""; WorkingDir: "{app}"; Tasks: desktopicon; Comment: "Launch Mkweli AML"

[Run]
; Check system requirements and Docker
Filename: "{app}\setup-config.bat"; Parameters: "check"; Flags: runhidden waituntilterminated; StatusMsg: "Checking system requirements..."

; Offer to launch application after install
Filename: "wscript.exe"; Parameters: """{app}\{#MyAppExeName}"""; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[UninstallRun]
; Stop Docker containers on uninstall
Filename: "docker-compose"; Parameters: "down"; WorkingDir: "{app}"; Flags: runhidden waituntilterminated

[Code]
const
  MIN_RAM_MB = 4096;
  MIN_DISK_GB = 5;

var
  DockerPage: TWizardPage;
  DockerMissingLabel: TLabel;
  DownloadDockerButton: TButton;
  SystemCheckPage: TWizardPage;
  SystemStatusLabel: TLabel;

// Get total system RAM in MB
function GetTotalRAM: Integer;
var
  WbemLocator, WbemServices, WbemObjectSet, WbemObject: Variant;
  TotalMemory: Int64;
begin
  Result := 0;
  try
    WbemLocator := CreateOleObject('WbemScripting.SWbemLocator');
    WbemServices := WbemLocator.ConnectServer('.', 'root\CIMV2');
    WbemObjectSet := WbemServices.ExecQuery('SELECT TotalPhysicalMemory FROM Win32_ComputerSystem');
    WbemObject := WbemObjectSet.ItemIndex(0);
    TotalMemory := WbemObject.TotalPhysicalMemory;
    Result := TotalMemory div (1024 * 1024); // Convert to MB
  except
    Result := 8192; // Default assumption if check fails
  end;
end;

// Check if Docker Desktop is installed
function IsDockerInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('docker', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

// Open Docker download page
procedure DownloadDockerClick(Sender: TObject);
var
  ErrorCode: Integer;
begin
  ShellExec('open', 'https://www.docker.com/products/docker-desktop/', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
end;

// Create Docker check page
procedure CreateDockerPage;
begin
  DockerPage := CreateCustomPage(wpSelectDir, 'Docker Desktop Required', 
    'Mkweli AML requires Docker Desktop to run.');
  
  DockerMissingLabel := TLabel.Create(DockerPage);
  DockerMissingLabel.Parent := DockerPage.Surface;
  DockerMissingLabel.Caption := 
    'Docker Desktop is not installed on this computer.' + #13#10 + #13#10 +
    'Docker is required to run Mkweli AML. It provides a secure,' + #13#10 +
    'isolated environment for the application.' + #13#10 + #13#10 +
    'Please click the button below to download Docker Desktop,' + #13#10 +
    'then install it and restart this setup.';
  DockerMissingLabel.AutoSize := True;
  DockerMissingLabel.Top := 20;
  DockerMissingLabel.Left := 0;
  DockerMissingLabel.WordWrap := True;
  DockerMissingLabel.Width := DockerPage.SurfaceWidth;
  
  DownloadDockerButton := TButton.Create(DockerPage);
  DownloadDockerButton.Parent := DockerPage.Surface;
  DownloadDockerButton.Caption := 'Download Docker Desktop';
  DownloadDockerButton.Width := 200;
  DownloadDockerButton.Height := 35;
  DownloadDockerButton.Top := 150;
  DownloadDockerButton.Left := 0;
  DownloadDockerButton.OnClick := @DownloadDockerClick;
end;

// Create system check page
procedure CreateSystemCheckPage;
var
  RAM: Integer;
  StatusText: String;
begin
  SystemCheckPage := CreateCustomPage(wpWelcome, 'System Requirements Check',
    'Checking if your computer meets the minimum requirements.');
  
  RAM := GetTotalRAM;
  
  StatusText := 'System Check Results:' + #13#10 + #13#10;
  
  if RAM >= MIN_RAM_MB then
    StatusText := StatusText + '✓ RAM: ' + IntToStr(RAM) + ' MB (Minimum: ' + IntToStr(MIN_RAM_MB) + ' MB)' + #13#10
  else
    StatusText := StatusText + '✗ RAM: ' + IntToStr(RAM) + ' MB (Minimum: ' + IntToStr(MIN_RAM_MB) + ' MB required)' + #13#10;
  
  StatusText := StatusText + '✓ Operating System: Windows 10/11 64-bit' + #13#10;
  StatusText := StatusText + #13#10 + 'Note: Mkweli requires approximately 5 GB of disk space.';
  
  SystemStatusLabel := TLabel.Create(SystemCheckPage);
  SystemStatusLabel.Parent := SystemCheckPage.Surface;
  SystemStatusLabel.Caption := StatusText;
  SystemStatusLabel.AutoSize := True;
  SystemStatusLabel.Top := 20;
  SystemStatusLabel.Left := 0;
  SystemStatusLabel.WordWrap := True;
  SystemStatusLabel.Width := SystemCheckPage.SurfaceWidth;
end;

// Control which pages are shown
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  
  // Skip Docker page if Docker is installed
  if PageID = DockerPage.ID then
    Result := IsDockerInstalled;
end;

// Initialize wizard
procedure InitializeWizard;
begin
  CreateSystemCheckPage;
  CreateDockerPage;
end;

// Pre-installation check
function NextButtonClick(CurPageID: Integer): Boolean;
var
  RAM: Integer;
begin
  Result := True;
  
  // Check RAM on system check page
  if CurPageID = SystemCheckPage.ID then
  begin
    RAM := GetTotalRAM;
    if RAM < MIN_RAM_MB then
    begin
      if MsgBox('Your system has less than the recommended RAM (' + IntToStr(RAM) + ' MB). ' +
        'Mkweli may run slowly. Do you want to continue anyway?', mbConfirmation, MB_YESNO) = IDNO then
        Result := False;
    end;
  end;
  
  // Check Docker on Docker page
  if CurPageID = DockerPage.ID then
  begin
    if not IsDockerInstalled then
    begin
      MsgBox('Docker Desktop must be installed before continuing. ' +
        'Please download and install Docker Desktop, then restart this setup.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;
