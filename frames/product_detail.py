from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import messages
from components import HeaderWidget, create_page_title, load_product_pixmap
from components.product_card import format_money
from database import DatabaseError
from services.order_draft import DraftItem


class ProductDetailFrame(QFrame):
    def __init__(self, controller, product_id: int):
        super().__init__()
        self.controller = controller
        self.product_id = product_id
        self.product = None
        layout = QVBoxLayout(self)
        actions = [("Заказ", controller.show_cart)] if controller.session.is_authenticated else []
        layout.addWidget(HeaderWidget(controller, on_back=controller.show_catalog, actions=actions))
        layout.addWidget(create_page_title("Просмотр модели обуви"))

        try:
            self.product = controller.database.get_product(product_id)
        except DatabaseError as error:
            messages.show_error(str(error), "Ошибка загрузки товара", self)
        if not self.product:
            layout.addWidget(QLabel("Выбранная модель не найдена."))
            return

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        content = QVBoxLayout(container)
        content.addLayout(self._create_product_block())
        content.addLayout(self._create_size_block())
        content.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _create_product_block(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        image = QLabel()
        image.setFixedSize(360, 300)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = load_product_pixmap(self.product.get("image_filename"), 350, 290)
        if pixmap.isNull():
            image.setText("Изображение недоступно")
        else:
            image.setPixmap(pixmap)
        layout.addWidget(image)

        details = QGridLayout()
        rows = [
            ("Производство", self.product["manufacturer"]),
            ("Наименование", self.product["name"]),
            ("Категория", self.product["category"]),
            ("Подкатегория", self.product["subcategory"]),
            ("Цена со скидкой", format_money(self.product["discounted_price"])),
            ("Состав", self.product["composition"]),
            ("Описание", self.product["description"]),
        ]
        for row, (label, value) in enumerate(rows):
            title = QLabel(label)
            title.setStyleSheet("font-weight: 700;")
            details.addWidget(title, row, 0)
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            details.addWidget(value_label, row, 1)
        layout.addLayout(details, 1)
        return layout

    def _create_size_block(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        all_sizes = [str(size["size"]) for size in self.product["sizes"]]
        available = [size for size in self.product["sizes"] if size["quantity"] > 0]
        layout.addWidget(QLabel(f"Размерный ряд: {', '.join(all_sizes)}"))
        layout.addWidget(
            QLabel(
                "Доступные размеры: "
                + (", ".join(str(size["size"]) for size in available) or "нет")
            )
        )

        if not self.controller.session.can_order:
            layout.addWidget(
                QLabel("Для выбора размера и оформления заказа войдите по логину пользователя.")
            )
            return layout

        row = QHBoxLayout()
        row.addWidget(QLabel("Размер"))
        self.size_combo = QComboBox()
        for size in available:
            self.size_combo.addItem(
                f"{size['size']} — доступно {size['quantity']} шт.",
                dict(size),
            )
        self.size_combo.currentIndexChanged.connect(self._update_quantity_limit)
        row.addWidget(self.size_combo)
        row.addWidget(QLabel("Количество"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        row.addWidget(self.quantity_spin)
        add_button = QPushButton("Добавить в заказ")
        add_button.clicked.connect(self.add_to_order)
        add_button.setEnabled(bool(available))
        row.addWidget(add_button)
        row.addStretch()
        layout.addLayout(row)
        self._update_quantity_limit()
        return layout

    def _update_quantity_limit(self, *_):
        if not hasattr(self, "quantity_spin"):
            return
        size = self.size_combo.currentData()
        self.quantity_spin.setMaximum(int(size["quantity"]) if size else 1)

    def add_to_order(self) -> None:
        size = self.size_combo.currentData()
        if not size:
            messages.show_error("Для этой модели нет доступных размеров.", "Заказ невозможен", self)
            return
        if self.controller.session.order_client is None:
            self.controller.session.order_client = self.controller.session.user
        item = DraftItem(
            stock_item_id=int(size["stock_item_id"]),
            product_id=int(self.product["product_id"]),
            product_name=self.product["name"],
            manufacturer=self.product["manufacturer"],
            size=str(size["size"]),
            quantity=self.quantity_spin.value(),
            available_quantity=int(size["quantity"]),
            unit_price=Decimal(self.product["discounted_price"]),
        )
        try:
            self.controller.session.order_draft.add(item)
        except ValueError as error:
            messages.show_error(str(error), "Некорректное количество", self)
            return
        self.controller.show_cart()
