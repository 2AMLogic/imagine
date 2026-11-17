import json
from types import SimpleNamespace

import pytest

from imagine import cli

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 8
WEBP = b"RIFF\x04\x00\x00\x00WEBPVP8 "
JUNK = b"not an image"


def _args(out, n=1, param=None, json_out=False, model="nano-banana", ar=None):
    return SimpleNamespace(
        model=model, ref=None, size=None, param=param, n=n, ar=ar,
        out=out, json=json_out, cf_account=None, no_retry=False,
    )


@pytest.fixture
def run(monkeypatch):
    def _run(out, batches, n=1, param=None, json_out=False, ar=None):
        monkeypatch.setattr(cli.config, "gemini_key", lambda: "fake")
        monkeypatch.setattr(cli.gemini, "generate", lambda *a, **k: list(batches))
        return cli._generate(
            _args(str(out) if out else None, n, param, json_out, ar=ar), "tiny red dot", []
        )
    return _run


@pytest.mark.parametrize(
    "data,fmt", [(PNG, "png"), (JPEG, "jpeg"), (WEBP, "webp"), (JUNK, "unknown"), (b"", "unknown")]
)
def test_sniff(data, fmt):
    assert cli._sniff_format(data) == fmt


def test_jpeg_renamed_with_sidecar(run, tmp_path, capsys):
    run(tmp_path / "out.png", [JPEG])
    cap = capsys.readouterr()
    real = tmp_path / "out.jpg"
    assert cap.out.strip() == str(real)
    assert "provider returned JPEG" in cap.err
    assert real.read_bytes() == JPEG
    assert not (tmp_path / "out.png").exists()
    meta = json.loads((tmp_path / "out.jpg.json").read_text())
    assert meta["format"] == "jpeg" and meta["mime"] == "image/jpeg"
    import hashlib
    assert meta["sha256"] == hashlib.sha256(JPEG).hexdigest()


def test_matching_extension_untouched_but_format_recorded(run, tmp_path, capsys):
    run(tmp_path / "out.png", [PNG])
    cap = capsys.readouterr()
    assert cap.out.strip() == str(tmp_path / "out.png")
    assert cap.err == ""
    meta = json.loads((tmp_path / "out.png.json").read_text())
    assert meta["format"] == "png" and meta["mime"] == "image/png"


def test_uppercase_and_jpeg_aliases(run, tmp_path):
    run(tmp_path / "a.PNG", [PNG])
    assert (tmp_path / "a.PNG").exists()
    run(tmp_path / "b.jpeg", [JPEG])
    assert (tmp_path / "b.jpeg").exists()
    run(tmp_path / "c.PNG", [JPEG])
    assert (tmp_path / "c.jpg").exists()


def test_no_extension_gets_real_one(run, tmp_path):
    run(tmp_path / "out", [WEBP])
    assert (tmp_path / "out.webp").read_bytes() == WEBP


def test_unknown_bytes_keep_requested_extension(run, tmp_path):
    run(tmp_path / "out.png", [JUNK])
    meta = json.loads((tmp_path / "out.png.json").read_text())
    assert meta["format"] == "unknown" and meta["mime"] is None


def test_directory_component_created(run, tmp_path):
    run(tmp_path / "sub" / "dir" / "x.png", [JPEG])
    assert (tmp_path / "sub" / "dir" / "x.jpg.json").exists()


def test_n_naming_uses_per_image_extension(run, tmp_path, capsys):
    run(tmp_path / "out.png", [JPEG, PNG])
    assert (tmp_path / "out-1.jpg").exists()
    assert (tmp_path / "out-2.png").exists()
    assert capsys.readouterr().out.split() == [
        str(tmp_path / "out-1.jpg"), str(tmp_path / "out-2.png")
    ]


# --- params provenance (issue #19) ---

# The sidecar key set before `params` was added; `params` must be additive.
BASE_RECORD_KEYS = {
    "tool", "provider", "model", "alias", "prompt", "refs", "aspect_ratio",
    "size", "format", "mime", "sha256", "created",
}


