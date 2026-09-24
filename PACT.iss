#define AppVersion "1.3.1"
[Setup]
AppId={code:AppIdentity}
AppName=PACT
AppVersion={#AppVersion}
AppVerName=PACT v1.3.1
AppPublisher=PACT
DefaultDirName={localappdata}\Programs\PACT
DefaultGroupName={code:GroupName}
UninstallDisplayName={code:DisplayName}
UninstallDisplayIcon={app}\PACT.exe
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=dist
OutputBaseFilename=PACT_v1.3.1_Setup
SetupIconFile=app\assets\pact.ico
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=100
CloseApplications=force
RestartApplications=no
DisableProgramGroupPage=yes
UsePreviousAppDir=yes
UsePreviousLanguage=no
UsePreviousGroup=no
VersionInfoProductName=PACT
VersionInfoDescription=PACT Setup
VersionInfoVersion=1.3.1.0
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked
Name: startup; Description: "Start PACT hidden when I sign in to Windows"; Flags: unchecked
[Files]
Source: "package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "PACTMaintenance.exe"; Flags: dontcopy
Source: "app\assets\fonts\Newsreader.ttf"; Flags: dontcopy
[Icons]
Name: "{group}\PACT"; Filename: "{app}\PACT.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall PACT"; Filename: "{uninstallexe}"
Name: "{userdesktop}\PACT"; Filename: "{app}\PACT.exe"; Tasks: desktopicon
Name: "{userstartup}\PACT"; Filename: "{app}\PACT.exe"; Parameters: "--hidden"; Tasks: startup
[Run]
Filename: "{app}\PACT.exe"; Description: "Open PACT"; Flags: nowait postinstall skipifsilent; Check: LaunchAllowed
[Code]
function AddFontResourceEx(FileName: String; Flags: DWORD; Reserved: Integer): Integer;
 external 'AddFontResourceExW@gdi32.dll stdcall';
procedure RemoveLegacyStartup;
var Shell, Link: Variant; ShortcutPath, Legacy, Value: String;
begin
 if ExpandConstant('{param:TESTMODE|0}') = '1' then Exit;
 Legacy := Lowercase(ExpandConstant('{localappdata}\Programs\PersonalOS\'));
 ShortcutPath := ExpandConstant('{userstartup}\PersonalOS.lnk');
 if FileExists(ShortcutPath) then begin
  try
   Shell := CreateOleObject('WScript.Shell');
   Link := Shell.CreateShortcut(ShortcutPath);
   Value := Link.TargetPath;
   Value := Lowercase(Value);
   if Pos(Legacy, Value) = 1 then DeleteFile(ShortcutPath);
  except
   Log('Legacy startup shortcut could not be inspected.');
  end;
 end;
 if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'PersonalOS', Value) then
  if Pos(Legacy, Lowercase(Value)) > 0 then
   RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'PersonalOS');
end;
function TestMode: Boolean;
begin
 Result := ExpandConstant('{param:TESTMODE|0}') = '1';
end;
function AppIdentity(Param: String): String;
begin
 if TestMode then Result := 'PACT-Validation-Only' else Result := 'PACT-Desktop-Stable';
end;
function GroupName(Param: String): String;
begin
 if TestMode then Result := 'PACT Validation' else Result := 'PACT';
end;
function DisplayName(Param: String): String;
begin
 if TestMode then Result := 'PACT Validation' else Result := 'PACT';
end;
function LaunchAllowed: Boolean;
begin
 Result := not TestMode;
end;
function PrepareToInstall(var NeedsRestart: Boolean): String;
var Code: Integer; Args: String;
begin
 Result := '';
 ExtractTemporaryFile('PACTMaintenance.exe');
 Args := '"' + ExpandConstant('{app}') + '"';
 if not TestMode then Args := Args + ' "' + ExpandConstant('{localappdata}\Programs\PersonalOS') + '"';
 if not Exec(ExpandConstant('{tmp}\PACTMaintenance.exe'), Args, '', SW_HIDE, ewWaitUntilTerminated, Code) then
  Result := 'PACT could not close the previous installation. Close PACT and retry.'
 else if Code <> 0 then Result := 'A running PACT installation could not be closed. Close it and retry.';
end;
procedure CurStepChanged(CurStep: TSetupStep);
var Code: Integer;
begin
 if CurStep = ssPostInstall then begin
  if not Exec(ExpandConstant('{app}\PACT.exe'), '--self-test', ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, Code) then
   RaiseException('PACT startup verification could not run. Please reinstall.');
  if Code <> 0 then RaiseException('PACT startup verification failed. Please reinstall.');
  RemoveLegacyStartup;
 end;
end;
procedure InitializeWizard;
begin
 ExtractTemporaryFile('Newsreader.ttf');
 AddFontResourceEx(ExpandConstant('{tmp}\Newsreader.ttf'), $10, 0);
 WizardForm.Font.Color := $040410;
 WizardForm.Color := $FAFAFA;
 WizardForm.MainPanel.Color := $FAFAFA;
 WizardForm.Font.Name := 'Newsreader';
end;
function InitializeUninstall: Boolean;
var Code: Integer;
begin
 Result := True;
 if FileExists(ExpandConstant('{app}\PACT.exe')) then
  Exec(ExpandConstant('{app}\PACT.exe'), '--shutdown', ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, Code);
end;
