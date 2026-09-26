from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCES_DIR = PROJECT_ROOT / "database" / "resources"
PRODUCT_IMAGES_DIR = RESOURCES_DIR / "images"


def load_product_pixmap(filename: str | None, width: int, height: int) -> QPixmap:
    requested = PRODUCT_IMAGES_DIR / Path(filename or "").name
    path = requested if requested.is_file() else RESOURCES_DIR / "picture.png"
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return QPixmap()
    return pixmap.scaled(
        width,
        height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def create_page_title(text: str) -> QLabel:
    label = QLabel(text, objectName="page_title")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label


class HeaderWidget(QWidget):
    def __init__(self, controller, *, on_back=None, actions: list[tuple[str, callable]] | None = None):
        super().__init__(objectName="header")
        layout = QHBoxLayout(self)
        if on_back:
            back_button = QPushButton("Назад", objectName="secondary_button")
            back_button.clicked.connect(on_back)
            layout.addWidget(back_button)

        logo = QLabel()
        logo.setFixedSize(70, 70)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(RESOURCES_DIR / "logo.png"))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    68,
                    68,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(logo)

        brand = QLabel("Чудо Обувь", objectName="section_title")
        layout.addWidget(brand)
        layout.addStretch()

        for text, callback in actions or []:
            button = QPushButton(text, objectName="secondary_button")
            button.clicked.connect(callback)
            layout.addWidget(button)

        user_label = QLabel(controller.session.display_name)
        user_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        user_label.setWordWrap(True)
        user_label.setMinimumWidth(200)
        layout.addWidget(user_label)
