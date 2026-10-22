#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <wchar.h>

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR args, int show)
{
    WCHAR directory[32768], executable[32768], command[65536];
    if (!GetModuleFileNameW(NULL, directory, 32768)) return 1;
    WCHAR *slash = wcsrchr(directory, L'\\');
    if (!slash) return 1;
    *slash = 0;
    if (swprintf(executable, 32768, L"%ls\\runtime\\pythonw.exe", directory) < 0 ||
        swprintf(command, 65536, L"\"%ls\" -I \"%ls\\start-windows.pyw\"", executable, directory) < 0) return 1;
    STARTUPINFOW startup = {sizeof(startup)};
    PROCESS_INFORMATION process = {0};
    if (!CreateProcessW(executable, command, NULL, NULL, FALSE, 0, NULL, directory, &startup, &process)) {
        MessageBoxW(NULL, L"Unable to start the bundled runtime. Please reinstall Salary Motivator.",
                    L"Salary Motivator", MB_OK | MB_ICONERROR);
        return 1;
    }
    CloseHandle(process.hThread);
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD code = 1;
    GetExitCodeProcess(process.hProcess, &code);
    CloseHandle(process.hProcess);
    return (int)code;
}
