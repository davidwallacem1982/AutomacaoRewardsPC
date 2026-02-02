# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import os
from PyInstaller.utils.hooks import collect_data_files

BASE_DIR = Path(os.getcwd())

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=[
        (str(BASE_DIR / 'app' / 'assets'), 'app/assets'),
    ],
    hiddenimports=[],
    hookspath=[],
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
    [],
    exclude_binaries=True,
    name='AutoRewardsPC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
        console=False,  # False = sem terminal
    icon=str(BASE_DIR / 'app' / 'assets' / 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutoRewardsPC',
)
