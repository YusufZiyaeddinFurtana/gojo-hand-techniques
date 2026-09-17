@echo off
setlocal
set "PYTHONUTF8=1"
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\launch.py %*
  goto finish
)
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
  py -3.12 scripts\launch.py %*
  goto finish
)
python --version >nul 2>&1
if not errorlevel 1 (
  python scripts\launch.py %*
  goto finish
)
echo Python bulunamadi. https://www.python.org/downloads/windows/
echo Python 3.12 64-bit kurun ve "Add python.exe to PATH" secenegini acin.
pause
exit /b 1
:finish
set "GOJO_EXIT=%errorlevel%"
if not "%GOJO_EXIT%"=="0" (
  echo Baslatilamadi. Yukaridaki hata mesajini kontrol edin.
  pause
)
exit /b %GOJO_EXIT%
