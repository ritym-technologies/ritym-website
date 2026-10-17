# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
project_root = Path(r"D:\Projects\MIDI")

added_files = [
    (str(project_root / "src" / "ui"), "src/ui"),
    (str(project_root / "config"), "config"),
    (str(project_root / "docs"), "docs"),
    (str(project_root / "pulsestage.ico"), "."),
]

a = Analysis(
    [str(project_root / "src" / "launcher" / "desktop_app.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.protocols.websockets.websockets_impl",
        "uvicorn.lifespans",
        "uvicorn.lifespans.on",
        "fastapi",
        "starlette",
        "starlette.middleware",
        "starlette.middleware.cors",
        "starlette.staticfiles",
        "starlette.responses",
        "websockets",
        "pydantic",
        "pydantic_core",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "pandas"],
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
    name="PulseStage",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed mode: No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "pulsestage.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PulseStage",
)
