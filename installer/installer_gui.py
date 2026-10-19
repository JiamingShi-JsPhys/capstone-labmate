"""Tkinter GUI for the Capstone LabMate installer.

Run directly (``python installer/installer_gui.py``) for development, or frozen
into ``capstone-labmate-installer.exe`` via ``build_installer.py``. The skill is
discovered at runtime from either the frozen bundle or the source tree.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading

SELF_DIR = os.path.dirname(os.path.abspath(__file__))
if SELF_DIR not in sys.path:
    sys.path.insert(0, SELF_DIR)

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import installer_core as core

BUNDLE = core.bundled_skill_root()
META = core.read_skill_meta(BUNDLE)


def _self_check() -> int:
    """Headless tkinter sanity check (used by --check)."""
    try:
        r = tk.Tk()
        r.withdraw()
        r.destroy()
        print("tkinter self-check OK")
        return 0
    except Exception as exc:  # pragma: no cover - needs a display
        print(f"self-check FAILED: {exc}")
        return 1


def _self_test() -> int:
    """Write a frozen-bundle diagnostic to a temp file (windowed-safe).

    Verifies that the bundled skill payload resolves correctly once the exe is
    frozen. Results are written to %TEMP%/clm_selftest.txt so they survive the
    --windowed build (no console).
    """
    try:
        r = tk.Tk()
        r.withdraw()
        r.destroy()
        tkinter_ok = True
    except Exception:  # pragma: no cover - needs a display
        tkinter_ok = False
    info = {
        "bundled_skill_root": BUNDLE,
        "skill_md_present": os.path.isfile(os.path.join(BUNDLE, "SKILL.md")),
        "meta_title": META.title,
        "frameworks": META.frameworks,
        "tkinter_ok": tkinter_ok,
    }
    out = os.path.join(tempfile.gettempdir(), "clm_selftest.txt")
    with open(out, "w", encoding="utf-8") as fh:
        for k, v in info.items():
            fh.write(f"{k}: {v}\n")
    try:
        print(json.dumps(info, ensure_ascii=False))
    except Exception:
        pass
    return 0


class InstallerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Capstone LabMate Installer")
        root.geometry("640x720")
        root.minsize(580, 660)
        root.resizable(True, True)
        self.fw_vars: dict[str, tk.BooleanVar] = {}
        self.scope_var = tk.StringVar(value="user")
        self.project_dir = tk.StringVar(value="")
        self._build_ui()

    # ----- UI construction -------------------------------------------------
    def _build_ui(self) -> None:
        band = tk.Frame(self.root, bg="#1f2d3d", padx=18, pady=14)
        band.pack(fill="x")
        tk.Label(band, text=META.title, bg="#1f2d3d", fg="white",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(band, text="Capstone LabMate · PASCO lab companion",
                 bg="#1f2d3d", fg="#aab7c4",
                 font=("Segoe UI", 10)).pack(anchor="w")

        body = tk.Frame(self.root, padx=18, pady=14)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Install into the following AI hosts (select one or more):",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(4, 6))
        fw_frame = tk.Frame(body)
        fw_frame.pack(fill="x", padx=8)
        for key in ("claude", "dsh", "codex", "workbuddy"):
            var = tk.BooleanVar(value=False)
            self.fw_vars[key] = var
            tk.Checkbutton(fw_frame, text=core.FRAMEWORK_LABELS[key],
                           variable=var, font=("Segoe UI", 10)).pack(
                               anchor="w", pady=2)

        tk.Label(body, text="Installation scope:", font=("Segoe UI", 11, "bold")
                 ).pack(anchor="w", pady=(12, 4))
        scope_frame = tk.Frame(body)
        scope_frame.pack(fill="x", padx=8)
        tk.Radiobutton(scope_frame, text="User-level (available across all projects)",
                       variable=self.scope_var, value="user",
                       font=("Segoe UI", 10),
                       command=self._on_scope_change).pack(anchor="w", pady=2)
        tk.Radiobutton(scope_frame, text="Project-level (current task folder only)",
                       variable=self.scope_var, value="project",
                       font=("Segoe UI", 10),
                       command=self._on_scope_change).pack(anchor="w", pady=2)

        self.proj_row = tk.Frame(body)
        self.proj_entry = tk.Entry(self.proj_row, textvariable=self.project_dir,
                                   font=("Segoe UI", 9))
        self.proj_entry.pack(side="left", fill="x", expand=True)
        tk.Button(self.proj_row, text="Browse...", command=self._browse
                  ).pack(side="right", padx=(6, 0))

        note = ("Note: optional dependencies (numpy / matplotlib / pypdf) degrade "
                "gracefully when missing — installation and core operation are unaffected.")
        tk.Label(body, text=note, fg="#666666", font=("Segoe UI", 9),
                 wraplength=560, justify="left").pack(anchor="w", pady=(10, 4))

        tk.Button(body, text="Install", font=("Segoe UI", 11, "bold"),
                  bg="#2e7d32", fg="white", height=1,
                  command=self._on_install).pack(fill="x", pady=(4, 8))

        log_frame = tk.LabelFrame(body, text="Installation Log", padx=6, pady=6)
        log_frame.pack(fill="both", expand=True)
        self.log = scrolledtext.ScrolledText(log_frame, height=10,
                                             font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        self._on_scope_change()

    # ----- callbacks --------------------------------------------------------
    def _on_scope_change(self) -> None:
        if self.scope_var.get() == "project":
            self.proj_row.pack(fill="x", padx=8, pady=(2, 0))
        else:
            self.proj_row.pack_forget()

    def _browse(self) -> None:
        d = filedialog.askdirectory(title="Select task folder")
        if d:
            self.project_dir.set(d)

    def _log(self, line: str) -> None:
        self.log.insert("end", line + "\n")
        self.log.see("end")

    def _on_install(self) -> None:
        selected = [k for k, v in self.fw_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("No host selected", "Please select at least one AI host.")
            return
        scope = self.scope_var.get()
        proj = self.project_dir.get().strip() if scope == "project" else None
        if scope == "project" and not proj:
            messagebox.showwarning("No folder selected",
                                   "Project-level install requires a task folder.")
            return
        self._log(f"Source: {BUNDLE}")
        self._log(f"Scope: {scope}" + (f" -> {proj}" if proj else ""))
        self._log("Hosts: " +
                  ", ".join(core.FRAMEWORK_LABELS[f] for f in selected))
        self._log("")
        threading.Thread(target=self._run_install, args=(selected, scope, proj),
                        daemon=True).start()

    def _run_install(self, selected, scope, proj) -> None:
        try:
            installed, skipped, logs = core.install_skill(
                BUNDLE, selected, scope=scope, project_dir=proj, force=False)
            lines = logs + [f"Done: {installed} installed, {skipped} skipped."]
            self.root.after(0, lambda: [self._log(l) for l in lines])
            if installed:
                self.root.after(
                    0, lambda: messagebox.showinfo(
                        "Installation complete",
                        f"Installed into {installed} host(s); {skipped} skipped."))
        except Exception as exc:  # noqa: BLE001
            self.root.after(0, lambda: self._log(f"Error: {exc}"))


def main() -> None:
    args = sys.argv[1:]
    if "--version" in args or "-v" in args:
        print(META.title)
        return
    if "--check" in args:
        sys.exit(_self_check())
    if "--selftest" in args:
        sys.exit(_self_test())
    InstallerApp(tk.Tk()).root.mainloop()


if __name__ == "__main__":
    main()
