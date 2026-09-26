from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

import messages
from database import DatabaseError
from frames.common import HeaderWidget, create_page_title
from frames.product_card import format_money


class OrdersFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.addWidget(HeaderWidget(controller, on_back=controller.show_catalog))
        layout.addWidget(create_page_title("Список заказов"))

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Номер", "Дата заказа", "ФИО клиента", "Итоговая сумма"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.open_order)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        create_button = QPushButton("Добавить заказ")
        create_button.clicked.connect(controller.show_order_client)
        buttons.addWidget(create_button)
        open_button = QPushButton("Просмотреть выбранный", objectName="secondary_button")
        open_button.clicked.connect(self.open_selected_order)
        buttons.addWidget(open_button)
        delete_button = QPushButton("Удалить выбранный", objectName="secondary_button")
        delete_button.clicked.connect(self.delete_selected_order)
        buttons.addWidget(delete_button)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        if not self.controller.session.can_manage_orders:
            messages.show_error("Просмотр списка заказов доступен менеджеру и администратору.")
            self.controller.show_catalog()
            return
        try:
            orders = self.controller.database.list_orders()
        except DatabaseError as error:
            messages.show_error(str(error), "Ошибка загрузки заказов", self)
            orders = []
        self.table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            values = [
                str(order["order_id"]),
                order["order_date"].strftime("%d.%m.%Y"),
                order["client_name"],
                format_money(order["total"]),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in {0, 1, 3}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, int(order["order_id"]))
                self.table.setItem(row, column, item)

    def selected_order_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0 or not self.table.item(row, 0):
            return None
        return int(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))

    def open_order(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item:
            self.controller.show_order(int(item.data(Qt.ItemDataRole.UserRole)))

    def open_selected_order(self) -> None:
        order_id = self.selected_order_id()
        if order_id is None:
            messages.show_warning("Выберите заказ в списке.", "Заказ не выбран", self)
            return
        self.controller.show_order(order_id)

    def delete_selected_order(self) -> None:
        order_id = self.selected_order_id()
        if order_id is None:
            messages.show_warning("Выберите заказ в списке.", "Заказ не выбран", self)
            return
        if not messages.ask_confirmation(
            f"Удалить заказ №{order_id}? Все количества будут возвращены на соответствующие размеры.",
            "Удаление заказа",
            self,
        ):
            return
        try:
            self.controller.database.delete_order(order_id)
        except DatabaseError as error:
            messages.show_error(str(error), "Заказ не удалён", self)
            return
        messages.show_info(f"Заказ №{order_id} удалён, остатки восстановлены.", "Заказ удалён", self)
        self.refresh()

    def on_show(self) -> None:
        self.refresh()
