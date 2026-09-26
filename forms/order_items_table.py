from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHeaderView, QPushButton, QTableWidget, QTableWidgetItem

from components.product_card import format_money


class DraftItemsTable(QTableWidget):
    remove_requested = Signal(int)

    def __init__(self):
        super().__init__(0, 7)
        self.setHorizontalHeaderLabels(
            ["Модель", "Производство", "Размер", "Количество", "Цена", "Сумма", "Действие"]
        )
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

    def set_items(self, items) -> None:
        self.setRowCount(len(items))
        for row, item in enumerate(items):
            values = [
                item.product_name,
                item.manufacturer,
                item.size,
                str(item.quantity),
                format_money(item.unit_price),
                format_money(item.line_total),
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column in {2, 3, 4, 5}:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, column, cell)
            button = QPushButton("Удалить", objectName="secondary_button")
            button.clicked.connect(
                lambda _, stock_item_id=item.stock_item_id: self.remove_requested.emit(stock_item_id)
            )
            self.setCellWidget(row, 6, button)


class OrderItemsTable(QTableWidget):
    remove_requested = Signal(int)

    def __init__(self, *, editable: bool):
        columns = 7 if editable else 6
        super().__init__(0, columns)
        headers = ["Модель", "Производство", "Размер", "Количество", "Цена", "Сумма"]
        if editable:
            headers.append("Действие")
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.editable = editable

    def set_items(self, items: list[dict]) -> None:
        self.setRowCount(len(items))
        for row, item in enumerate(items):
            values = [
                item["name"],
                item["manufacturer"],
                str(item["size"]),
                str(item["quantity"]),
                format_money(item["unit_price"]),
                format_money(item["line_total"]),
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column in {2, 3, 4, 5}:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, column, cell)
            if self.editable:
                button = QPushButton("Удалить позицию", objectName="secondary_button")
                button.clicked.connect(
                    lambda _, order_item_id=item["order_item_id"]: self.remove_requested.emit(order_item_id)
                )
                self.setCellWidget(row, 6, button)
