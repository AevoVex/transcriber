from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from urllib.error import HTTPError, URLError


DEFAULT_URL = "http://127.0.0.1:11434"
WINDOWS_INSTALLER_URL = "https://ollama.com/download/OllamaSetup.exe"
LINUX_INSTALLER_URL = "https://ollama.com/install.sh"
MACOS_DOWNLOAD_URL = "https://ollama.com/download/mac"


class OllamaManagerError(RuntimeError):
    pass


@dataclass(frozen=True)
class PullProgress:
    status: str
    completed: int = 0
    total: int = 0

    @property
    def percent(self) -> int | None:
        if self.total <= 0:
            return None
        return min(100, max(0, round(self.completed * 100 / self.total)))


def normalize_model_name(name: str) -> str:
    normalized = name.strip().lower()
    return normalized if ":" in normalized else f"{normalized}:latest"


def ollama_executable() -> Path | None:
    found = shutil.which("ollama")
    if found:
        return Path(found)
    if os.name == "nt":
        candidate = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
        if candidate.is_file():
            return candidate
    if sys.platform == "darwin":
        candidate = Path("/Applications/Ollama.app/Contents/Resources/ollama")
        if candidate.is_file():
            return candidate
    return None


class OllamaClient:
    def __init__(self, base_url: str = DEFAULT_URL, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _json(self, path: str) -> dict:
        try:
            with urllib.request.urlopen(f"{self.base_url}{path}", timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
            raise OllamaManagerError(f"Ollama API недоступен: {exc}") from exc

    def is_available(self) -> bool:
        try:
            self._json("/api/tags")
            return True
        except OllamaManagerError:
            return False

    def models(self) -> list[str]:
        payload = self._json("/api/tags")
        return [str(item.get("name") or item.get("model", "")) for item in payload.get("models", [])]

    def has_model(self, model: str) -> bool:
        wanted = normalize_model_name(model)
        return any(normalize_model_name(installed) == wanted for installed in self.models())

    def pull_model(self, model: str) -> Iterator[PullProgress]:
        model = model.strip()
        if not model:
            raise OllamaManagerError("Не указано имя модели.")
        request = urllib.request.Request(
            f"{self.base_url}/api/pull",
            data=json.dumps({"model": model, "stream": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=None) as response:
                for raw_line in response:
                    if not raw_line.strip():
                        continue
                    update = json.loads(raw_line.decode("utf-8"))
                    if update.get("error"):
                        raise OllamaManagerError(str(update["error"]))
                    yield PullProgress(
                        status=str(update.get("status", "Загрузка…")),
                        completed=int(update.get("completed") or 0),
                        total=int(update.get("total") or 0),
                    )
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise OllamaManagerError(f"Модель не найдена или недоступна: {details}") from exc
        except (URLError, OSError, json.JSONDecodeError) as exc:
            raise OllamaManagerError(f"Ошибка загрузки модели: {exc}") from exc


def wait_for_ollama(base_url: str = DEFAULT_URL, timeout: int = 60) -> bool:
    deadline = time.monotonic() + timeout
    client = OllamaClient(base_url, timeout=2)
    while time.monotonic() < deadline:
        if client.is_available():
            return True
        time.sleep(1)
    return False


def start_ollama_service() -> bool:
    executable = ollama_executable()
    if not executable:
        return False
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        subprocess.Popen(
            [str(executable), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        return True
    except OSError:
        return False


def install_ollama() -> str:
    """Run the official platform installer and return a user-facing status."""
    if os.name == "nt":
        installer = Path(tempfile.gettempdir()) / "OllamaSetup.exe"
        urllib.request.urlretrieve(WINDOWS_INSTALLER_URL, installer)
        completed = subprocess.run([str(installer)], check=False)
        if completed.returncode:
            raise OllamaManagerError(f"Установщик Ollama завершился с кодом {completed.returncode}.")
        return "Установка Ollama завершена."
    if sys.platform.startswith("linux"):
        installer = Path(tempfile.gettempdir()) / "ollama-install.sh"
        urllib.request.urlretrieve(LINUX_INSTALLER_URL, installer)
        completed = subprocess.run(["sh", str(installer)], check=False)
        if completed.returncode:
            raise OllamaManagerError(f"Установка Ollama завершилась с кодом {completed.returncode}.")
        return "Установка Ollama завершена."
    if sys.platform == "darwin":
        webbrowser.open(MACOS_DOWNLOAD_URL)
        return "Открыта официальная загрузка Ollama для macOS. Установите приложение в Applications."
    raise OllamaManagerError(f"Автоматическая установка не поддерживается: {sys.platform}")
