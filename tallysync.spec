# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for TallySync Windows executable.
#
# Build: pyinstaller tallysync.spec
# Output: dist/tallysync/tallysync.exe
#
# Run from the repo root with the .venv active.

import sys
from pathlib import Path

ROOT = Path(".").resolve()

block_cipher = None

a = Analysis(
    ["app/main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Bundle all XML request templates
        ("app/xml/*.xml", "app/xml"),
        # Bundle default config (no secrets)
        ("config.yaml", "."),
    ],
    hiddenimports=[
        # SQLAlchemy dialects used at runtime
        "sqlalchemy.dialects.postgresql",
        "psycopg",
        # APScheduler job stores
        "apscheduler.jobstores.sqlalchemy",
        "apscheduler.triggers.cron",
        "apscheduler.triggers.interval",
        # pywin32 service framework
        "win32serviceutil",
        "win32service",
        "win32event",
        # pydantic v2 validators
        "pydantic_core",
        # lxml
        "lxml.etree",
        # loguru
        "loguru",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy"],
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
    name="tallysync",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version="version_info.txt",
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="tallysync",
)
