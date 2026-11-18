"""Gate tests for the version single-source-of-truth (issue #28).

The real invariant after the fix is structural: the version literals are
*gone*, and the version is *derived* from ``VERSION``. The derivation tests
below assert the derivation stays in place (they are red on a tree that
reintroduces a static literal). The agreement test is a stale-install canary
only: after this refactor ``__version__`` is derived from ``VERSION``, so
agreement is close to true by construction — but a plain ``uv run`` after a
bump without ``uv sync --reinstall-package imagine`` (stale editable install)
will show the old metadata value, which is exactly what this test surfaces.
"""

import re
from pathlib import Path

from imagine import __version__

ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_does_not_hardcode_version():
    pp = (ROOT / "pyproject.toml").read_text()
    assert not re.search(r'(?m)^\s*version\s*=\s*["\']', pp), (
        "pyproject.toml still has a static version literal; "
        "use dynamic = [\"version\"] with the hatchling VERSION source"
    )


def test_package_init_does_not_hardcode_version():
    src = (ROOT / "imagine" / "__init__.py").read_text()
    assert not re.search(r'__version__\s*=\s*["\']\d+\.\d+', src), (
        "__init__.py still has a hard-coded version literal; "
        "derive it from importlib.metadata / VERSION instead"
    )


def test_version_matches_single_source_of_truth():
    # Stale-install canary (see module docstring): not a drift gate — after
    # the #28 refactor the value is derived from this same file.
    assert __version__ == (ROOT / "VERSION").read_text().strip()
