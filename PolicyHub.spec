# -*- mode: python ; coding: utf-8 -*-
"""
PolicyHub PyInstaller Specification File

Builds PolicyHub into a single Windows executable using PySide6.

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

# PySide6 data files path
import PySide6
pyside6_path = Path(PySide6.__file__).parent

# Build data files list
datas = [
    # PySide6 plugins
    (str(pyside6_path / 'plugins' / 'platforms'), 'PySide6/plugins/platforms'),
    (str(pyside6_path / 'plugins' / 'styles'), 'PySide6/plugins/styles'),
    (str(pyside6_path / 'plugins' / 'imageformats'), 'PySide6/plugins/imageformats'),
]

# Add resources/styles if it exists
resources_styles = project_root / 'resources' / 'styles'
if resources_styles.exists():
    datas.append((str(resources_styles), 'resources/styles'))

# Hidden imports for dynamic modules
hiddenimports = [
    # PySide6 core modules
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    # Database and security
    'bcrypt',
    # Reporting
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.colors',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.lib.units',
    'reportlab.platypus',
    'reportlab.platypus.doctemplate',
    'reportlab.platypus.paragraph',
    'reportlab.platypus.tables',
    'reportlab.platypus.flowables',
    'reportlab.graphics',
    # Excel
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',
    'openpyxl.workbook',
    'openpyxl.worksheet',
    # Image processing
    'PIL',
    'PIL.Image',
]

# Binaries - PySide6 Qt DLLs
binaries = []

# Collect all Qt DLLs
qt_dlls = pyside6_path.glob('*.dll')
for dll in qt_dlls:
    binaries.append((str(dll), '.'))

# Analysis configuration
a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=binaries,
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
        'tkinter',
        'customtkinter',
        'tksheet',
        'tkcalendar',
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
    icon=None,  # Add icon path if you have one: 'resources/icon.ico'
    version=None,  # Add version file if you have one: 'version_info.txt'
)
