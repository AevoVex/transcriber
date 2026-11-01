# Сборка Transcriber

## Требования

- Windows 10/11, Linux или macOS;
- Python 3.10–3.12;
- виртуальное окружение `.venv`;
- Inno Setup 6 — только для Windows-установщика.

## Автоматическая сборка Windows

```powershell
build.bat
```

Сценарий устанавливает зависимости сборки, очищает предыдущие артефакты через PyInstaller и создаёт one-folder дистрибутив:

```text
dist/Transcriber/
├── Transcriber.exe
├── TranscriberCLI.exe
├── ChatExportParser.exe
└── _internal/
```

`Transcriber.exe` — GUI без консольного окна. Два других EXE предназначены для CLI и контекстного меню. Все три программы используют общую папку зависимостей, поэтому библиотеки не дублируются.

Если `ISCC.exe` найден, `build.bat` компилирует `installer/transcriber.iss` и создаёт установщик в `installer/output`.

## Ручная сборка

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean transcriber.spec
```

На Linux/macOS используйте исполняемые файлы виртуального окружения без расширения `.exe`:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
pyinstaller --noconfirm --clean transcriber.spec
```

## Автотесты

Функциональные тесты не загружают реальные модели Whisper/Ollama и используют временные файлы:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

На Linux/macOS:

```bash
.venv/bin/python -m pytest -q
```

Проверка EXE:

```powershell
.\dist\Transcriber\TranscriberCLI.exe --help
.\dist\Transcriber\ChatExportParser.exe --help
```

Сборка установщика:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\transcriber.iss
```

## Выпуск новой версии

1. Обновить `APP_VERSION` в `installer/transcriber.iss`.
2. Обновить версию в `version_info.txt`.
3. Добавить изменения в `CHANGELOG.md`.
4. Выполнить `build.bat` на чистом окружении.
5. Проверить GUI, CLI, удаление приложения и пункты контекстного меню.

## Ограничения

Сборка платформозависима: пакет для каждой ОС необходимо собирать на этой ОС. Inno Setup и интеграция с контекстным меню относятся только к Windows. Модели Whisper не упаковываются и загружаются при первом использовании.
