# Profile Install and Hardening Notes

Use this reference when refreshing or reinstalling `acca-tracker` from its source repository into a Hermes profile.

## Profile-safe install

Install into the active profile's skill tree, not the default/global skill directory unless that is explicitly intended.

```bash
# Run from the skill's source directory (a clone or download of acca-tracker).
PROFILE=default   # change to your Hermes profile name
mkdir -p ~/.hermes/profiles/"$PROFILE"/skills/acca-tracker
rsync -a --delete --exclude '.git' ./ \
  ~/.hermes/profiles/"$PROFILE"/skills/acca-tracker/
```

Copy the whole skill directory, not only `SKILL.md`; the skill relies on `docs/`, `knowledge/`, `workflows/`, `templates/`, `examples/`, and `references/`.

Start a fresh Hermes session or `/reset` after installing because skill loading is session-cached.

## Pre-install hardening checklist

Before installing or updating the profile copy, run `python3 scripts/validate.py` in the source repo (frontmatter, links, version sync, and the score-fetcher unit tests), then confirm:

- Frontmatter starts at byte 0 with `---` and has a closing `---` block.
- `name`, `description`, `version`, `author`, `license`, `platforms`, and `metadata.hermes.tags` are present.
- Description starts with `Use when ...` and is under 1024 characters.
- `metadata.hermes.requires_toolsets` includes `[web, vision, cronjob]`.
- No runtime/user betting state lives in the skill directory; templates belong in `templates/`, not `state/`.
- Overall status taxonomy is canonical: `WON | LIVE | PARTIAL | PENDING | DEAD | UNVERIFIABLE`.
- `TRACKING COMPLETE` is allowed only when all legs are terminal/settled, the user stops tracking, or Hermes explicitly says this is the final/max-repeat run.
- Lookup failure, blocked sources, unverifiable legs, or guessed wall-clock expiry must not complete tracking.
- Cron prompts omit stake, return, balances, ticket/account identifiers, QR/barcodes, payment details, and odds unless explicitly requested for display.
- Recurring updates carry no boundary footer and respect the script's `CHANGE SINCE LAST RUN` line (`NO` -> `[SILENT]`); cron schedules are never tighter than `*/15`.
- Underage or illegal gambling signals cause refusal/stop-tracking guidance, not continued betting tracking.

## Validation probe

```bash
set -e
# Validates the installed copy. Optionally also validates a source clone if SRC is set.
PROFILE="${PROFILE:-default}"
INST="${INST:-$HOME/.hermes/profiles/$PROFILE/skills/acca-tracker}"
SRC="${SRC:-}"
python3 - "$INST" "$SRC" <<'PY'
import sys, re
from pathlib import Path
roots=[Path(sys.argv[1])]
if len(sys.argv) > 2 and sys.argv[2] and Path(sys.argv[2]).exists():
    roots.append(Path(sys.argv[2]))
for root in roots:
    s=(root/'SKILL.md').read_text()
    assert s.startswith('---')
    close=s.find('\n---\n',3)
    assert close != -1
    fm=s[4:close]
    assert 'name: acca-tracker' in fm
    assert 'platforms: [linux, macos, windows]' in fm
    assert 'requires_toolsets: [web, vision, cronjob]' in fm
    assert len(s) <= 100_000
    assert not (root/'state').exists()
    missing=[]
    for md in root.rglob('*.md'):
        text=md.read_text()
        for match in re.finditer(r'\[[^\]]+\]\(([^)]+)\)', text):
            target=match.group(1)
            if target.startswith(('http://','https://','#','mailto:')): continue
            rel=target.split('#')[0]
            if rel and not (md.parent/rel).resolve().exists():
                missing.append((str(md.relative_to(root)), target))
    assert not missing, missing
    print('OK', root)
PY
hermes --profile "$PROFILE" skills list | grep -i 'acca-tracker'
```
