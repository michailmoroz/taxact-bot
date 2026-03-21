# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for TaxAct E-File Extension Bot.

Build with:  pyinstaller clickbot.spec --noconfirm
Output:      dist/TaxActBot/TaxActBot.exe
"""

import os
from pathlib import Path

# Locate CustomTkinter package for bundling its theme/font assets
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['clickbot/gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        # CustomTkinter theme/font assets (required for GUI)
        (ctk_path, 'customtkinter/'),

        # App config (bundled as read-only defaults)
        ('config/settings.json', 'config'),
        ('config/processes', 'config/processes'),

        # Button templates for vision module
        ('.agents/screenshots/buttons', '.agents/screenshots/buttons'),

        # Verification screen templates
        ('assets/verify', 'assets/verify'),

        # Tesseract OCR bundle
        ('tesseract_bundle', 'tesseract_bundle'),
    ],
    hiddenimports=[
        'pywintypes',
        'cv2',
        'PIL._tkinter_finder',
        'pydirectinput',
        'clickbot.winkeys',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'notebook',
        'IPython',
        'jupyter',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # onedir mode
    name='TaxActBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid AV false positives
    console=False,  # Windowed mode (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,  # keyboard module needs admin for global hotkeys
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='TaxActBot',
)
