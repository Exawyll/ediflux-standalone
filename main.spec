# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

# Include frontend and templates directories
datas = [
    ('frontend', 'frontend'),
    ('templates', 'templates'),
]

# Collect GTK3 DLLs for WeasyPrint if on Windows
binaries = []
if sys.platform == 'win32':
    gtk_dirs = [
        os.environ.get('GTK_FOLDER'),
        r'C:\Program Files\GTK3-Runtime Win64\bin',
        r'C:\Program Files (x86)\GTK3-Runtime Win64\bin',
        r'C:\gtk\bin',
    ]
    
    gtk_bin_path = None
    for d in gtk_dirs:
        if d and os.path.exists(d):
            gtk_bin_path = d
            break
            
    if gtk_bin_path:
        print(f"Found GTK3 at: {gtk_bin_path}")
        for filename in os.listdir(gtk_bin_path):
            if filename.endswith('.dll'):
                # Bundle into the top-level directory of the exe ('.' means root of bundle)
                binaries.append((os.path.join(gtk_bin_path, filename), '.'))
    else:
        print("WARNING: GTK3 bin path not found. WeasyPrint may fail.")

# Uvicorn and other hidden imports
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',
    'pydantic',
    'weasyprint', 
]

# Handling imports for python-multipart if used
try:
    import python_multipart
    hiddenimports.append('python_multipart')
except ImportError:
    pass

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='factur-x-generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
