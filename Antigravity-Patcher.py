# coding: utf-8
"""Compatibility entry point for the Windows adaptation."""
from pathlib import Path
from patcher import build, install, DEFAULT_APP, require_closed, VERSION
if __name__ == '__main__':
    require_closed()
    bundle = Path(__file__).resolve().parent / 'build' / f'{VERSION}-release'
    if not bundle.exists():
        build(DEFAULT_APP, bundle)
    install(DEFAULT_APP, bundle)
