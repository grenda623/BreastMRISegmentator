"""Unit tests for the `breast-mri-segment` CLI argparse layer.

The CLI delegates to ``breast_mri_segmentator.api.segment``; we mock that so no
inference (and no GPU / weights) is needed. These tests just pin the argument
parsing and the values forwarded to ``segment``.
"""
from __future__ import annotations

from unittest import mock

import pytest

from breast_mri_segmentator import __version__, cli


def test_version_flag_prints_version_and_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert __version__ in out


def test_missing_required_args_exits_2():
    # argparse exits with code 2 when required -i/-o are absent.
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2


def test_defaults_forwarded_to_segment(tmp_path):
    inp, out = tmp_path / "in", tmp_path / "out"
    with mock.patch.object(cli, "segment", return_value=out) as seg:
        rc = cli.main(["-i", str(inp), "-o", str(out)])
    assert rc == 0
    seg.assert_called_once_with(
        input_dir=str(inp),
        output_dir=str(out),
        from_dicom=False,
        weights_dir=None,
        use_tta=False,
        fold=0,
    )


def test_all_flags_parsed(tmp_path):
    inp, out, weights = tmp_path / "in", tmp_path / "out", tmp_path / "w"
    argv = [
        "-i", str(inp), "-o", str(out),
        "--from-dicom", "--tta",
        "--weights", str(weights),
        "--fold", "2",
    ]
    with mock.patch.object(cli, "segment", return_value=out) as seg:
        rc = cli.main(argv)
    assert rc == 0
    _, kwargs = seg.call_args
    assert kwargs["from_dicom"] is True
    assert kwargs["use_tta"] is True
    assert kwargs["weights_dir"] == str(weights)
    assert kwargs["fold"] == 2


def test_invalid_fold_type_exits_2(tmp_path):
    argv = ["-i", str(tmp_path), "-o", str(tmp_path), "--fold", "notanint"]
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    assert exc.value.code == 2
