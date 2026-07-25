from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".toml", ".yaml", ".yml"}
FORBIDDEN = {
    "absolute user path": re.compile(r"/" r"Users/|/" r"home/"),
    "child-specific relation": re.compile(
        r"\b("
        r"my " r"daughter|"
        r"your " r"daughter|"
        r"your " r"child|"
        r"5-" r"year-old|"
        r"ages " r"4[–-]5"
        r")\b",
        re.IGNORECASE,
    ),
    "concrete USB modem identifier": re.compile(r"usbmodem[0-9A-Fa-f]{8,}"),
}


def test_public_tree_has_no_personal_or_machine_specific_copy():
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    failures = []
    for name in tracked:
        path = ROOT / name
        if path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(errors="ignore")
        for label, pattern in FORBIDDEN.items():
            if pattern.search(text):
                failures.append(f"{name}: {label}")
    assert failures == []
