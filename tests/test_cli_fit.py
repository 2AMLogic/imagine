import pytest

from imagine import cli

FITTED_PNG = b"\x89PNG\r\n\x1a\n" + b"\xff" * 8

# Non-PNG sources are the guard: a .png source produces the same destination
# under either naming rule, so it is kept only for completeness.
DEFAULT_DEST_CASES = [
    ("photo.jpg", "photo-fit.png"),
    ("anim.webp", "anim-fit.png"),
    ("noext", "noext-fit.png"),
    ("archive.tar.gz", "archive.tar-fit.png"),
    ("owl.png", "owl-fit.png"),
]


@pytest.fixture
def fit_calls(monkeypatch):
    calls = []

    def _fit(src, dest, size=None, max_kb=None, mode=None):
        dest.write_bytes(FITTED_PNG)
        calls.append({"src": src, "dest": dest, "size": size,
                      "max_kb": max_kb, "mode": mode})
        return dest

    monkeypatch.setattr(cli, "fit_image", _fit)
    return calls


def _make_source(tmp_path, name):
    src = tmp_path / name
    src.write_bytes(b"\x00" * 4)
    return src


@pytest.mark.parametrize("name,expected", DEFAULT_DEST_CASES)
def test_fit_default_dest_forces_png(fit_calls, tmp_path, name, expected):
    src = _make_source(tmp_path, name)
    assert cli.main(["fit", str(src)]) == 0
    assert fit_calls[0]["dest"] == tmp_path / expected


@pytest.mark.parametrize("out", ["out.jpg", "out.webp", "renamed"])
def test_fit_explicit_out_passed_through(fit_calls, tmp_path, out):
    src = _make_source(tmp_path, "photo.jpg")
    dest = tmp_path / out
    assert cli.main(["fit", str(src), "--out", str(dest)]) == 0
    assert fit_calls[0]["dest"] == dest


def test_fit_stdout_is_dest_path_only(fit_calls, tmp_path, capsys):
    src = _make_source(tmp_path, "photo.jpg")
    cli.main(["fit", str(src)])
    assert capsys.readouterr().out == str(tmp_path / "photo-fit.png") + "\n"


def test_fit_flags_reach_fit_image(fit_calls, tmp_path):
    src = _make_source(tmp_path, "photo.jpg")
    cli.main(["fit", str(src), "--size", "320x132", "--max-kb", "64",
              "--mode", "cover"])
    call = fit_calls[0]
    assert call["src"] == src
    assert call["size"] == "320x132"
    assert call["max_kb"] == 64
    assert call["mode"] == "cover"


def test_fit_parser_defaults(fit_calls, tmp_path):
    src = _make_source(tmp_path, "photo.jpg")
    cli.main(["fit", str(src)])
    call = fit_calls[0]
    assert call["size"] is None
    assert call["max_kb"] is None
    assert call["mode"] == "contain"


def test_fit_missing_source_exits_without_calling_fit(fit_calls, tmp_path):
    missing = tmp_path / "gone.jpg"
    with pytest.raises(SystemExit) as ei:
        cli.main(["fit", str(missing)])
    assert str(ei.value) == f"imagine: no such file: {missing}"
    assert fit_calls == []
