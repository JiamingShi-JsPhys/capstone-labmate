# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules

binaries = [('C:/Users/shijiaming/AppData/Local/Programs/Python/Python314/DLLs/tcl86t.dll', 'DLLs'), ('C:/Users/shijiaming/AppData/Local/Programs/Python/Python314/DLLs/tk86t.dll', 'DLLs'), ('C:/Users/shijiaming/AppData/Local/Programs/Python/Python314/DLLs/zlib1.dll', 'DLLs')]
hiddenimports = []
binaries += collect_dynamic_libs('tkinter')
hiddenimports += collect_submodules('tkinter')


a = Analysis(
    ['C:/Users/shijiaming/Desktop/Al-tool/Workbuddy/coding/PASCO/本地仓库/capstone-labmate-main/installer/installer_gui.py'],
    pathex=[],
    binaries=binaries,
    datas=[('C:/Users/shijiaming/Desktop/Al-tool/Workbuddy/coding/PASCO/本地仓库/capstone-labmate-main/capstone-labmate', '_BUNDLED_SKILL'), ('C:/Users/shijiaming/AppData/Local/Programs/Python/Python314/tcl/tcl8.6', 'tcl/tcl8.6'), ('C:/Users/shijiaming/AppData/Local/Programs/Python/Python314/tcl/tk8.6', 'tcl/tk8.6')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='capstone-labmate-installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
