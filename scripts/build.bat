@echo off
REM Build TaxActBot executable using PyInstaller.
REM Run from project root: scripts\build.bat

cd /d "%~dp0.."

echo === Building TaxActBot ===
echo.

echo Step 1: Checking tesseract_bundle...
if not exist "tesseract_bundle\tesseract.exe" (
    echo ERROR: tesseract_bundle not found.
    echo Run scripts\prepare_tesseract.bat first.
    exit /b 1
)
echo   OK
echo.

echo Step 2: Cleaning previous build...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo   OK
echo.

echo Step 3: Running PyInstaller...
pyinstaller clickbot.spec --noconfirm
if errorlevel 1 (
    echo.
    echo FAILED: PyInstaller build failed.
    exit /b 1
)
echo.

echo Step 4: Verifying output...
if exist "dist\TaxActBot\TaxActBot.exe" (
    echo.
    echo ============================================
    echo   SUCCESS: dist\TaxActBot\TaxActBot.exe
    echo ============================================
    echo.
    echo To test: dist\TaxActBot\TaxActBot.exe
    echo To create installer: compile installer\taxactbot.iss with Inno Setup
) else (
    echo FAILED: TaxActBot.exe not found in dist\TaxActBot\
    exit /b 1
)
