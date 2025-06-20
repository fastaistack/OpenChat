# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['openchat.py'],
    pathex=[],
    binaries=[('libmagic/libexpat.1.dylib', 'Frameworks')],
    datas=[('pkg', 'pkg'), ('/Users/xingchenhan/templates', 'docx/templates'), ('/Users/xingchenhan/YOLO', 'resources/models')],
    hiddenimports=['imghdr'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OpenChat',
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
    icon=['icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OpenChat',
)
app = BUNDLE(
    coll,
    name='OpenChat.app',
    icon='icon.icns',
    bundle_identifier='com.example.openchat',
)
