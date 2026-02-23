@echo off
REM Copies Tesseract OCR files into tesseract_bundle/ for PyInstaller packaging.
REM Requires Tesseract-OCR installed at "C:\Program Files\Tesseract-OCR".

set SRC=C:\Program Files\Tesseract-OCR
set DST=%~dp0..\tesseract_bundle

if not exist "%SRC%\tesseract.exe" (
    echo ERROR: Tesseract not found at %SRC%
    echo Install from: https://github.com/UB-Mannheim/tesseract/wiki
    exit /b 1
)

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
