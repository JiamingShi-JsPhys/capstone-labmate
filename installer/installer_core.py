"""Installer core for Capstone LabMate (single bundled skill).

Pure standard-library implementation so the frozen exe has no third-party
runtime dependencies. The skill payload is bundled at build time under
``_BUNDLED_SKILL``; when run from source it is discovered next to this file.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Framework registry
# ---------------------------------------------------------------------------
FRAMEWORK_LABELS: Dict[str, str] = {
    "workbuddy": "WorkBuddy",
    "claude": "Claude Code",
    "codex": "OpenAI Codex",
    "dsh": "DeepSeek Harness",
}
USER_ROOTS: Dict[str, str] = {
    "workbuddy": ".workbuddy/skills",
    "claude": ".claude/skills",
    "codex": ".codex/skills",
    "dsh": ".dsh/skills",
}
PROJECT_ROOTS: Dict[str, str] = {
    "workbuddy": ".workbuddy/skills",
    "claude": ".claude/skills",
    "codex": ".agents/skills",
    "dsh": ".dsh/skills",
}

# Slim install: only these entries are copied into every host's skills folder.
# A skill missing from this table is copied whole (forward-compatible default).
INSTALL_MANIFEST: Dict[str, List[str]] = {
    "capstone-labmate": ["SKILL.md", "skill.json", "scripts", "config", "templates", "assets"],
}


@dataclass
class SkillMeta:
    name: str
    version: str
    author: str = ""
    license: str = ""
    description: str = ""
    summary_line: str = ""
    entry_point: str = ""
    frameworks: List[str] = field(default_factory=list)
    dependencies: dict = field(default_factory=dict)

    @property
    def title(self) -> str:
        return f"{self.name}  v{self.version}"


def bundled_skill_root() -> str:
    """Return the absolute path of the capstone-labmate skill directory."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        container = os.path.join(meipass, "_BUNDLED_SKILL")
        if os.path.isfile(os.path.join(container, "SKILL.md")):
            return container
        # Drill down one level in case the bundle nested the skill folder.
        if os.path.isdir(container):
            for name in sorted(os.listdir(container)):
                sub = os.path.join(container, name)
                if os.path.isdir(sub) and os.path.isfile(os.path.join(sub, "SKILL.md")):
                    return sub
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (
        os.path.join(here, "..", "capstone-labmate"),
        os.path.join(here, "capstone-labmate"),
        os.path.join(os.getcwd(), "capstone-labmate"),
    ):
        if os.path.isfile(os.path.join(cand, "SKILL.md")):
            return os.path.abspath(cand)
    raise RuntimeError("Could not locate the bundled capstone-labmate skill.")


def read_skill_meta(skill_dir: str) -> SkillMeta:
    """Read name/version from SKILL.md frontmatter and skill.json."""
    skill_dir = os.path.abspath(skill_dir)
    name = os.path.basename(skill_dir.rstrip(os.sep))
    version = "1.0.0-beta"
    description = ""
    author = ""
    license_ = ""
    entry = ""
    fw: List[str] = []
    deps: dict = {}
    md = os.path.join(skill_dir, "SKILL.md")
    if os.path.isfile(md):
        with open(md, "r", encoding="utf-8") as fh:
            text = fh.read()
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1]
                for line in fm.splitlines():
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip()
                    elif line.startswith("version:"):
                        version = line.split(":", 1)[1].strip()
                    elif line.startswith("description:"):
                        description = line.split(":", 1)[1].strip()
                    elif line.startswith("author:"):
                        author = line.split(":", 1)[1].strip()
                    elif line.startswith("license:"):
                        license_ = line.split(":", 1)[1].strip()
                    elif line.startswith("entry:"):
                        entry = line.split(":", 1)[1].strip()
    sj = os.path.join(skill_dir, "skill.json")
    if os.path.isfile(sj):
        try:
            data = json.loads(Path(sj).read_text(encoding="utf-8"))
            name = data.get("name", name)
            version = data.get("version", version)
            author = data.get("author", author)
            license_ = data.get("license", license_)
            entry = data.get("entry", entry)
            fw = data.get("platforms", fw)
            deps = data.get("dependencies", {})
            if not description and data.get("description"):
                description = data["description"]
        except Exception:
            pass
    summary = description.split(".", 1)[0] if description else ""
    return SkillMeta(
        name=name, version=version, author=author, license=license_,
        description=description, summary_line=summary, entry_point=entry,
        frameworks=fw, dependencies=deps,
    )


def resolve_target_root(framework: str, scope: str,
                        project_dir: Optional[str]) -> str:
    if scope == "user":
        base = os.path.expanduser("~")
        return os.path.join(base, USER_ROOTS[framework])
    proj = project_dir or os.getcwd()
    return os.path.join(proj, PROJECT_ROOTS[framework])


def expected_installed_files(skill_dir: str,
                             manifest: Optional[List[str]]) -> List[str]:
    out: List[str] = []
    if not manifest:
        for root, _, files in os.walk(skill_dir):
            for f in files:
                out.append(os.path.relpath(os.path.join(root, f), skill_dir))
        return out
    for rel in manifest:
        item = os.path.join(skill_dir, rel)
        if os.path.isdir(item):
            for r, _, fs in os.walk(item):
                for f in fs:
                    out.append(os.path.relpath(os.path.join(r, f), skill_dir))
        elif os.path.isfile(item):
            out.append(rel)
    return sorted(set(out))


def install_skill(src_root: str, frameworks: List[str], scope: str = "user",
                  project_dir: Optional[str] = None,
                  force: bool = False) -> Tuple[int, int, List[str]]:
    """Install the bundled skill into each selected framework.

    Returns (installed, skipped, log_lines).
    """
    meta = read_skill_meta(src_root)
    manifest = INSTALL_MANIFEST.get(meta.name)
    logs: List[str] = []
    installed = 0
    skipped = 0
    for fw in frameworks:
        if fw not in FRAMEWORK_LABELS:
            logs.append(f"SKIP  unknown framework '{fw}'")
            continue
        label = FRAMEWORK_LABELS[fw]
        target_root = resolve_target_root(fw, scope, project_dir)
        dst = os.path.join(target_root, meta.name)
        if os.path.exists(dst):
            if force:
                shutil.rmtree(dst)
                logs.append(f"FORCE removed existing {dst}")
            else:
                logs.append(
                    f"SKIP  {meta.name} -> {label} (already exists; use Force)")
                skipped += 1
                continue
        os.makedirs(target_root, exist_ok=True)
        os.makedirs(dst, exist_ok=True)
        ok = True
        if manifest:
            for rel in manifest:
                item = os.path.join(src_root, rel)
                if not os.path.exists(item):
                    logs.append(
                        f"FAIL  {meta.name} -> {label}: "
                        f"manifest entry missing: {rel}")
                    ok = False
                    break
                dest = os.path.join(dst, rel)
                if os.path.isdir(item):
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
        else:
            shutil.copytree(src_root, dst)
        if ok and os.path.isfile(os.path.join(dst, "SKILL.md")):
            logs.append(f"OK    {meta.name} -> {label}")
            logs.append(f"      {dst}")
            installed += 1
        else:
            logs.append(f"FAIL  {meta.name} -> {label}: verification failed")
    return installed, skipped, logs


if __name__ == "__main__":
    root = bundled_skill_root()
    m = read_skill_meta(root)
    print(m.title)
    print("bundle:", root)
    print("frameworks:", m.frameworks)
