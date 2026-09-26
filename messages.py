from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def _show(
    icon: QMessageBox.Icon,
    text: str,
    title: str,
    parent: QWidget | None = None,
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
) -> QMessageBox.StandardButton:
    message = QMessageBox(parent)
    message.setWindowTitle(title)
    message.setText(text)
    message.setIcon(icon)
    message.setStandardButtons(buttons)
    if buttons & QMessageBox.StandardButton.Yes:
        message.button(QMessageBox.StandardButton.Yes).setText("Да")
    if buttons & QMessageBox.StandardButton.No:
        message.button(QMessageBox.StandardButton.No).setText("Нет")
    return message.exec()


def show_info(text: str, title: str = "Информация", parent: QWidget | None = None):
    return _show(QMessageBox.Icon.Information, text, title, parent)


def show_warning(text: str, title: str = "Предупреждение", parent: QWidget | None = None):
    return _show(QMessageBox.Icon.Warning, text, title, parent)


def show_error(text: str, title: str = "Ошибка", parent: QWidget | None = None):
    return _show(QMessageBox.Icon.Critical, text, title, parent)


def ask_confirmation(text: str, title: str = "Подтверждение", parent: QWidget | None = None) -> bool:
    result = _show(
        QMessageBox.Icon.Question,
        text,
        title,
        parent,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes
