import pytest

from imagine import cli


@pytest.fixture
def fitted_png():
    return b"\x89PNG\r\n\x1a\n" + b"\xff" * 8


@pytest.fixture
def fit_calls(fitted_png, monkeypatch):
    """Replace cli.fit_image: write known bytes to dest; magick never invoked."""
    calls = []

    def _fit(src, dest, size=None, max_kb=None, mode=None):
        dest.write_bytes(fitted_png)
        calls.append({"src": src, "dest": dest, "size": size,
                      "max_kb": max_kb, "mode": mode})
        return dest

    monkeypatch.setattr(cli, "fit_image", _fit)
    return calls
