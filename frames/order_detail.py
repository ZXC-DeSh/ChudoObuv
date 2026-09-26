from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

import messages
from components import HeaderWidget, create_page_title
from components.product_card import format_money
from database import DatabaseError, OrderValidationError
from forms import OrderItemsTable


class OrderDetailFrame(QFrame):
    def __init__(self, controller, order_id: int):
        super().__init__()
        self.controller = controller
        self.order_id = order_id
        self.order = None
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(HeaderWidget(controller, on_back=controller.show_orders))
        title = "Редактирование заказа" if controller.session.is_admin else "Состав заказа"
        self.layout.addWidget(create_page_title(title))
        self.info_layout = QVBoxLayout()
        self.layout.addLayout(self.info_layout)
        self.table = OrderItemsTable(editable=controller.session.is_admin)
        self.table.remove_requested.connect(self.remove_item)
        self.layout.addWidget(self.table)
        self.total_label = QLabel(objectName="section_title")
        self.layout.addWidget(self.total_label)
        self.refresh()

    def refresh(self) -> None:
        try:
            self.order = self.controller.database.get_order(self.order_id)
        except DatabaseError as error:
            messages.show_error(str(error), "Ошибка загрузки заказа", self)
            return
        if not self.order:
            messages.show_error("Заказ не найден.", "Ошибка загрузки", self)
            self.controller.show_orders()
            return

        while self.info_layout.count():
            item = self.info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

        self.info_layout.addWidget(QLabel(f"Заказ №{self.order_id}"))
        self.info_layout.addWidget(QLabel(f"Клиент: {self.order['client_name']}"))
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Дата заказа"))
        if self.controller.session.is_admin:
            self.date_edit = QDateEdit()
            self.date_edit.setCalendarPopup(True)
            self.date_edit.setDisplayFormat("dd.MM.yyyy")
            order_date = self.order["order_date"]
            self.date_edit.setDate(QDate(order_date.year, order_date.month, order_date.day))
            date_row.addWidget(self.date_edit)
            save_button = QPushButton("Сохранить дату")
            save_button.clicked.connect(self.save_date)
            date_row.addWidget(save_button)
        else:
            date_row.addWidget(QLabel(self.order["order_date"].strftime("%d.%m.%Y")))
        date_row.addStretch()
        self.info_layout.addLayout(date_row)
        self.table.set_items(self.order["items"])
        self.total_label.setText(f"Итоговая сумма заказа: {format_money(self.order['total'])}")

    def save_date(self) -> None:
        selected = self.date_edit.date().toPython()
        try:
            self.controller.database.update_order_date(self.order_id, selected)
        except DatabaseError as error:
            messages.show_error(str(error), "Дата не изменена", self)
            return
        messages.show_info("Дата заказа обновлена.", "Изменения сохранены", self)
        self.refresh()

    def remove_item(self, order_item_id: int) -> None:
        if not messages.ask_confirmation(
            "Удалить позицию из заказа? Количество будет возвращено на склад выбранного размера.",
            "Удаление позиции",
            self,
        ):
            return
        try:
            self.controller.database.remove_order_item(self.order_id, order_item_id)
        except (OrderValidationError, DatabaseError) as error:
            messages.show_error(str(error), "Позиция не удалена", self)
            return
        messages.show_info("Позиция удалена, остаток размера восстановлен.", "Изменения сохранены", self)
        self.refresh()
