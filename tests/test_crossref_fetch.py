from __future__ import annotations

from dataclasses import replace
import json

import pytest

from ingestion.crossref import fetch_source_records


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, raise_json_error: bool = False):
        self.status_code = status_code
        self._payload = payload or {}
        self._raise_json_error = raise_json_error

    def json(self):
        if self._raise_json_error:
            raise ValueError("invalid json")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"status {self.status_code}")


def _isolated(base_settings, tmp_path):
    paths = replace(
        base_settings.paths,
        raw_api_response=tmp_path / "crossref_response.json",
        raw_records_json=tmp_path / "crossref_records.json",
    )
    return replace(base_settings, paths=paths)


def test_fetch_success_on_first_try(monkeypatch, base_settings, tmp_path, sample_crossref_payload):
    settings = _isolated(base_settings, tmp_path)
    calls = []

    def fake_get(*args, **kwargs):
        calls.append(1)
        return _FakeResponse(200, sample_crossref_payload)

    monkeypatch.setattr("requests.get", fake_get)

    records = fetch_source_records(settings)

    assert len(calls) == 1
    assert len(records) == 1  # 1 item hop le trong sample_crossref_payload
    assert settings.paths.raw_api_response.exists()
    assert settings.paths.raw_records_json.exists()


def test_fetch_retries_on_503_then_succeeds(monkeypatch, base_settings, tmp_path, sample_crossref_payload):
    settings = _isolated(base_settings, tmp_path)
    responses = [_FakeResponse(503), _FakeResponse(200, sample_crossref_payload)]

    def fake_get(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("time.sleep", lambda *_: None)

    records = fetch_source_records(settings)
    assert len(records) == 1


def test_fetch_falls_back_to_snapshot_when_network_fails(monkeypatch, base_settings, tmp_path, sample_crossref_payload):
    settings = _isolated(base_settings, tmp_path)
    # Snapshot da co san tu truoc (vd lan chay truoc).
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    from dataclasses import asdict

    from ingestion.crossref import parse_crossref_payload

    existing = parse_crossref_payload(sample_crossref_payload)
    settings.paths.raw_records_json.write_text(
        json.dumps([asdict(r) for r in existing]), encoding="utf-8"
    )

    def fake_get(*args, **kwargs):
        import requests

        raise requests.ConnectionError("network is down")

    monkeypatch.setattr("requests.get", fake_get)

    records = fetch_source_records(settings)
    assert len(records) == len(existing)


def test_fetch_retries_exhausted_raises_when_no_snapshot(monkeypatch, base_settings, tmp_path):
    settings = _isolated(base_settings, tmp_path)

    def fake_get(*args, **kwargs):
        return _FakeResponse(503)

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("time.sleep", lambda *_: None)

    with pytest.raises(Exception):
        fetch_source_records(settings)
