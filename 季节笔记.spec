# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('seasonal_notes/assets', 'seasonal_notes/assets')],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='季节笔记',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['季节笔记.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='季节笔记',
)
app = BUNDLE(
    coll,
    name='季节笔记.app',
    icon='季节笔记.icns',
    bundle_identifier='com.paofu.seasonalnotes',
    info_plist={
        'CFBundleDisplayName': '季节笔记',
        'CFBundleName': '季节笔记',
        'CFBundleShortVersionString': '0.6.0',
        'CFBundleVersion': '6',
        'LSApplicationCategoryType': 'public.app-category.productivity',
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Copyright © 2026 paofu76. All rights reserved.',
    },
)
