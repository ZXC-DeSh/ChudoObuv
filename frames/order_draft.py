from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class DraftItem:
    stock_item_id: int
    product_id: int
    product_name: str
    manufacturer: str
    size: str
    quantity: int
    available_quantity: int
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


class OrderDraft:
    def __init__(self) -> None:
        self._items: dict[int, DraftItem] = {}

    @property
    def items(self) -> list[DraftItem]:
        return list(self._items.values())

    @property
    def total(self) -> Decimal:
        return sum((item.line_total for item in self._items.values()), Decimal("0.00"))

    def add(self, item: DraftItem) -> None:
        if item.quantity <= 0:
            raise ValueError("Количество должно быть больше нуля.")
        existing = self._items.get(item.stock_item_id)
        requested = item.quantity + (existing.quantity if existing else 0)
        if requested > item.available_quantity:
            raise ValueError(
                f"Недостаточно доступного количества для размера {item.size}. "
                f"Доступно: {item.available_quantity} шт."
            )
        if existing:
            existing.quantity = requested
            existing.available_quantity = item.available_quantity
            existing.unit_price = item.unit_price
        else:
            self._items[item.stock_item_id] = item

    def remove(self, stock_item_id: int) -> None:
        self._items.pop(stock_item_id, None)

    def clear(self) -> None:
        self._items.clear()

    def is_empty(self) -> bool:
        return not self._items

    def database_items(self) -> list[dict]:
        return [
            {"stock_item_id": item.stock_item_id, "quantity": item.quantity}
            for item in self._items.values()
        ]
