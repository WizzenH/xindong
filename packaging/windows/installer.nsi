Unicode True
!include "MUI2.nsh"
!include "x64.nsh"
Name "薪动 · 上班鼓励器"
OutFile "${OUTPUT_FILE}"
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "Salary Motivator"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "FileDescription" "Salary Motivator Installer"
VIAddVersionKey "LegalCopyright" "2026 WizzenH"
InstallDir "$LOCALAPPDATA\Programs\SalaryMotivator"
InstallDirRegKey HKCU "Software\SalaryMotivator" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
!define MUI_ICON "${APP_ICON}"
!define MUI_UNICON "${APP_ICON}"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\SalaryMotivator.exe"
!define MUI_FINISHPAGE_RUN_TEXT "启动上班鼓励器"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"
Function .onInit
    ${IfNot} ${RunningX64}
        MessageBox MB_ICONSTOP "This package requires 64-bit Windows."
        Abort
    ${EndIf}
FunctionEnd
Section "Install"
    SetShellVarContext current
    SetOutPath "$INSTDIR"
    File /r "${PAYLOAD_DIR}/*"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    CreateDirectory "$SMPROGRAMS\Salary Motivator"
    CreateShortcut "$SMPROGRAMS\Salary Motivator\上班鼓励器.lnk" "$INSTDIR\SalaryMotivator.exe"
    CreateShortcut "$SMPROGRAMS\Salary Motivator\卸载.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortcut "$DESKTOP\上班鼓励器.lnk" "$INSTDIR\SalaryMotivator.exe"
    WriteRegStr HKCU "Software\SalaryMotivator" "InstallDir" "$INSTDIR"
    ; Enable on fresh install; preserve the user's disabled state on upgrades.
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SalaryMotivator" "DisplayVersion"
    ${If} $0 == ""
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "SalaryMotivator" '$\"$INSTDIR\SalaryMotivator.exe$\"'
    ${EndIf}
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SalaryMotivator" "DisplayName" "上班鼓励器"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SalaryMotivator" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SalaryMotivator" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SalaryMotivator" "QuietUninstallString" '$\"$INSTDIR\Uninstall.exe$\" /S'
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SalaryMotivator" "DisplayIcon" "$INSTDIR\SalaryMotivator.exe"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SalaryMotivator" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SalaryMotivator" "NoRepair" 1
SectionEnd
Section "Uninstall"
    SetShellVarContext current
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "SalaryMotivator"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SalaryMotivator"
    DeleteRegKey HKCU "Software\SalaryMotivator"
    Delete "$DESKTOP\上班鼓励器.lnk"
    Delete "$SMPROGRAMS\Salary Motivator\上班鼓励器.lnk"
    Delete "$SMPROGRAMS\Salary Motivator\卸载.lnk"
    RMDir "$SMPROGRAMS\Salary Motivator"
    RMDir /r "$INSTDIR\app\salary_motivator"
    RMDir "$INSTDIR\app"
    Delete "$INSTDIR\LICENSE"
    ; Delete only files owned by this application; preserve personal salary settings.
    RMDir /r "$INSTDIR\runtime"
    Delete "$INSTDIR\salary_model.py"
    Delete "$INSTDIR\startup.py"
    Delete "$INSTDIR\themes.py"
    Delete "$INSTDIR\preferences.py"
    Delete "$INSTDIR\appearance.py"
    Delete "$INSTDIR\tray.py"
    Delete "$INSTDIR\window_chrome.py"
    Delete "$INSTDIR\salary.ico"
    RMDir /r "$INSTDIR\__pycache__"
    Delete "$INSTDIR\salary.py"
    Delete "$INSTDIR\start-windows.pyw"
    Delete "$INSTDIR\SalaryMotivator.exe"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"
SectionEnd
