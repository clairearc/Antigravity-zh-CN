# coding: utf-8
"""Restore the marked Windows 2.13.0 patch without deleting official updates."""
from patcher import restore, DEFAULT_APP
if __name__ == '__main__':
    restore(DEFAULT_APP)
