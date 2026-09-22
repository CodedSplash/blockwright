@echo off
rem blockwright launcher for Windows.
rem   no arguments            pick sources in the terminal
rem   blockwright.bat "path"  build charts right away
chcp 65001 >nul
setlocal

where py >nul 2>&1
if %errorlevel%==0 goto :havepy
where python >nul 2>&1
if %errorlevel%==0 goto :havepython
echo.
echo   Не найден Python. Установите его с python.org
echo   и отметьте при установке "Add python.exe to PATH".
echo.
pause
exit /b 1

:havepy
set "PY=py -3"
goto :run
:havepython
set "PY=python"

:run
pushd "%~dp0"
%PY% -m blockwright %*
set "RC=%errorlevel%"
popd
if not "%RC%"=="0" pause
endlocal
