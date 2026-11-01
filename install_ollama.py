from __future__ import annotations

import argparse

from ollama_manager import OllamaClient, OllamaManagerError, install_ollama, wait_for_ollama


def main() -> None:
    parser = argparse.ArgumentParser(description="Установка Ollama и загрузка модели")
    parser.add_argument("--model", default="qwen3-vl:8b")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()

    try:
        client = OllamaClient(args.ollama_url)
        if not client.is_available() and not args.skip_install:
            print("[OLLAMA] Ollama не найдена. Запускается официальный установщик…")
            print(install_ollama())
        if not wait_for_ollama(args.ollama_url):
            raise OllamaManagerError("Ollama API не запустился вовремя.")
        if client.has_model(args.model):
            print(f"[OLLAMA] Модель уже установлена: {args.model}")
            return
        print(f"[OLLAMA] Загрузка модели: {args.model}")
        for update in client.pull_model(args.model):
            percent = f" {update.percent}%" if update.percent is not None else ""
            print(f"[PULL]{percent} {update.status}", flush=True)
        print(f"[OLLAMA] Модель готова: {args.model}")
    except OllamaManagerError as exc:
        print(f"[ERROR] {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
