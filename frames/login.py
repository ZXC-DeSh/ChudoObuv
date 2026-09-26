from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout

import messages
from database import DatabaseError
from frames.common import RESOURCES_DIR, create_page_title


class LoginFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.setContentsMargins(120, 45, 120, 80)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(RESOURCES_DIR / "logo.png"))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    220,
                    220,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(create_page_title("Чудо Обувь — вход в систему"))
        layout.addStretch()

        layout.addWidget(QLabel("Логин"))
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Введите логин из Users_import.xlsx")
        self.login_edit.returnPressed.connect(self.sign_in)
        layout.addWidget(self.login_edit)

        sign_in_button = QPushButton("Войти")
        sign_in_button.clicked.connect(self.sign_in)
        layout.addWidget(sign_in_button)

        guest_button = QPushButton("Продолжить без авторизации", objectName="secondary_button")
        guest_button.clicked.connect(self.enter_as_guest)
        layout.addWidget(guest_button)

    def sign_in(self) -> None:
        login = self.login_edit.text().strip()
        if not login:
            messages.show_warning("Введите логин пользователя.", "Не заполнен логин", self)
            return
        try:
            user = self.controller.database.authenticate(login)
        except DatabaseError as error:
            messages.show_error(str(error), "Ошибка базы данных", self)
            return
        if not user:
            messages.show_error(
                f"Пользователь с логином «{login}» не найден. Проверьте ввод.",
                "Ошибка авторизации",
                self,
            )
            return
        self.controller.session.sign_in(user)
        self.controller.show_catalog(recreate=True)

    def enter_as_guest(self) -> None:
        self.controller.session.enter_as_guest()
        self.controller.show_catalog(recreate=True)
