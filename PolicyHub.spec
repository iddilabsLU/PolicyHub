# -*- mode: python ; coding: utf-8 -*-
"""
PolicyHub PyInstaller Specification File

Builds PolicyHub into a single Windows executable.

Usage:
    pyinstaller PolicyHub.spec

Or use the build.bat script:
    build.bat
"""

import os
import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH).resolve()

# CustomTkinter data files path
import customtkinter
ctk_path = Path(customtkinter.__file__).parent

# tksheet data files (if any)
try:
    import tksheet
    tksheet_path = Path(tksheet.__file__).parent
except ImportError:
    tksheet_path = None

# tkcalendar data files
try:
    import tkcalendar
    tkcal_path = Path(tkcalendar.__file__).parent
    import babel
    babel_path = Path(babel.__file__).parent
except ImportError:
    tkcal_path = None
    babel_path = None

# Build data files list
datas = [
    # CustomTkinter assets
    (str(ctk_path), 'customtkinter'),
]

# Add tksheet if available
if tksheet_path:
    datas.append((str(tksheet_path), 'tksheet'))

# Add tkcalendar and babel if available
if tkcal_path:
    datas.append((str(tkcal_path), 'tkcalendar'))
if babel_path:
    datas.append((str(babel_path / 'locale-data'), 'babel/locale-data'))
    datas.append((str(babel_path / 'global.dat'), 'babel'))

# Hidden imports for dynamic modules
hiddenimports = [
    'customtkinter',
    'tksheet',
    'tkcalendar',
    'babel',
    'babel.numbers',
    'babel.dates',
    'bcrypt',
    'reportlab',
    'reportlab.lib',
    'reportlab.platypus',
    'reportlab.graphics',
    'openpyxl',
    'openpyxl.styles',
    'PIL',
    'PIL._tkinter_finder',
]

# Analysis configuration
a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Bundle configuration
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PolicyHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if you have one: 'assets/icon.ico'
    version=None,  # Add version file if you have one: 'version_info.txt'
)