def _sidecar(tmp_path, name="out.png"):
    return json.loads((tmp_path / f"{name}.json").read_text())


def test_params_recorded_with_json_types(run, tmp_path):
    run(tmp_path / "out.png", [PNG], param=["steps=4", "sampler=euler"])
    meta = _sidecar(tmp_path)
    assert meta["params"] == {"steps": 4, "sampler": "euler"}
    assert isinstance(meta["params"]["steps"], int)
    assert isinstance(meta["params"]["sampler"], str)


def test_params_empty_dict_when_no_flags(run, tmp_path):
    run(tmp_path / "out.png", [PNG])
    meta = _sidecar(tmp_path)
    assert "params" in meta
    assert meta["params"] == {}


def test_params_in_json_record(run, tmp_path, capsys):
    run(tmp_path / "out.png", [PNG], param=["steps=4", "sampler=euler"], json_out=True)
    cap = capsys.readouterr()
    records = json.loads(cap.out)
    assert len(records) == 1
    assert records[0]["params"] == {"steps": 4, "sampler": "euler"}
    assert isinstance(records[0]["params"]["steps"], int)


def test_params_empty_in_json_record(run, tmp_path, capsys):
    run(tmp_path / "out.png", [PNG], json_out=True)
    records = json.loads(capsys.readouterr().out)
    assert records[0]["params"] == {}


# --- --json stdout contract (issue #31) ----------------------------------

# Without --json, stdout is the path stream, untouched by this change:
# test_jpeg_renamed_with_sidecar / test_n_naming_uses_per_image_extension
# assert one path line per image and nothing else.


def test_json_stdout_parses_with_applicability_note(run, tmp_path, capsys):
    """Probe A: --ar 99:1 on a Gemini model; the note goes to stderr only."""
    run(tmp_path / "out.png", [PNG], json_out=True, ar="99:1")
    cap = capsys.readouterr()
    records = json.loads(cap.out)
    assert records[0]["path"] == str(tmp_path / "out.png")
    assert "not a documented aspect ratio" in cap.err


def test_json_stdout_parses_with_format_fallback(run, tmp_path, capsys):
    """Probe B: JPEG bytes for -o out.png; record's path is the real .jpg."""
    run(tmp_path / "out.png", [JPEG], json_out=True)
    cap = capsys.readouterr()
    records = json.loads(cap.out)
    assert records[0]["path"] == str(tmp_path / "out.jpg")
    assert (tmp_path / "out.jpg").read_bytes() == JPEG
    assert "provider returned JPEG" in cap.err


def test_json_stdout_parses_with_bracket_in_path(run, tmp_path, capsys):
    """Probe C: '[' in the path; defeats any slice-from-'[' stderr workaround."""
    run(tmp_path / "c[draft].png", [JPEG], json_out=True)
    cap = capsys.readouterr()
    records = json.loads(cap.out)
    assert records[0]["path"] == str(tmp_path / "c[draft].jpg")
    assert (tmp_path / "c[draft].jpg").exists()


def test_json_n2_is_one_array_of_two_records(run, tmp_path, capsys):
    """--n > 1 with a note: one stderr note per invocation, one stdout array."""
    run(tmp_path / "out.png", [PNG], n=2, json_out=True, ar="99:1")
    cap = capsys.readouterr()
    records = json.loads(cap.out)  # a second array or stray line would fail here
    assert [r["path"] for r in records] == [
        str(tmp_path / "out-1.png"), str(tmp_path / "out-2.png")
    ]
    assert cap.err.count("imagine: note:") == 1


def test_json_unknown_format_record_on_stdout(run, tmp_path, capsys):
    run(tmp_path / "out.png", [JUNK], json_out=True)
    cap = capsys.readouterr()
    records = json.loads(cap.out)
    assert records[0]["path"] == str(tmp_path / "out.png")
    assert records[0]["format"] == "unknown" and records[0]["mime"] is None


