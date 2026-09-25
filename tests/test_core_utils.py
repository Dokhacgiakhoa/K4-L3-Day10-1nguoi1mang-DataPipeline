from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import (
    compact_join,
    ensure_parent,
    first_sentence,
    now_utc,
    read_json,
    safe_slug,
    write_csv,
    write_json,
    write_text,
)


def test_write_and_read_json_round_trip(tmp_path):
    path = tmp_path / "nested" / "file.json"
    write_json(path, {"a": 1, "b": [1, 2, 3]})
    assert read_json(path) == {"a": 1, "b": [1, 2, 3]}


def test_write_json_creates_parent_dirs(tmp_path):
    path = tmp_path / "a" / "b" / "c.json"
    write_json(path, {})
    assert path.exists()


def test_ensure_parent_is_idempotent(tmp_path):
    path = tmp_path / "x" / "y.txt"
    ensure_parent(path)
    ensure_parent(path)
    assert path.parent.exists()


def test_write_csv_creates_file(tmp_path):
    path = tmp_path / "out.csv"
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    write_csv(df, path)
    assert path.exists()
    assert "a,b" in path.read_text(encoding="utf-8")


def test_write_text(tmp_path):
    path = tmp_path / "note.md"
    write_text(path, "hello world")
    assert path.read_text(encoding="utf-8") == "hello world"


def test_now_utc_has_utc_tzinfo():
    now = now_utc()
    assert isinstance(now, datetime)
    assert now.tzinfo is not None


def test_safe_slug_strips_special_chars():
    assert safe_slug("Hello, World!") == "hello-world"


def test_safe_slug_empty_falls_back_to_item():
    assert safe_slug("!!!") == "item"


def test_compact_join_skips_falsy_items():
    assert compact_join(["a", "", None, "b"]) == "a, b"


def test_compact_join_custom_separator():
    assert compact_join(["x", "y"], sep=" | ") == "x | y"


def test_first_sentence_splits_on_punctuation():
    assert first_sentence("First sentence. Second sentence.") == "First sentence."


def test_first_sentence_no_punctuation_returns_whole_text():
    assert first_sentence("just one clause without punctuation") == "just one clause without punctuation"
