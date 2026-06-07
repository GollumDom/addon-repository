#!/usr/bin/env python3
"""Synchronise les versions des addons forkés vers leur dernière release GitHub.

Pour chaque addon, on compare la version déclarée dans le fichier de config à la
dernière release du fork correspondant. Si une version plus récente existe, on
bump la config et on préfixe le CHANGELOG (du plus récent au plus ancien) pour
toutes les versions intermédiaires manquantes.

Lancé par .github/workflows/auto_sync.yml. Le commit/push est fait par le
workflow si ce script a modifié des fichiers.
"""
import pathlib
import re
import subprocess
import urllib.request

OTBR_UPSTREAM_CHANGELOG = (
    "https://raw.githubusercontent.com/home-assistant/addons/master/"
    "openthread_border_router/CHANGELOG.md"
)


def vkey(v):
    return tuple(int(x) for x in v.split("."))


def fork_release_tags(repo):
    """Tags de release stables (X.Y.Z...) d'un repo, via gh CLI."""
    out = subprocess.check_output(
        [
            "gh", "release", "list", "--repo", repo,
            "--exclude-pre-releases", "--exclude-drafts",
            "--limit", "200", "--json", "tagName", "--jq", ".[].tagName",
        ],
        text=True,
    )
    return [
        t.strip()
        for t in out.splitlines()
        if re.fullmatch(r"\d+(?:\.\d+)+", t.strip())
    ]


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode()


def parse_sections(text):
    """Map version -> notes depuis un CHANGELOG en '## X.Y.Z'."""
    sections, cur, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\d+(?:\.\d+)+)\s*$", line)
        if m:
            if cur:
                sections[cur] = "\n".join(buf).strip("\n")
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur:
        sections[cur] = "\n".join(buf).strip("\n")
    return sections


def newer_versions(current, tags):
    return sorted({t for t in tags if vkey(t) > vkey(current)}, key=vkey)


def sync_second_core():
    cfg = pathlib.Path("second-core/config.json")
    txt = cfg.read_text()
    current = re.search(r'"version":\s*"([^"]+)"', txt).group(1)
    new = newer_versions(current, fork_release_tags("Smeagolworms4/ha_second_core"))
    if not new:
        print(f"second-core: déjà à jour ({current})")
        return False

    latest = new[-1]
    cfg.write_text(
        re.sub(r'("version":\s*")[^"]+(")', rf"\g<1>{latest}\g<2>", txt, count=1)
    )

    clog = pathlib.Path("second-core/CHANGELOG.md")
    block = "".join(
        f"## {v}\n- Bump Home Assistant Core to {v}\n\n"
        for v in sorted(new, key=vkey, reverse=True)
    )
    clog.write_text(block + clog.read_text())
    print(f"second-core: {current} -> {latest} (+{len(new)})")
    return True


def sync_otbr():
    cfg = pathlib.Path("core_openthread_border_router/config.yaml")
    txt = cfg.read_text()
    current = re.search(r"^version:\s*(\S+)", txt, re.M).group(1)
    repo = "Smeagolworms4/core_openthread_border_router"
    new = newer_versions(current, fork_release_tags(repo))
    if not new:
        print(f"OTBR: déjà à jour ({current})")
        return False

    latest = new[-1]
    cfg.write_text(
        re.sub(r"^version:\s*\S+", f"version: {latest}", txt, count=1, flags=re.M)
    )

    upstream = parse_sections(fetch(OTBR_UPSTREAM_CHANGELOG))
    block = "".join(
        f"## {v}\n{upstream.get(v) or f'- Bump to upstream version {v}'}\n\n"
        for v in sorted(new, key=vkey, reverse=True)
    )

    clog = pathlib.Path("core_openthread_border_router/CHANGELOG.md")
    old = clog.read_text()
    if old.startswith("# Changelog"):
        rest = old.split("\n", 1)[1].lstrip("\n") if "\n" in old else ""
        clog.write_text("# Changelog\n\n" + block + rest)
    else:
        clog.write_text(block + old)
    print(f"OTBR: {current} -> {latest} (+{len(new)})")
    return True


if __name__ == "__main__":
    changed = False
    changed |= sync_second_core()
    changed |= sync_otbr()
    print("CHANGED" if changed else "NOCHANGE")
