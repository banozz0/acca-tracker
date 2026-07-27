#!/usr/bin/env python3
"""Repo validation for acca-tracker: frontmatter, links, version sync, script
compile + unit tests. Run from anywhere:

    python3 scripts/validate.py
"""
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


# --- SKILL.md frontmatter ---
skill = (ROOT / "SKILL.md").read_text()
check(skill.startswith("---"), "SKILL.md must start with --- frontmatter")
close = skill.find("\n---\n", 3)
check(close != -1, "SKILL.md frontmatter has no closing ---")
fm = skill[4:close] if close != -1 else ""
check("name: acca-tracker" in fm, "frontmatter missing name: acca-tracker")
check("platforms: [linux, macos, windows]" in fm, "frontmatter missing platforms")
check("requires_toolsets: [web, vision, cronjob]" in fm, "frontmatter missing requires_toolsets")
check(len(skill) <= 100_000, "SKILL.md over 100k chars")
desc = re.search(r'description: "?(Use when [^"\n]+)', fm)
check(bool(desc), 'frontmatter description must start with "Use when ..."')

# --- version sync SKILL.md <-> README.md ---
v_skill = re.search(r"^version: (\S+)$", fm, re.M)
v_readme = re.search(r"^Version: (\S+)$", (ROOT / "README.md").read_text(), re.M)
check(bool(v_skill) and bool(v_readme) and v_skill.group(1) == v_readme.group(1),
      f"version mismatch: SKILL.md={v_skill and v_skill.group(1)} README.md={v_readme and v_readme.group(1)}")

# --- no runtime state dir ---
check(not (ROOT / "state").exists(), "state/ must not exist in the skill directory")

# --- relative markdown links resolve ---
for md in ROOT.rglob("*.md"):
    if ".git" in md.parts:
        continue
    for m in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", md.read_text()):
        target = m.group(1)
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        rel = target.split("#")[0]
        if rel and not (md.parent / rel).resolve().exists():
            errors.append(f"broken link in {md.relative_to(ROOT)}: {target}")

# --- script compiles + unit tests pass ---
try:
    py_compile.compile(str(ROOT / "scripts" / "fetch-scores.py"), doraise=True,
                       cfile=str(Path(tempfile.mkdtemp()) / "fetch-scores.pyc"))
except py_compile.PyCompileError as e:
    errors.append(f"fetch-scores.py does not compile: {e}")
r = subprocess.run([sys.executable, str(ROOT / "scripts" / "test_fetch_scores.py")],
                   capture_output=True, text=True)
check(r.returncode == 0, f"unit tests failed:\n{r.stderr[-2000:]}")

if errors:
    print("FAIL")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"OK {ROOT} (version {v_skill.group(1) if v_skill else '?'})")
