@echo off
REM Copies Tesseract OCR files into tesseract_bundle/ for PyInstaller packaging.
REM Searches common install locations automatically.

set DST=%~dp0..\tesseract_bundle

REM Try common Tesseract install locations
set SRC=
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    set "SRC=C:\Program Files\Tesseract-OCR"
) else if exist "%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe" (
    set "SRC=%LOCALAPPDATA%\Programs\Tesseract-OCR"
) else if exist "%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe" (
    set "SRC=%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR"
) else if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    set "SRC=C:\Program Files (x86)\Tesseract-OCR"
)

if "%SRC%"=="" (
    echo ERROR: Tesseract not found in common locations:
    echo   - C:\Program Files\Tesseract-OCR
    echo   - %LOCALAPPDATA%\Programs\Tesseract-OCR
    echo   - C:\Program Files ^(x86^)\Tesseract-OCR
    echo.
    echo Install from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Or set SRC manually: set SRC=C:\path\to\Tesseract-OCR
    exit /b 1
)

echo Found Tesseract at: %SRC%

echo Preparing Tesseract bundle...

if exist "%DST%" rmdir /s /q "%DST%"
mkdir "%DST%"
mkdir "%DST%\tessdata"

echo Copying tesseract.exe...
copy "%SRC%\tesseract.exe" "%DST%\" >nul

echo Copying DLLs...
for %%f in ("%SRC%\*.dll") do copy "%%f" "%DST%\" >nul

echo Copying eng.traineddata...
copy "%SRC%\tessdata\eng.traineddata" "%DST%\tessdata\" >nul

echo.
echo Done! Files copied to: %DST%
dir /b "%DST%"
echo.
echo tessdata\:
dir /b "%DST%\tessdata"
