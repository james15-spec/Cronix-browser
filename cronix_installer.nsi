; Cronix Browser - Windows Installer
; Built with NSIS

Unicode True

;--------------------------------
; General

Name "Cronix"
OutFile "CronixSetup.exe"
InstallDir "$PROGRAMFILES64\Cronix"
InstallDirRegKey HKLM "Software\Croftonix\Cronix" "Install_Dir"
RequestExecutionLevel admin

;--------------------------------
; Version info

VIProductVersion "1.4.4.0"
VIAddVersionKey "ProductName"      "Cronix"
VIAddVersionKey "CompanyName"      "Croftonix"
VIAddVersionKey "FileDescription"  "Cronix Browser Installer"
VIAddVersionKey "FileVersion"      "1.4.4"
VIAddVersionKey "ProductVersion"   "1.4.4"
VIAddVersionKey "LegalCopyright"   "Croftonix 2026"

;--------------------------------
; Interface

!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON          "cronix.ico"
!define MUI_UNICON        "cronix.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP_NOSTRETCH

; Welcome page
!define MUI_WELCOMEPAGE_TITLE    "Welcome to Cronix Setup"
!define MUI_WELCOMEPAGE_TEXT     "Cronix is a lightweight, privacy-respecting \
browser by Croftonix.$\r$\n$\r$\nThis will install Cronix $\r$\non your computer."

; Finish page
!define MUI_FINISHPAGE_RUN          "$INSTDIR\Cronix.exe"
!define MUI_FINISHPAGE_RUN_TEXT     "Launch Cronix"
!define MUI_FINISHPAGE_LINK         "Visit croftonix on GitHub"
!define MUI_FINISHPAGE_LINK_LOCATION "https://github.com/james15-spec/Cronix-browser"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Installer sections

Section "Cronix (required)" SecMain

  SectionIn RO

  ; Install files from PyInstaller dist folder
  SetOutPath "$INSTDIR"
  File /r "..\dist\Cronix\*.*"

  ; Write install dir to registry
  WriteRegStr HKLM "Software\Croftonix\Cronix" "Install_Dir" "$INSTDIR"

  ; Write uninstall info
  WriteRegStr HKLM \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\Cronix" \
    "DisplayName" "Cronix"
  WriteRegStr HKLM \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\Cronix" \
    "DisplayIcon" "$INSTDIR\Cronix.exe"
  WriteRegStr HKLM \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\Cronix" \
    "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\Cronix" \
    "DisplayVersion" "1.4.4"
  WriteRegStr HKLM \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\Cronix" \
    "Publisher" "Croftonix"
  WriteRegStr HKLM \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\Cronix" \
    "URLInfoAbout" "https://github.com/james15-spec/Cronix-browser"
  WriteRegDWORD HKLM \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\Cronix" \
    "NoModify" 1
  WriteRegDWORD HKLM \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\Cronix" \
    "NoRepair" 1

  WriteUninstaller "$INSTDIR\uninstall.exe"

SectionEnd

Section "Start Menu Shortcuts" SecStartMenu

  CreateDirectory "$SMPROGRAMS\Cronix"
  CreateShortcut "$SMPROGRAMS\Cronix\Cronix.lnk" \
    "$INSTDIR\Cronix.exe" "" "$INSTDIR\Cronix.exe" 0
  CreateShortcut "$SMPROGRAMS\Cronix\Uninstall Cronix.lnk" \
    "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0

SectionEnd

Section "Desktop Shortcut" SecDesktop

  CreateShortcut "$DESKTOP\Cronix.lnk" \
    "$INSTDIR\Cronix.exe" "" "$INSTDIR\Cronix.exe" 0

SectionEnd

;--------------------------------
; Register as default browser capable

Section "Register URL Handler" SecURL

  WriteRegStr HKLM "Software\Clients\StartMenuInternet\Cronix" "" "Cronix"
  WriteRegStr HKLM "Software\Clients\StartMenuInternet\Cronix\shell\open\command" \
    "" '"$INSTDIR\Cronix.exe"'

  ; http
  WriteRegStr HKCR "CronixHTML" "" "Cronix HTML Document"
  WriteRegStr HKCR "CronixHTML\shell\open\command" "" '"$INSTDIR\Cronix.exe" "%1"'

SectionEnd

;--------------------------------
; Uninstaller

Section "Uninstall"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Cronix"
  DeleteRegKey HKLM "Software\Croftonix\Cronix"
  DeleteRegKey HKLM "Software\Clients\StartMenuInternet\Cronix"
  DeleteRegKey HKCR "CronixHTML"

  ; Remove files
  RMDir /r "$INSTDIR"

  ; Remove shortcuts
  Delete "$SMPROGRAMS\Cronix\Cronix.lnk"
  Delete "$SMPROGRAMS\Cronix\Uninstall Cronix.lnk"
  RMDir  "$SMPROGRAMS\Cronix"
  Delete "$DESKTOP\Cronix.lnk"

SectionEnd
