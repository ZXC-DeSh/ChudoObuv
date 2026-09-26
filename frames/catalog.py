from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import messages
from components import HeaderWidget, ProductCard, create_page_title
from database import DatabaseError


class CatalogFrame(QFrame):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.database = controller.database
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.refresh_products)

        layout = QVBoxLayout(self)
        actions = []
        if controller.session.is_authenticated:
            actions.append(("Заказ", controller.show_cart))
        if controller.session.can_manage_orders:
            actions.append(("Список заказов", controller.show_orders))
        actions.append(("Выйти", controller.sign_out))
        layout.addWidget(HeaderWidget(controller, actions=actions))
        layout.addWidget(create_page_title("Каталог моделей обуви"))

        self.search_edit = None
        self.category_combo = None
        self.sort_combo = None
        if controller.session.is_authenticated:
            self._create_controls(layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        self.refresh_products()

    def _create_controls(self, parent_layout: QVBoxLayout) -> None:
        controls = QWidget()
        layout = QHBoxLayout(controls)

        layout.addWidget(QLabel("Поиск"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Наименование или описание")
        self.search_edit.textChanged.connect(self._schedule_refresh)
        layout.addWidget(self.search_edit, 2)

        layout.addWidget(QLabel("Категория"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("Все категории")
        try:
            self.category_combo.addItems(self.database.list_categories())
        except DatabaseError as error:
            messages.show_error(str(error), "Ошибка загрузки категорий", self)
        self.category_combo.currentIndexChanged.connect(self._schedule_refresh)
        layout.addWidget(self.category_combo, 1)

        layout.addWidget(QLabel("Цена"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("По возрастанию", "price_asc")
        self.sort_combo.addItem("По убыванию", "price_desc")
        self.sort_combo.currentIndexChanged.connect(self._schedule_refresh)
        layout.addWidget(self.sort_combo, 1)
        parent_layout.addWidget(controls)

    def _schedule_refresh(self, *_):
        self.search_timer.start(200)

    def refresh_products(self) -> None:
        search = self.search_edit.text() if self.search_edit else ""
        category = self.category_combo.currentText() if self.category_combo else "Все категории"
        sort_direction = self.sort_combo.currentData() if self.sort_combo else "price_asc"
        try:
            products = self.database.list_products(search, category, sort_direction)
        except DatabaseError as error:
            messages.show_error(str(error), "Ошибка загрузки каталога", self)
            products = []

        container = QWidget()
        layout = QVBoxLayout(container)
        if not products:
            label = QLabel("Товары не найдены")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        for product in products:
            card = ProductCard(product)
            card.clicked.connect(self.controller.show_product)
            layout.addWidget(card)
        layout.addStretch()
        self.scroll_area.setWidget(container)

    def on_show(self) -> None:
        self.refresh_products()
