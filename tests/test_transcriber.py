from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from main import create_json, create_markdown, find_media_files, format_timestamp, transcribe_file


def test_format_timestamp_supports_minutes_and_hours() -> None:
    assert format_timestamp(65.9) == "01:05"
    assert format_timestamp(3661.2) == "01:01:01"


def test_find_media_files_filters_and_deduplicates(tmp_path: Path) -> None:
    audio = tmp_path / "voice.ogg"
    video = tmp_path / "clip.MP4"
    ignored = tmp_path / "notes.txt"
    for path in (audio, video, ignored):
        path.write_bytes(b"test")

    found = find_media_files([tmp_path, audio])
    assert set(found) == {audio, video}
    assert len(found) == 2


def test_markdown_and_json_contain_plain_and_timestamped_text() -> None:
    source = Path("voice.ogg")
    messages = [
        {"timestamp": "00:00", "text": "Привет"},
        {"timestamp": "00:03", "text": "как дела?"},
    ]

    markdown = create_markdown(source, "ru", messages)
    payload = create_json(source, "ru", messages)

    assert "## Текст\n\nПривет как дела?" in markdown
    assert "[00:03] как дела?" in markdown
    assert payload["message"] == "Привет как дела?"
    assert payload["messages_with_timestamps"] == messages


def test_transcribe_file_writes_both_formats_and_skips_existing(
    tmp_path: Path, capsys
) -> None:
    source = tmp_path / "voice.ogg"
    source.write_bytes(b"audio")

    class FakeModel:
        calls = 0

        def transcribe(self, *_args, **_kwargs):
            self.calls += 1
            segments = [
                SimpleNamespace(start=0.0, text=" Привет "),
                SimpleNamespace(start=2.0, text=" "),
                SimpleNamespace(start=3.4, text="мир"),
            ]
            info = SimpleNamespace(language="ru", language_probability=0.99)
            return segments, info

    model = FakeModel()
    output = tmp_path / "result"
    transcribe_file(model, source, "ru", False, "both", output)

    md_path = output / "voice.md"
    json_path = output / "voice.json"
    assert md_path.is_file() and json_path.is_file()
    assert json.loads(json_path.read_text(encoding="utf-8"))["message"] == "Привет мир"
    assert "[00:03] мир" in md_path.read_text(encoding="utf-8")
    assert model.calls == 1

    transcribe_file(model, source, "ru", False, "both", output)
    assert model.calls == 1
    assert "[SKIP]" in capsys.readouterr().out
