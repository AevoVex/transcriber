from __future__ import annotations

import html
import os
import re
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, QProcessEnvironment, QSettings, QThread, QTimer, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ollama_manager import (
    OllamaClient,
    OllamaManagerError,
    install_ollama,
    ollama_executable,
    start_ollama_service,
    wait_for_ollama,
)


APP_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else APP_DIR
EXECUTABLE_SUFFIX = ".exe" if os.name == "nt" else ""
MEDIA_FILTER = (
    "Медиафайлы (*.mp3 *.wav *.ogg *.opus *.m4a *.aac *.flac "
    "*.mp4 *.mkv *.webm);;Все файлы (*)"
)
HTML_FILTER = "HTML-файлы (*.html *.htm);;Все файлы (*)"

NORD_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #2E3440;
    color: #D8DEE9;
    font-family: "Segoe UI Variable", "Inter", "Segoe UI", sans-serif;
    font-size: 13px;
}
QFrame#sidebar { background-color: #292E39; border-right: 1px solid #434C5E; }
QLabel#brand { color: #ECEFF4; font-size: 18px; font-weight: 600; letter-spacing: 1px; }
QFrame#sidebar QLabel { background: transparent; }
QLabel#muted, QLabel#note { color: #8F98A8; }
QLabel#sidebarSection { color: #7F8999; font-size: 11px; font-weight: 600; letter-spacing: 1px; }
QLabel#sectionTitle { color: #E5E9F0; font-size: 15px; font-weight: 600; }
QLabel#pageTitle { color: #ECEFF4; font-size: 22px; font-weight: 600; }
QLabel#pageDescription { color: #9AA5B5; font-size: 12px; }
QListWidget#navigation {
    background: transparent; border: none; outline: none; padding: 2px 0;
}
QListWidget#navigation::item {
    height: 38px; border-radius: 5px; padding: 0 8px; color: #B8C0CC;
}
QListWidget#navigation::item:hover { background: #343B49; color: #E5E9F0; }
QListWidget#navigation::item:selected {
    background: #3B4252; color: #ECEFF4; border-left: 3px solid #88C0D0;
}
QScrollArea { border: none; background: #2E3440; }
QScrollArea > QWidget > QWidget { background: #2E3440; }
QGroupBox {
    background: #3B4252; border: 1px solid #4C566A; border-radius: 7px;
    margin-top: 14px; padding: 14px 12px 10px 12px; font-weight: 600; color: #E5E9F0;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QLineEdit, QComboBox, QSpinBox, QListWidget, QTextBrowser {
    min-height: 24px; background: #343B49; color: #D8DEE9;
    border: 1px solid #4C566A; border-radius: 5px; padding: 4px 7px;
    selection-background-color: #5E81AC;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QListWidget:focus, QTextBrowser:focus {
    border-color: #88C0D0;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: #3B4252; border: 1px solid #4C566A; selection-background-color: #434C5E; }
QPushButton {
    min-height: 24px; padding: 4px 12px; background: #434C5E; color: #E5E9F0;
    border: 1px solid #4C566A; border-radius: 5px;
}
QPushButton:hover { background: #4C566A; border-color: #5E81AC; }
QPushButton:pressed { background: #3B4252; }
QPushButton:disabled { color: #7F8999; background: #343B49; border-color: #434C5E; }
QPushButton#startButton { background: #88C0D0; color: #2E3440; border-color: #88C0D0; font-weight: 600; }
QPushButton#startButton:hover { background: #8FBCBB; }
QPushButton#stopButton { background: #434C5E; color: #BF616A; border-color: #BF616A; font-weight: 600; }
QPushButton#stopButton:hover { background: #BF616A; color: #ECEFF4; }
QPushButton#ghostButton { background: transparent; border-color: transparent; color: #AAB3C0; }
QPushButton#ghostButton:hover { background: #434C5E; color: #ECEFF4; }
QCheckBox { spacing: 8px; color: #D8DEE9; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #4C566A; border-radius: 4px; background: #343B49; }
QCheckBox::indicator:hover { border-color: #88C0D0; }
QCheckBox::indicator:checked { background: #88C0D0; border-color: #88C0D0; }
QFrame#outputPanel { background: #3B4252; border-top: 1px solid #4C566A; }
QTextBrowser { font-family: "Cascadia Mono", "JetBrains Mono", monospace; font-size: 12px; }
QSplitter::handle { background: #4C566A; height: 1px; }
QScrollBar:vertical { width: 10px; background: #2E3440; }
QScrollBar::handle:vertical { background: #4C566A; min-height: 28px; border-radius: 4px; }
QToolTip { background: #434C5E; color: #ECEFF4; border: 1px solid #4C566A; }
"""


class OllamaTask(QThread):
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, action: str, model: str, base_url: str, parent=None):
        super().__init__(parent)
        self.action = action
        self.model = model
        self.base_url = base_url

    def run(self) -> None:
        try:
            if self.action == "install":
                self.message.emit("Загрузка и запуск официального установщика Ollama…")
                result = install_ollama()
                self.message.emit(result)
                if sys.platform == "darwin":
                    self.succeeded.emit(result)
                    return
                if not wait_for_ollama(self.base_url, timeout=90):
                    raise OllamaManagerError(
                        "Установка завершена, но Ollama API пока недоступен. "
                        "Запустите Ollama и повторите проверку."
                    )

            client = OllamaClient(self.base_url)
            if client.has_model(self.model):
                self.succeeded.emit(f"Модель уже установлена: {self.model}")
                return
            self.message.emit(f"Загрузка модели {self.model}…")
            for update in client.pull_model(self.model):
                self.message.emit(update.status)
                self.progress.emit(update.percent if update.percent is not None else -1)
            if not client.has_model(self.model):
                raise OllamaManagerError("Ollama не подтвердила установку модели.")
            self.succeeded.emit(f"Модель готова: {self.model}")
        except Exception as exc:
            self.failed.emit(str(exc))


class OllamaProgressDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(480)
        self.status = QLabel("Подготовка…")
        self.status.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.close_button = QPushButton("Закрыть")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignRight)

    def update_progress(self, value: int) -> None:
        if value < 0:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(value)

    def complete(self, message: str) -> None:
        self.status.setText(message)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.close_button.setEnabled(True)

    def fail(self, message: str) -> None:
        self.status.setText(f"Ошибка: {message}")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.close_button.setEnabled(True)


class DropListWidget(QListWidget):
    paths_dropped = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)

    def dragEnterEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self.paths_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

class PathSelector(QWidget):
    def __init__(self, file_filter: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.file_filter = file_filter
        self.paths = DropListWidget()
        self.paths.paths_dropped.connect(self.add_paths)
        self.paths.setAlternatingRowColors(True)
        self.paths.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.paths.setMinimumHeight(125)

        add_files = QPushButton("Добавить файлы…")
        add_folder = QPushButton("Добавить папку…")
        remove = QPushButton("Убрать")
        clear = QPushButton("Очистить")

        add_files.clicked.connect(self.add_files)
        add_folder.clicked.connect(self.add_folder)
        remove.clicked.connect(self.remove_selected)
        clear.clicked.connect(self.paths.clear)

        buttons = QHBoxLayout()
        buttons.addWidget(add_files)
        buttons.addWidget(add_folder)
        buttons.addStretch(1)
        buttons.addWidget(remove)
        buttons.addWidget(clear)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.paths)
        layout.addLayout(buttons)

    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы",
            "",
            self.file_filter,
        )
        self.add_paths(files)

    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            self.add_paths([folder])

    def add_paths(self, paths: list[str]) -> None:
        existing = {self.paths.item(i).text() for i in range(self.paths.count())}
        for value in paths:
            normalized = str(Path(value).resolve())
            if normalized not in existing:
                self.paths.addItem(normalized)
                existing.add(normalized)

    def remove_selected(self) -> None:
        for item in self.paths.selectedItems():
            self.paths.takeItem(self.paths.row(item))

    def values(self) -> list[str]:
        return [self.paths.item(i).text() for i in range(self.paths.count())]


class ModelOptions(QGroupBox):
    def __init__(self, parent: QWidget | None = None):
        super().__init__("Параметры модели", parent)

        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.addItems(["large-v3", "medium", "small", "base"])

        self.language = QComboBox()
        self.language.setEditable(True)
        self.language.addItems(["ru", "auto", "en"])

        self.device = QComboBox()
        self.device.addItems(["cuda", "cpu"])

        self.compute_type = QComboBox()
        self.compute_type.setEditable(True)
        self.compute_type.addItems(["float16", "int8_float16", "int8", "float32"])

        form = QFormLayout(self)
        form.addRow("Модель:", self.model)
        form.addRow("Язык:", self.language)
        form.addRow("Устройство:", self.device)
        form.addRow("Тип вычислений:", self.compute_type)

    def arguments(self) -> list[str]:
        return [
            "--model", self.model.currentText().strip(),
            "--language", self.language.currentText().strip(),
            "--device", self.device.currentText(),
            "--compute-type", self.compute_type.currentText().strip(),
        ]

    def load_settings(self, settings: QSettings, prefix: str) -> None:
        self.model.setCurrentText(settings.value(f"{prefix}/model", "large-v3"))
        self.language.setCurrentText(settings.value(f"{prefix}/language", "ru"))
        self.device.setCurrentText(settings.value(f"{prefix}/device", "cuda"))
        self.compute_type.setCurrentText(
            settings.value(f"{prefix}/compute_type", "float16")
        )

    def save_settings(self, settings: QSettings, prefix: str) -> None:
        settings.setValue(f"{prefix}/model", self.model.currentText())
        settings.setValue(f"{prefix}/language", self.language.currentText())
        settings.setValue(f"{prefix}/device", self.device.currentText())
        settings.setValue(f"{prefix}/compute_type", self.compute_type.currentText())


class TranscriptionTab(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.path_selector = PathSelector(MEDIA_FILTER)
        self.options = ModelOptions()

        self.output_format = QComboBox()
        self.output_format.addItem("Markdown", "md")
        self.output_format.addItem("JSON", "json")
        self.output_format.addItem("Markdown + JSON", "both")

        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Рядом с исходным файлом")
        browse_output = QPushButton("Обзор…")
        browse_output.clicked.connect(self.select_output_dir)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_dir)
        output_row.addWidget(browse_output)

        self.force = QCheckBox("Перезаписать готовые результаты (--force)")

        output_group = QGroupBox("Результат")
        output_form = QFormLayout(output_group)
        output_form.addRow("Формат:", self.output_format)
        output_form.addRow("Папка:", output_row)
        output_form.addRow("", self.force)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Медиафайлы или папки:"))
        layout.addWidget(self.path_selector)
        layout.addWidget(output_group)
        layout.addWidget(self.options)
        layout.addStretch(1)

    def select_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Папка результатов")
        if folder:
            self.output_dir.setText(folder)

    def command(self) -> tuple[Path, list[str]]:
        paths = self.path_selector.values()
        if not paths:
            raise ValueError("Добавьте хотя бы один медиафайл или папку.")

        arguments = [
            *paths,
            "--format", self.output_format.currentData(),
            *self.options.arguments(),
        ]
        if self.output_dir.text().strip():
            arguments.extend(["--output-dir", self.output_dir.text().strip()])
        if self.force.isChecked():
            arguments.append("--force")
        return APP_DIR / "main.py", arguments

    def load_settings(self, settings: QSettings) -> None:
        self.options.load_settings(settings, "transcription")
        index = self.output_format.findData(settings.value("transcription/format", "md"))
        self.output_format.setCurrentIndex(max(index, 0))
        self.output_dir.setText(settings.value("transcription/output_dir", ""))
        self.force.setChecked(settings.value("transcription/force", False, type=bool))

    def save_settings(self, settings: QSettings) -> None:
        self.options.save_settings(settings, "transcription")
        settings.setValue("transcription/format", self.output_format.currentData())
        settings.setValue("transcription/output_dir", self.output_dir.text())
        settings.setValue("transcription/force", self.force.isChecked())


class ChatExportTab(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.path_selector = PathSelector(HTML_FILTER)
        self.options = ModelOptions()
        self.no_transcribe = QCheckBox("Не запускать Whisper — использовать готовые JSON/MD")
        self.force = QCheckBox(
            "Перезаписать готовые результаты (--force)"
        )

        self.describe_images = QCheckBox("Описывать фото и стикеры через Ollama")
        self.vision_model = QComboBox()
        self.vision_model.setEditable(True)
        self.vision_model.addItems(
            ["qwen3-vl:8b", "qwen3-vl-vision:latest", "qwen3-vl:4b", "qwen3-vl:2b"]
        )
        self.ollama_url = QLineEdit("http://127.0.0.1:11434")
        self.vision_log = QCheckBox("Подробный лог ошибок Ollama (--log)")
        self.ollama_setup_button = QPushButton("Проверить / скачать модель")
        self.ollama_status = QLabel("Статус Ollama ещё не проверен")
        self.ollama_status.setObjectName("muted")

        self.export_md = QCheckBox("Создать Markdown-архив для Obsidian")
        self.md_chunk_size = QSpinBox()
        self.md_chunk_size.setRange(50, 5000)
        self.md_chunk_size.setValue(500)
        self.md_chunk_size.setSuffix(" сообщений")
        self.md_chunk_size.setEnabled(False)
        self.export_md.toggled.connect(self.md_chunk_size.setEnabled)

        markdown_group = QGroupBox("Текстовая выгрузка чата")
        markdown_form = QFormLayout(markdown_group)
        markdown_form.addRow("", self.export_md)
        markdown_form.addRow("Размер одной части:", self.md_chunk_size)

        vision_group = QGroupBox("Описание изображений")
        vision_form = QFormLayout(vision_group)
        vision_form.addRow("", self.describe_images)
        vision_form.addRow("Vision-модель:", self.vision_model)
        vision_form.addRow("Ollama API:", self.ollama_url)
        vision_form.addRow("", self.ollama_setup_button)
        vision_form.addRow("Статус:", self.ollama_status)
        vision_form.addRow("", self.vision_log)

        self.no_transcribe.toggled.connect(self.update_force_enabled)
        self.describe_images.toggled.connect(self.update_force_enabled)

        note = QLabel(
            "Расшифровки сохраняются в transcriptions, описания картинок — "
            "в image_descriptions. HTML перед первым изменением копируется в .bak."
        )
        note.setWordWrap(True)
        note.setObjectName("note")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("HTML-файлы или папка Telegram Chat Export:"))
        layout.addWidget(self.path_selector)
        layout.addWidget(self.no_transcribe)
        layout.addWidget(self.force)
        layout.addWidget(vision_group)
        layout.addWidget(markdown_group)
        layout.addWidget(note)
        layout.addWidget(self.options)
        layout.addStretch(1)

    def update_force_enabled(self) -> None:
        self.vision_log.setEnabled(self.describe_images.isChecked())
        self.force.setEnabled(
            not self.no_transcribe.isChecked() or self.describe_images.isChecked()
        )

    def command(self) -> tuple[Path, list[str]]:
        paths = self.path_selector.values()
        if not paths:
            raise ValueError("Добавьте HTML-файл или папку экспорта.")

        arguments = [*paths, *self.options.arguments()]
        if self.no_transcribe.isChecked():
            arguments.append("--no-transcribe")
        if self.describe_images.isChecked():
            arguments.extend([
                "--describe-images",
                "--vision-model", self.vision_model.currentText().strip(),
                "--ollama-url", self.ollama_url.text().strip(),
            ])
        if self.vision_log.isChecked() and self.describe_images.isChecked():
            arguments.append("--log")
        if self.export_md.isChecked():
            arguments.extend(["--export-md", "--md-chunk-size", str(self.md_chunk_size.value())])
        if self.force.isChecked() and self.force.isEnabled():
            arguments.append("--force")
        return APP_DIR / "chat_export_parser.py", arguments

    def load_settings(self, settings: QSettings) -> None:
        self.options.load_settings(settings, "chat_export")
        self.no_transcribe.setChecked(
            settings.value("chat_export/no_transcribe", False, type=bool)
        )
        self.force.setChecked(
            settings.value("chat_export/force", False, type=bool)
        )
        self.describe_images.setChecked(
            settings.value("chat_export/describe_images", False, type=bool)
        )
        self.vision_model.setCurrentText(
            settings.value("chat_export/vision_model", "qwen3-vl:8b")
        )
        self.ollama_url.setText(
            settings.value("chat_export/ollama_url", "http://127.0.0.1:11434")
        )
        self.vision_log.setChecked(
            settings.value("chat_export/vision_log", False, type=bool)
        )
        self.export_md.setChecked(
            settings.value("chat_export/export_md", False, type=bool)
        )
        self.md_chunk_size.setValue(
            settings.value("chat_export/md_chunk_size", 500, type=int)
        )
        self.update_force_enabled()

    def save_settings(self, settings: QSettings) -> None:
        self.options.save_settings(settings, "chat_export")
        settings.setValue("chat_export/no_transcribe", self.no_transcribe.isChecked())
        settings.setValue("chat_export/force", self.force.isChecked())
        settings.setValue("chat_export/describe_images", self.describe_images.isChecked())
        settings.setValue("chat_export/vision_model", self.vision_model.currentText())
        settings.setValue("chat_export/ollama_url", self.ollama_url.text())
        settings.setValue("chat_export/vision_log", self.vision_log.isChecked())
        settings.setValue("chat_export/export_md", self.export_md.isChecked())
        settings.setValue("chat_export/md_chunk_size", self.md_chunk_size.value())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcriber")
        self.resize(1180, 820)
        self.setMinimumSize(900, 640)

        self.settings = QSettings("LocalTools", "Transcriber")
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("PYTHONUNBUFFERED", "1")
        environment.insert("PYTHONIOENCODING", "utf-8")
        environment.insert("PYTHONUTF8", "1")
        self.process.setProcessEnvironment(environment)
        self.process.setWorkingDirectory(str(APP_DIR))
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.started.connect(self.process_started)
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.process_error)

        self.transcription_tab = TranscriptionTab()
        self.chat_export_tab = ChatExportTab()
        self.pages = QStackedWidget()
        self.pages.addWidget(
            self.wrap_page(
                self.transcription_tab,
                "Транскрипция",
                "Локальная расшифровка аудио и видео с экспортом Markdown и JSON.",
            )
        )
        self.pages.addWidget(
            self.wrap_page(
                self.chat_export_tab,
                "Telegram Chat Export",
                "Транскрипции, vision-описания и связанный Markdown-архив чата.",
            )
        )

        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setFixedWidth(236)
        self.navigation.setSpacing(4)
        for title, symbol in (("Транскрипция", "◉"), ("Chat Export", "◇")):
            item = QListWidgetItem(f"  {symbol}   {title}")
            self.navigation.addItem(item)
        self.navigation.currentRowChanged.connect(self.switch_page)

        self.log = QTextBrowser()
        self.log.setOpenLinks(False)
        self.log.setOpenExternalLinks(False)
        self.log.anchorClicked.connect(self.open_log_link)
        self.output_buffer = ""
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(190)
        log_font = QFont("Cascadia Mono")
        log_font.setStyleHint(QFont.StyleHint.Monospace)
        self.log.setFont(log_font)

        self.start_button = QPushButton("Запустить")
        self.start_button.setObjectName("startButton")
        self.stop_button = QPushButton("Остановить")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setEnabled(False)
        open_output_button = QPushButton("Открыть результат")
        clear_button = QPushButton("Очистить лог")
        clear_button.setObjectName("ghostButton")

        self.start_button.clicked.connect(self.start_process)
        self.stop_button.clicked.connect(self.stop_process)
        open_output_button.clicked.connect(self.open_result_folder)
        clear_button.clicked.connect(self.log.clear)

        actions = QHBoxLayout()
        actions.addWidget(self.start_button)
        actions.addWidget(self.stop_button)
        actions.addWidget(open_output_button)
        actions.addStretch(1)
        actions.addWidget(clear_button)

        output_header = QHBoxLayout()
        output_title = QLabel("Вывод процесса")
        output_title.setObjectName("sectionTitle")
        output_header.addWidget(output_title)
        output_header.addStretch(1)

        output_panel = QFrame()
        output_panel.setObjectName("outputPanel")
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(12, 10, 12, 12)
        output_layout.addLayout(output_header)
        output_layout.addWidget(self.log)
        output_layout.addLayout(actions)

        workspace = QSplitter(Qt.Orientation.Vertical)
        workspace.addWidget(self.pages)
        workspace.addWidget(output_panel)
        workspace.setStretchFactor(0, 3)
        workspace.setStretchFactor(1, 1)
        workspace.setSizes([570, 230])

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 18, 12, 12)
        brand = QLabel("TRANSCRIBER")
        brand.setObjectName("brand")
        subtitle = QLabel("Local media tools")
        subtitle.setObjectName("muted")
        tools_label = QLabel("ИНСТРУМЕНТЫ")
        tools_label.setObjectName("sidebarSection")
        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(22)
        sidebar_layout.addWidget(tools_label)
        sidebar_layout.addWidget(self.navigation)
        sidebar_layout.addStretch(1)
        version = QLabel("Developer build · Qt 6")
        version.setObjectName("muted")
        sidebar_layout.addWidget(version)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar)
        layout.addWidget(workspace, 1)
        self.setCentralWidget(central)

        self.apply_theme()

        self.transcription_tab.load_settings(self.settings)
        self.chat_export_tab.load_settings(self.settings)
        self.navigation.setCurrentRow(self.settings.value("window/page", 0, type=int))
        self.ollama_task: OllamaTask | None = None
        self.ollama_dialog: OllamaProgressDialog | None = None
        self.chat_export_tab.ollama_setup_button.clicked.connect(self.check_ollama_interactive)
        QTimer.singleShot(700, self.check_ollama_on_startup)

    @staticmethod
    def wrap_page(content: QWidget, title: str, description: str) -> QWidget:
        content.setMinimumWidth(0)
        content.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        description_label = QLabel(description)
        description_label.setObjectName("pageDescription")
        shell = QWidget()
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(18, 16, 18, 10)
        layout.setSpacing(6)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addSpacing(6)
        layout.addWidget(scroll, 1)
        return shell

    def switch_page(self, index: int) -> None:
        if index >= 0:
            self.pages.setCurrentIndex(index)

    def active_command(self) -> tuple[Path, list[str]]:
        return (
            self.transcription_tab.command()
            if self.pages.currentIndex() == 0
            else self.chat_export_tab.command()
        )

    def start_process(self) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return
        try:
            script, arguments = self.active_command()
        except ValueError as exc:
            QMessageBox.warning(self, "Не выбраны файлы", str(exc))
            return

        if (
            self.pages.currentIndex() == 1
            and self.chat_export_tab.describe_images.isChecked()
            and not self.ensure_ollama_model()
        ):
            return

        if not getattr(sys, "frozen", False) and not script.is_file():
            QMessageBox.critical(self, "Ошибка", f"Не найден файл: {script}")
            return

        self.output_buffer = ""
        if getattr(sys, "frozen", False):
            executable_name = (
                f"TranscriberCLI{EXECUTABLE_SUFFIX}"
                if script.name == "main.py"
                else f"ChatExportParser{EXECUTABLE_SUFFIX}"
            )
            program = RUNTIME_DIR / executable_name
            process_arguments = arguments
        else:
            program = Path(sys.executable)
            process_arguments = [str(script), *arguments]

        command_preview = " ".join([str(program), *process_arguments])
        self.append_log(f"\n> {command_preview}\n")
        self.process.start(str(program), process_arguments)

    def ollama_values(self) -> tuple[str, str]:
        return (
            self.chat_export_tab.vision_model.currentText().strip(),
            self.chat_export_tab.ollama_url.text().strip(),
        )

    def check_ollama_on_startup(self) -> None:
        model, base_url = self.ollama_values()
        client = OllamaClient(base_url, timeout=2)
        if not client.is_available():
            if ollama_executable() and start_ollama_service() and wait_for_ollama(base_url, 10):
                self.offer_missing_model(client, model, base_url)
                return
            self.chat_export_tab.ollama_status.setText("Ollama не найдена или не запущена")
            answer = QMessageBox.question(
                self,
                "Требуется Ollama",
                "Для описания изображений нужна Ollama, но локальный сервис не найден.\n\n"
                "Скачать и запустить официальный установщик?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.start_ollama_task("install", model, base_url)
            return
        self.offer_missing_model(client, model, base_url)

    def check_ollama_interactive(self) -> None:
        model, base_url = self.ollama_values()
        if not model:
            QMessageBox.warning(self, "Модель не указана", "Введите имя модели Ollama.")
            return
        client = OllamaClient(base_url, timeout=3)
        if not client.is_available():
            if ollama_executable() and start_ollama_service() and wait_for_ollama(base_url, 10):
                self.offer_missing_model(client, model, base_url, always_report=True)
                return
            self.chat_export_tab.ollama_status.setText("Ollama API недоступен")
            answer = QMessageBox.question(
                self,
                "Ollama недоступна",
                "Установить Ollama с официального сайта и затем скачать модель?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.start_ollama_task("install", model, base_url)
            return
        self.offer_missing_model(client, model, base_url, always_report=True)

    def offer_missing_model(
        self,
        client: OllamaClient,
        model: str,
        base_url: str,
        always_report: bool = False,
    ) -> bool:
        try:
            if client.has_model(model):
                self.chat_export_tab.ollama_status.setText(f"Готово: {model}")
                if always_report:
                    QMessageBox.information(self, "Ollama", f"Модель установлена: {model}")
                return True
        except OllamaManagerError as exc:
            self.chat_export_tab.ollama_status.setText(str(exc))
            return False
        self.chat_export_tab.ollama_status.setText(f"Модель отсутствует: {model}")
        answer = QMessageBox.question(
            self,
            "Модель Ollama не найдена",
            f"Модель «{model}» не установлена.\n\nСкачать её сейчас?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.start_ollama_task("pull", model, base_url)
        return False

    def ensure_ollama_model(self) -> bool:
        model, base_url = self.ollama_values()
        if not model:
            QMessageBox.warning(self, "Модель не указана", "Введите имя vision-модели.")
            return False
        client = OllamaClient(base_url, timeout=3)
        if not client.is_available():
            self.check_ollama_interactive()
            return False
        return self.offer_missing_model(client, model, base_url)

    def start_ollama_task(self, action: str, model: str, base_url: str) -> None:
        if self.ollama_task and self.ollama_task.isRunning():
            return
        dialog = OllamaProgressDialog("Настройка Ollama", self)
        task = OllamaTask(action, model, base_url, self)
        self.ollama_dialog = dialog
        self.ollama_task = task
        task.message.connect(dialog.status.setText)
        task.progress.connect(dialog.update_progress)
        task.succeeded.connect(dialog.complete)
        task.failed.connect(dialog.fail)
        task.succeeded.connect(self.chat_export_tab.ollama_status.setText)
        task.failed.connect(self.chat_export_tab.ollama_status.setText)
        task.finished.connect(self.ollama_task_finished)
        task.finished.connect(task.deleteLater)
        dialog.open()
        task.start()

    def ollama_task_finished(self) -> None:
        self.ollama_task = None

    def stop_process(self) -> None:
        if self.process.state() == QProcess.ProcessState.NotRunning:
            return
        self.append_log("\n[GUI] Остановка процесса…\n")
        self.process.terminate()
        QTimer.singleShot(3000, self.kill_if_running)

    def kill_if_running(self) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

    def read_output(self) -> None:
        data = bytes(self.process.readAllStandardOutput())
        self.output_buffer += data.decode("utf-8", errors="replace")
        while "\n" in self.output_buffer:
            line, self.output_buffer = self.output_buffer.split("\n", 1)
            self.append_output_line(line.rstrip("\r"))

    def append_output_line(self, line: str) -> None:
        match = re.match(r"^\[(EXPORT|OK)\]\s+(.+)$", line)
        if match:
            candidate = Path(match.group(2).strip())
            if candidate.exists():
                resolved = candidate.resolve()
                url = QUrl.fromLocalFile(str(resolved)).toString()
                name = resolved.name or str(resolved)
                parent = "" if not resolved.name else str(resolved.parent) + os.sep
                prefix = html.escape(f"[{match.group(1)}] {parent}")
                label = html.escape(name)
                cursor = self.log.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                cursor.insertHtml(f'{prefix}<a href="{url}">{label}</a><br/>')
                self.log.setTextCursor(cursor)
                self.log.ensureCursorVisible()
                return
        self.append_log(line + "\n")

    def append_log(self, text: str) -> None:
        cursor = self.log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def open_log_link(self, url: QUrl) -> None:
        QDesktopServices.openUrl(url)

    def result_folder(self) -> Path | None:
        if self.pages.currentIndex() == 0:
            current = self.transcription_tab
            configured = current.output_dir.text().strip()
            if configured:
                return Path(configured)
            paths = current.path_selector.values()
            if paths:
                first = Path(paths[0])
                return first if first.is_dir() else first.parent
        else:
            current = self.chat_export_tab
            paths = current.path_selector.values()
            if paths:
                first = Path(paths[0])
                root = first if first.is_dir() else first.parent
                transcriptions = root / "transcriptions"
                return transcriptions if transcriptions.exists() else root
        return None

    def open_result_folder(self) -> None:
        folder = self.result_folder()
        if folder is None:
            QMessageBox.information(self, "Папка результата", "Сначала выберите файл или папку.")
            return
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def apply_theme(self) -> None:
        self.setStyleSheet(NORD_STYLESHEET)
        self.log.document().setDefaultStyleSheet(
            "a { color: #88C0D0; text-decoration: none; }"
        )

    def process_started(self) -> None:
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.navigation.setEnabled(False)
        self.pages.setEnabled(False)

    def process_finished(self, exit_code: int, _exit_status: QProcess.ExitStatus) -> None:
        self.read_output()
        if self.output_buffer:
            self.append_output_line(self.output_buffer.rstrip("\r"))
            self.output_buffer = ""
        self.append_log(f"\n[GUI] Процесс завершён, код: {exit_code}\n")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.navigation.setEnabled(True)
        self.pages.setEnabled(True)

    def process_error(self, _error: QProcess.ProcessError) -> None:
        self.append_log(f"\n[GUI ERROR] {self.process.errorString()}\n")

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if self.process.state() != QProcess.ProcessState.NotRunning:
            answer = QMessageBox.question(
                self,
                "Процесс выполняется",
                "Остановить процесс и закрыть приложение?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.process.kill()
            self.process.waitForFinished(2000)

        self.transcription_tab.save_settings(self.settings)
        self.chat_export_tab.save_settings(self.settings)
        self.settings.setValue("window/page", self.pages.currentIndex())
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Transcriber")
    app.setOrganizationName("LocalTools")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
