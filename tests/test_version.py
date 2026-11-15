from pathlib import Path

from imagine import __version__

ROOT = Path(__file__).resolve().parent.parent


def test_version_matches_single_source_of_truth():
    assert __version__ == (ROOT / "VERSION").read_text().strip()
