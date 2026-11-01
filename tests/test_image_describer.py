from __future__ import annotations

import json
from pathlib import Path

import image_describer
from describe_images import find_images, is_source_image, save_description


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_image_filter_excludes_thumbnails_and_non_webp_stickers(tmp_path: Path) -> None:
    photos = tmp_path / "photos"
    stickers = tmp_path / "stickers"
    photos.mkdir()
    stickers.mkdir()
    source_photo = photos / "photo.jpg"
    photo_thumb = photos / "photo_thumb.jpg"
    source_sticker = stickers / "sticker (3).webp"
    sticker_thumb = stickers / "sticker (3).webp_thumb.jpg"
    sticker_png = stickers / "sticker.png"
    for path in (source_photo, photo_thumb, source_sticker, sticker_thumb, sticker_png):
        path.write_bytes(b"image")

    assert is_source_image(source_photo)
    assert is_source_image(source_sticker)
    assert not is_source_image(photo_thumb)
    assert not is_source_image(sticker_thumb)
    assert not is_source_image(sticker_png)
    assert find_images([tmp_path]) == [source_photo, source_sticker]


def test_describe_image_retries_empty_response_and_disables_thinking(
    tmp_path: Path, monkeypatch
) -> None:
    image = tmp_path / "photo.jpg"
    image.write_bytes(b"raw-image")
    requests: list[dict] = []
    responses = iter(
        [
            {"done": True, "done_reason": "stop", "message": {"content": "", "thinking": "long"}},
            {"done": True, "done_reason": "stop", "message": {"content": "Готовое описание"}},
        ]
    )

    def fake_urlopen(request, timeout):
        assert timeout == 300
        requests.append(json.loads(request.data.decode("utf-8")))
        return FakeResponse(next(responses))

    monkeypatch.setattr(image_describer, "urlopen", fake_urlopen)
    result = image_describer.describe_image(image, context="Подпись пользователя")

    assert result == "Готовое описание"
    assert len(requests) == 2
    assert requests[0]["messages"][0]["content"].startswith("/no_think\n")
    assert "Подпись пользователя" in requests[0]["messages"][0]["content"]
    assert len(requests[0]["messages"]) == 1
    assert len(requests[0]["messages"][0]["images"]) == 1
    assert requests[0]["options"]["num_ctx"] == 8192
    assert requests[1]["options"]["num_predict"] == 3072


def test_save_description_writes_json_and_markdown(tmp_path: Path) -> None:
    image = tmp_path / "photo.jpg"
    image.write_bytes(b"image")
    json_path, md_path = save_description(image, "Описание", "vision-model", tmp_path / "out")

    assert json.loads(json_path.read_text(encoding="utf-8")) == {
        "source": "photo.jpg",
        "model": "vision-model",
        "description": "Описание",
    }
    assert "Описание" in md_path.read_text(encoding="utf-8")
