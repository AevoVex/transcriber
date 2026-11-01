from __future__ import annotations

import json
from pathlib import Path

from chat_export_parser import (
    collect_image_references,
    export_markdown_chat,
    extract_chat_messages,
    find_html_files,
    telegram_html_sort_key,
    update_html,
)


HTML = """<!doctype html><html><head></head><body>
<div class="message default clearfix" id="message100">
 <div class="body">
  <div class="pull_right date details" title="01.08.2026 10:00:01 UTC+03:00">10:00</div>
  <div class="from_name">Алиса</div>
  <div class="text">Привет<br>мир</div>
 </div>
</div>
<div class="message default clearfix joined" id="message101">
 <div class="body">
  <div class="pull_right date details" title="01.08.2026 10:01:02 UTC+03:00">10:01</div>
  <div class="reply_to details">In reply to <a href="#go_to_message100">this message</a></div>
  <div class="media_wrap clearfix">
   <a class="media clearfix pull_left block_link media_voice_message" href="voice_messages/audio_1.ogg"><div class="body">Voice message</div></a>
  </div>
  <span class="reactions">
   <span class="reaction"><span class="emoji">❤️</span><span class="userpics">
    <div class="userpic"><div class="initials">А</div></div>
    <div class="userpic"><div class="initials">Б</div></div>
   </span></span>
  </span>
 </div>
</div>
<div class="message default clearfix" id="message102">
 <div class="body">
  <div class="pull_right date details" title="02.08.2026 11:00:00 UTC+03:00">11:00</div>
  <div class="from_name">Боб</div>
  <div class="media_wrap clearfix">
   <a class="photo_wrap clearfix pull_left" href="photos/photo_1.jpg"><img class="photo" src="photos/photo_1_thumb.jpg"></a>
  </div>
  <div class="text">Подпись к фото</div>
 </div>
</div>
</body></html>"""


def prepare_export(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "ChatExport"
    (root / "voice_messages").mkdir(parents=True)
    (root / "photos").mkdir()
    (root / "transcriptions").mkdir()
    (root / "image_descriptions" / "photos").mkdir(parents=True)
    (root / "voice_messages" / "audio_1.ogg").write_bytes(b"audio")
    (root / "photos" / "photo_1.jpg").write_bytes(b"image")
    (root / "transcriptions" / "audio_1.json").write_text(
        json.dumps({"message": "Текст голоса", "messages_with_timestamps": []}),
        encoding="utf-8",
    )
    (root / "image_descriptions" / "photos" / "photo_1.json").write_text(
        json.dumps({"description": "Описание фотографии"}), encoding="utf-8"
    )
    html_path = root / "messages.html"
    html_path.write_text(HTML, encoding="utf-8")
    return root, html_path


def test_extract_messages_preserves_sender_reply_reactions_and_media(tmp_path: Path) -> None:
    root, html_path = prepare_export(tmp_path)
    messages = extract_chat_messages([html_path], root)

    assert [message.message_id for message in messages] == ["100", "101", "102"]
    assert messages[0].parts == ["Привет\nмир"]
    assert messages[1].sender == "Алиса"
    assert messages[1].reply_to == "100"
    assert messages[1].reactions == [("❤️", 2)]
    assert messages[1].parts == ["**Голосовое сообщение:** Текст голоса"]
    assert messages[2].parts == ["Подпись к фото", "**Фото:** Описание фотографии"]


def test_markdown_export_chunks_and_links_messages(tmp_path: Path) -> None:
    root, html_path = prepare_export(tmp_path)
    output = tmp_path / "markdown"
    files = export_markdown_chat(root, [html_path], chunk_size=1, output_dir=output)

    assert [path.name for path in files] == [
        "chat-part-001.md", "chat-part-002.md", "chat-part-003.md"
    ]
    second = files[1].read_text(encoding="utf-8")
    assert "[[chat-part-001#^message-100|message 100]]" in second
    assert "Reactions: ❤️ x2" in second
    assert "^message-101" in second
    assert "[[chat-part-001|← Предыдущая часть]]" in second
    assert "[[chat-part-003|Следующая часть →]]" in second
    assert "# 2026-08-02" in files[2].read_text(encoding="utf-8")


def test_update_html_is_idempotent(tmp_path: Path) -> None:
    root, html_path = prepare_export(tmp_path)
    first = update_html(html_path, root)
    content_after_first = html_path.read_text(encoding="utf-8")
    second = update_html(html_path, root)

    assert first == (1, 0, 1, 0)
    assert second == (1, 0, 1, 0)
    assert html_path.read_text(encoding="utf-8") == content_after_first
    assert content_after_first.count("<!-- transcriber:start -->") == 1
    assert content_after_first.count("<!-- image-description:start -->") == 1
    assert html_path.with_suffix(".html.bak").is_file()


def test_image_caption_and_thumbnail_filter(tmp_path: Path) -> None:
    root, _ = prepare_export(tmp_path)
    references = collect_image_references(HTML, root)
    assert len(references) == 1
    assert references[0].image_path.name == "photo_1.jpg"
    assert references[0].caption == "Подпись к фото"


def test_telegram_html_sort_key_orders_numbered_pages() -> None:
    paths = [Path("messages10.html"), Path("messages2.html"), Path("messages.html")]
    assert [path.name for path in sorted(paths, key=telegram_html_sort_key)] == [
        "messages.html", "messages2.html", "messages10.html"
    ]
