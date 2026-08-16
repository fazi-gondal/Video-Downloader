; Inno Setup script for the Video Downloader Windows installer.
; Compiled in CI with:
;   ISCC.exe /DAppExe=<exe name> /DAppVersion=<x.y.z> /DAppArch=<x64|arm64> installer.iss
; AppExe is detected dynamically because flet names the executable
; after the project slug. AppArch matches the architecture the app was
; built for (the runner's CPU) and drives the installer's arch gating.

#ifndef AppExe
  #define AppExe "video_downloader.exe"
#endif
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef AppArch
  #define AppArch "x64"
#endif

#define AppName "Video Downloader"
#define AppPublisher "fazigondal"

[Setup]
AppId=com.fazigondal.videodownloader
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName=C:\Program Files\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\..\build
OutputBaseFilename=VideoDownloader-windows-{#AppArch}-setup
Compression=lzma2
SolidCompression=yes
#if AppArch == "arm64"
; arm64 binaries only run on Windows 11 ARM devices
ArchitecturesAllowed=arm64
ArchitecturesInstallIn64BitMode=arm64
#else
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
#endif
UninstallDisplayIcon={app}\{#AppExe}
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\build\windows\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
