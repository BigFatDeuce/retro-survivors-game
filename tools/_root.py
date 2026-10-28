"""Paths shared by every tool (see tools/README.md).
ROOT = the project root (the folder holding game/, tools/, work/, raw/); override it with the RS_ROOT environment variable.
Importing this module also puts every tools/ folder on sys.path, so a tool imports any other one by its bare name
(`import swflib`, `import build_icons20 as B`, `import patch_091`) wherever the two live. A tool in a sub-folder starts with:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/
    import _root          (or: from _root import ROOT)"""
import os, sys
TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = (os.environ.get('RS_ROOT') or os.path.dirname(TOOLS)).replace('\\', '/')
FOLDERS = ('lib', 'content', 'assets', 'research', 'checks')
for _d in FOLDERS:
    _p = os.path.join(TOOLS, _d)
    if _p not in sys.path: sys.path.append(_p)
RAW = f'{ROOT}/raw/rc'   # the Dofus Retro 1.41.9 client's files, copied into the repository (most builders read these)
# the up-to-date official client as installed by the Ankama launcher (60-fps sprites, newer skins, sounds): read in place
CLIENT = (os.environ.get('RS_NEWCLIENT') or os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Ankama', 'Retro', 'resources', 'app', 'retroclient')).replace('\\', '/')
