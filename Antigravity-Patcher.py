# coding: utf-8
"""Compatibility entry point for the Windows 2.13.0 adaptation."""
from pathlib import Path
from patcher import build, install, DEFAULT_APP, require_closed
if __name__ == '__main__':
    require_closed()
    bundle = Path(__file__).resolve().parent / 'build' / '2.13.0-release'
    if not bundle.exists():
        build(DEFAULT_APP, bundle)
    install(DEFAULT_APP, bundle)
