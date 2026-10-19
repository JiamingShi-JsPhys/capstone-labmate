"""Build the Capstone LabMate installer exe and release assets.

Produces:
  * dist/capstone-labmate-installer.exe  -- frozen, bundles the skill payload
  * release/capstone-labmate.zip         -- slim skill-only zip for the
                                         GitHub Release asset (method 2)

Requires a Python install that includes tkinter + PyInstaller.
On this machine use:

    C:/Users/shijiaming/AppData/Local/Programs/Python/Python314/python.exe build_installer.py

Tkinter collection strategy (onefile, Windows):
  1. _tkinter.pyd        (C extension)   -> --collect-submodules=tkinter
  2. tcl86t.dll / tk86t.dll             -> --add-binary  DLLs
  3. tcl/tcl8.6 + tcl/tk8.6 data dirs   -> --add-data  (Tcl scripts, images, etc.)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "capstone-labmate")
ENTRY = os.path.join(HERE, "installer", "installer_gui.py")
DIST = os.path.join(HERE, "dist")
RELEASE = os.path.join(HERE, "release")
BUILD = os.path.join(HERE, "build")
EXE_NAME = "capstone-labmate-installer"

# Files kept out of the published slim zip / install payload.
EXCLUDE = {".git", "__pycache__", ".pytest_cache", "tests", "conftest.py",
           "pyproject.toml", "requirements.txt", "LICENSE"}


def _find_python_with_tk() -> str:
    """Return the Python interpreter to use for building.

    Preference order:
      1. the Python currently running this script (if it has tkinter)
      2. a hard-coded list of known paths on this machine
    """
    import tkinter  # noqa: F401  – verify current interpreter
    return sys.executable


def build_exe() -> str:
    os.makedirs(DIST, exist_ok=True)
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)

    py = _find_python_with_tk()

    # Locate Tcl/Tk data dir and DLLs relative to the build interpreter.
    import tkinter
    tk_pkg = os.path.dirname(tkinter.__file__)          # .../Lib/tkinter
    # tcl data: <prefix>/tcl/tcl8.6 and <prefix>/tcl/tk8.6
    prefix = os.path.dirname(os.path.dirname(tk_pkg))   # .../Lib -> prefix
    tcl_dir = os.path.join(prefix, "tcl", "tcl8.6")
    tk_dir  = os.path.join(prefix, "tcl", "tk8.6")
    dlls    = os.path.join(prefix, "DLLs")

    # Build --add-binary args for each required shared library
    extra_binaries = []
    for dll_name in ("tcl86t.dll", "tk86t.dll", "zlib1.dll"):
        src = os.path.join(dlls, dll_name)
        if os.path.isfile(src):
            extra_binaries.append(f"--add-binary={src}{os.pathsep}DLLs")

    # Tcl/Tk data dirs (Tcl scripts, images, theme files)
    extra_data = []
    for data_dir in (tcl_dir, tk_dir):
        if os.path.isdir(data_dir):
            # tcl8.6 -> bundled under "tcl/tcl8.6" (relative to _MEIPASS root)
            rel = os.path.relpath(data_dir, prefix)   # e.g. "tcl/tcl8.6"
            extra_data.append(f"--add-data={data_dir}{os.pathsep}{rel}")

    cmd = [
        py, "-m", "PyInstaller",
        "--noconfirm", "--onefile", "--windowed",
        f"--name={EXE_NAME}",
        f"--distpath={DIST}",
        f"--workpath={BUILD}",
        f"--add-data={SKILL_DIR}{os.pathsep}_BUNDLED_SKILL",
        # tkinter collection
        "--collect-submodules=tkinter",
        "--collect-binaries=tkinter",
        *extra_binaries,
        *extra_data,
        ENTRY,
    ]

    print(f"Building with: {py}")
    print(f"  Tcl data: {tcl_dir}  (exists={os.path.isdir(tcl_dir)})")
    print(f"  Tk  data: {tk_dir}   (exists={os.path.isdir(tk_dir)})")
    print(f"  DLLs:     {dlls}")

    subprocess.check_call(cmd)
    return os.path.join(DIST, EXE_NAME + ".exe")


def build_skill_zip() -> str:
    os.makedirs(RELEASE, exist_ok=True)
    zip_path = os.path.join(RELEASE, "capstone-labmate.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(SKILL_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE]
            for f in files:
                if f in EXCLUDE:
                    continue
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, HERE)  # capstone-labmate/...
                zf.write(fp, rel)
    return zip_path


if __name__ == "__main__":
    exe = build_exe()
    print("exe built ->", exe)
    zp = build_skill_zip()
    print("skill zip ->", zp)