def test_edit_json_stdout_parse(tmp_path, capsys, monkeypatch):
    """`edit` routes through _generate, so the stdout contract holds there too."""
    monkeypatch.setattr(cli.config, "gemini_key", lambda: "fake")
    monkeypatch.setattr(cli.gemini, "generate", lambda *a, **k: [PNG])
    (tmp_path / "in.png").write_bytes(PNG)
    args = _args(str(tmp_path / "out.png"), json_out=True, model="nano-banana-pro")
    args.image = str(tmp_path / "in.png")
    args.instruction = "brighten"
    assert cli.cmd_edit(args) == 0
    records = json.loads(capsys.readouterr().out)
    assert records[0]["path"] == str(tmp_path / "out.png")


def test_existing_sidecar_fields_unchanged(run, tmp_path):
    run(tmp_path / "out.png", [PNG])
    assert set(_sidecar(tmp_path)) == BASE_RECORD_KEYS | {"params"}


def test_params_nested_json_values_round_trip(run, tmp_path):
    run(tmp_path / "out.png", [PNG], param=['opts={"a":1}', "sizes=[1,2]"])
    meta = _sidecar(tmp_path)
    assert meta["params"] == {"opts": {"a": 1}, "sizes": [1, 2]}


def test_params_recorded_even_when_provider_never_receives_them(run, tmp_path, monkeypatch):
    """Gemini ignores --param; the sidecar records the request, not the wire payload."""
    seen = {}

    def _capture(*a, **k):
        seen.update(k)
        return [PNG]

    monkeypatch.setattr(cli.config, "gemini_key", lambda: "fake")
    monkeypatch.setattr(cli.gemini, "generate", _capture)
    cli._generate(
        _args(str(tmp_path / "out.png"), param=["steps=4"]), "tiny red dot", []
    )
    assert "params" not in seen
    assert _sidecar(tmp_path)["params"] == {"steps": 4}


def test_params_identical_across_n(run, tmp_path):
    run(tmp_path / "out.png", [PNG], n=2, param=["steps=4"])
    first = _sidecar(tmp_path, "out-1.png")
    second = _sidecar(tmp_path, "out-2.png")
    assert first["params"] == second["params"] == {"steps": 4}


# --- fit provenance sidecar (issue #21) ---

FIT_RECORD_KEYS = {
    "tool", "operation", "size", "max_kb", "mode", "source", "source_sha256",
    "sha256", "created", "source_record",
}


def test_fit_sidecar_fields_with_source_sidecar(fit_calls, fitted_png, tmp_path):
    import hashlib

    src = tmp_path / "photo.png"
    src.write_bytes(PNG)
    src.with_suffix(src.suffix + ".json").write_text(json.dumps({
        "prompt": "a tiny red dot", "provider": "gemini",
        "model": "gemini-2.5-flash-image", "alias": "nano-banana",
        "format": "png", "sha256": "deadbeef",
    }))
    assert cli.main(["fit", str(src), "--size", "320x132",
                     "--max-kb", "30", "--mode", "contain"]) == 0
    meta = json.loads((tmp_path / "photo-fit.png.json").read_text())
    assert set(meta) == FIT_RECORD_KEYS
    assert meta["tool"].startswith("imagine ")
    assert meta["operation"] == "fit"
    assert meta["size"] == "320x132"
    assert meta["max_kb"] == 30
    assert meta["mode"] == "contain"
    assert meta["source"] == str(src)
    assert meta["source_sha256"] == hashlib.sha256(PNG).hexdigest()
    assert meta["sha256"] == hashlib.sha256(fitted_png).hexdigest()
    assert meta["created"]
    assert meta["source_record"] == {
        "prompt": "a tiny red dot", "provider": "gemini",
        "model": "gemini-2.5-flash-image", "alias": "nano-banana",
    }


def test_fit_source_record_none_without_source_sidecar(fit_calls, tmp_path):
    src = tmp_path / "bare.png"
    src.write_bytes(PNG)
    assert cli.main(["fit", str(src), "--size", "320x132"]) == 0
    meta = json.loads((tmp_path / "bare-fit.png.json").read_text())
    assert meta["source_record"] is None


