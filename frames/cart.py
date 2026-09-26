from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

import messages
from database import DatabaseError, OrderValidationError
from frames.common import HeaderWidget, create_page_title
from frames.order_items_table import DraftItemsTable
from frames.product_card import format_money


class CartFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.addWidget(HeaderWidget(controller, on_back=controller.show_catalog))
        layout.addWidget(create_page_title("Формирование заказа"))

        client = controller.session.order_client or controller.session.user
        self.client_label = QLabel(
            f"Клиент: {client.full_name if client else 'не выбран'}",
            objectName="section_title",
        )
        layout.addWidget(self.client_label)

        self.table = DraftItemsTable()
        self.table.remove_requested.connect(self.remove_item)
        layout.addWidget(self.table)
        self.total_label = QLabel(objectName="section_title")
        layout.addWidget(self.total_label)

        buttons = QHBoxLayout()
        continue_button = QPushButton("Продолжить покупки", objectName="secondary_button")
        continue_button.clicked.connect(controller.show_catalog)
        buttons.addWidget(continue_button)
        cancel_button = QPushButton("Отказаться от заказа", objectName="secondary_button")
        cancel_button.clicked.connect(self.cancel_order)
        buttons.addWidget(cancel_button)
        buttons.addStretch()
        self.confirm_button = QPushButton("Подтвердить заказ")
        self.confirm_button.clicked.connect(self.confirm_order)
        buttons.addWidget(self.confirm_button)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        draft = self.controller.session.order_draft
        self.table.set_items(draft.items)
        self.total_label.setText(f"Предварительная сумма: {format_money(draft.total)}")
        self.confirm_button.setEnabled(not draft.is_empty())

    def remove_item(self, stock_item_id: int) -> None:
        self.controller.session.order_draft.remove(stock_item_id)
        self.refresh()

    def cancel_order(self) -> None:
        draft = self.controller.session.order_draft
        if draft.is_empty():
            self.controller.show_catalog()
            return
        if not messages.ask_confirmation(
            "Отказаться от заказа? Все добавленные позиции будут удалены.",
            "Отказ от заказа",
            self,
        ):
            return
        draft.clear()
        self.controller.session.order_client = self.controller.session.user
        self.controller.show_catalog(recreate=True)

    def confirm_order(self) -> None:
        session = self.controller.session
        if session.order_draft.is_empty():
            messages.show_error("Нельзя подтвердить пустой заказ.", "Пустой заказ", self)
            return
        client = session.order_client or session.user
        if client is None:
            messages.show_error("Для оформления заказа необходимо войти в систему.", "Нет клиента", self)
            return
        try:
            result = self.controller.database.create_order(
                client.user_id,
                session.order_draft.database_items(),
                date.today(),
            )
        except (OrderValidationError, DatabaseError) as error:
            messages.show_error(str(error), "Заказ не сохранён", self)
            return
        session.order_draft.clear()
        session.order_client = session.user
        messages.show_info(
            f"Заказ №{result['order_id']} оформлен. Итоговая сумма: {format_money(result['total'])}",
            "Заказ сохранён",
            self,
        )
        self.controller.show_catalog(recreate=True)
