from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFrame, QLabel, QPushButton, QVBoxLayout

import messages
from components import HeaderWidget, create_page_title
from database import DatabaseError


class OrderClientFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.addWidget(HeaderWidget(controller, on_back=controller.show_orders))
        layout.addWidget(create_page_title("Выбор клиента нового заказа"))
        layout.addWidget(QLabel("Клиент"))
        self.client_combo = QComboBox()
        layout.addWidget(self.client_combo)
        try:
            users = controller.database.list_users()
        except DatabaseError as error:
            messages.show_error(str(error), "Ошибка загрузки пользователей", self)
            users = []
        for user in users:
            self.client_combo.addItem(
                f"{user['full_name']} — {user['login']} ({user['role']})",
                dict(user),
            )
        continue_button = QPushButton("Перейти к каталогу")
        continue_button.clicked.connect(self.start_order)
        continue_button.setEnabled(bool(users))
        layout.addWidget(continue_button)
        layout.addStretch()

    def start_order(self) -> None:
        user = self.client_combo.currentData()
        if not user:
            messages.show_error("Выберите клиента заказа.", "Клиент не выбран", self)
            return
        draft = self.controller.session.order_draft
        if not draft.is_empty() and not messages.ask_confirmation(
            "Начать новый заказ? Текущий незавершённый заказ будет очищен.",
            "Новый заказ",
            self,
        ):
            return
        self.controller.session.select_order_client(user)
        self.controller.show_catalog(recreate=True)