def test_fit_malformed_source_sidecar_degrades_to_null(fit_calls, tmp_path):
    src = tmp_path / "broken.png"
    src.write_bytes(PNG)
    src.with_suffix(src.suffix + ".json").write_text("{not json")
    assert cli.main(["fit", str(src)]) == 0
    meta = json.loads((tmp_path / "broken-fit.png.json").read_text())
    assert meta["source_record"] is None


def test_fit_source_record_missing_keys_are_null(fit_calls, tmp_path):
    src = tmp_path / "partial.png"
    src.write_bytes(PNG)
    src.with_suffix(src.suffix + ".json").write_text(json.dumps({"prompt": "just a prompt"}))
    assert cli.main(["fit", str(src)]) == 0
    meta = json.loads((tmp_path / "partial-fit.png.json").read_text())
    assert meta["source_record"] == {
        "prompt": "just a prompt", "provider": None, "model": None, "alias": None,
    }


def test_fit_explicit_out_sidecar_next_to_dest(fit_calls, fitted_png, tmp_path):
    src = tmp_path / "in.png"
    src.write_bytes(PNG)
    out = tmp_path / "sub" / "dir" / "logo.png"
    out.parent.mkdir(parents=True)
    assert cli.main(["fit", str(src), "-o", str(out)]) == 0
    assert out.read_bytes() == fitted_png
    assert (tmp_path / "sub" / "dir" / "logo.png.json").is_file()


def test_fit_stdout_is_destination_path_only(fit_calls, tmp_path, capsys):
    src = tmp_path / "in.png"
    src.write_bytes(PNG)
    cli.main(["fit", str(src)])
    cap = capsys.readouterr()
    assert cap.out == str(tmp_path / "in-fit.png") + "\n"
    assert cap.err == ""


# --- fit in-place source_sha256 (issue #37) ---


def test_fit_in_place_source_sha256_is_prefit_bytes(fit_calls, fitted_png, tmp_path):
    """-o pointing at the source must record the PRE-fit source hash."""
    import hashlib

    src = tmp_path / "logo.png"
    src.write_bytes(PNG)
    src.with_suffix(src.suffix + ".json").write_text(json.dumps({
        "prompt": "a tiny red dot", "provider": "gemini",
        "model": "gemini-2.5-flash-image", "alias": "nano-banana",
    }))
    assert cli.main(["fit", str(src), "-o", str(src)]) == 0
    assert src.read_bytes() == fitted_png
    meta = json.loads((tmp_path / "logo.png.json").read_text())
    assert meta["source_sha256"] == hashlib.sha256(PNG).hexdigest()
    assert meta["source_sha256"] != hashlib.sha256(fitted_png).hexdigest()
    assert meta["sha256"] == hashlib.sha256(fitted_png).hexdigest()
    assert set(meta) == FIT_RECORD_KEYS
    assert meta["source_record"] == {
        "prompt": "a tiny red dot", "provider": "gemini",
        "model": "gemini-2.5-flash-image", "alias": "nano-banana",
    }


def test_fit_in_place_alias_spelling_records_prefit_hash(fit_calls, fitted_png, tmp_path):
    """-o given as sub/../<name>.png aliases the source; hash must not depend on path comparison."""
    import hashlib

    (tmp_path / "sub").mkdir()
    src = tmp_path / "logo.png"
    src.write_bytes(PNG)
    alias = tmp_path / "sub" / ".." / "logo.png"
    assert cli.main(["fit", str(src), "-o", str(alias)]) == 0
    assert src.read_bytes() == fitted_png
    meta = json.loads((tmp_path / "logo.png.json").read_text())
    assert meta["source_sha256"] == hashlib.sha256(PNG).hexdigest()
    assert meta["source_sha256"] != hashlib.sha256(fitted_png).hexdigest()
    assert meta["sha256"] == hashlib.sha256(fitted_png).hexdigest()
