from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from components.common import load_product_pixmap


def format_money(value) -> str:
    return f"{Decimal(value):,.2f}".replace(",", " ") + " руб."


def availability_text(quantity: int) -> str:
    return "много" if quantity > 5 else "мало"


def is_low_stock(quantity: int) -> bool:
    return quantity <= 3


class ProductCard(QFrame):
    clicked = Signal(int)

    def __init__(self, product: dict):
        super().__init__(objectName="product_card")
        self.product_id = int(product["product_id"])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("low_stock", is_low_stock(int(product["total_quantity"])))
        self.setMinimumHeight(230)

        layout = QHBoxLayout(self)
        image = QLabel()
        image.setFixedSize(180, 180)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = load_product_pixmap(product.get("image_filename"), 175, 175)
        if pixmap.isNull():
            image.setText("Изображение недоступно")
        else:
            image.setPixmap(pixmap)
        layout.addWidget(image)

        details = QVBoxLayout()
        name = QLabel(product["name"], objectName="product_name")
        name.setWordWrap(True)
        details.addWidget(name)
        details.addWidget(QLabel(f"{product['manufacturer']} | {product['category']}"))

        composition = QLabel(f"Состав: {product['composition']}")
        composition.setWordWrap(True)
        details.addWidget(composition)
        description = QLabel(f"Описание: {product['description']}")
        description.setWordWrap(True)
        details.addWidget(description)

        quantity = int(product["total_quantity"])
        amount_word = availability_text(quantity)
        details.addWidget(QLabel(f"Доступно: {amount_word} ({quantity} пар)"))
        layout.addLayout(details, 1)

        price_layout = QVBoxLayout()
        if int(product["discount_percent"]) == 25:
            original = format_money(product["price"])
            price_layout.addWidget(QLabel(f"<s>{original}</s>"))
            price_layout.addWidget(
                QLabel(format_money(product["discounted_price"]), objectName="price")
            )
            price_layout.addWidget(QLabel("Скидка 25%"))
        else:
            price_layout.addWidget(QLabel(format_money(product["price"]), objectName="price"))
        price_layout.addStretch()
        layout.addLayout(price_layout)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.product_id)
        super().mouseReleaseEvent(event)
