from __future__ import annotations

import json

import pytest

import ollama_manager
from ollama_manager import OllamaClient, OllamaManagerError, normalize_model_name


class FakeResponse:
    def __init__(self, payload=None, lines=None):
        self.payload = payload
        self.lines = lines or []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __iter__(self):
        return iter(json.dumps(line).encode("utf-8") + b"\n" for line in self.lines)


def test_model_names_treat_latest_as_default_tag() -> None:
    assert normalize_model_name("QWEN3-VL:8B") == "qwen3-vl:8b"
    assert normalize_model_name("gemma3") == "gemma3:latest"


def test_client_lists_and_matches_installed_models(monkeypatch) -> None:
    monkeypatch.setattr(
        ollama_manager.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(
            {"models": [{"name": "gemma3:latest"}, {"model": "qwen3-vl:8b"}]}
        ),
    )
    client = OllamaClient()
    assert client.models() == ["gemma3:latest", "qwen3-vl:8b"]
    assert client.has_model("gemma3")
    assert not client.has_model("missing:latest")


def test_pull_model_reports_streaming_progress(monkeypatch) -> None:
    requests = []

    def fake_urlopen(request, **_kwargs):
        requests.append(json.loads(request.data.decode("utf-8")))
        return FakeResponse(
            lines=[
                {"status": "pulling manifest"},
                {"status": "downloading", "completed": 25, "total": 100},
                {"status": "success"},
            ]
        )

    monkeypatch.setattr(ollama_manager.urllib.request, "urlopen", fake_urlopen)
    updates = list(OllamaClient().pull_model("qwen3-vl:8b"))

    assert requests == [{"model": "qwen3-vl:8b", "stream": True}]
    assert [update.percent for update in updates] == [None, 25, None]
    assert updates[-1].status == "success"


def test_pull_model_surfaces_stream_error(monkeypatch) -> None:
    monkeypatch.setattr(
        ollama_manager.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(lines=[{"error": "model not found"}]),
    )
    with pytest.raises(OllamaManagerError, match="model not found"):
        list(OllamaClient().pull_model("not-a-real-model"))
