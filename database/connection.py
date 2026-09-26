from __future__ import annotations

import logging
from collections import defaultdict
from contextlib import contextmanager
from datetime import date
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row

from database.config import DatabaseSettings
from frames.pricing import previous_calendar_month


class DatabaseError(RuntimeError):
    pass


class DatabaseUnavailableError(DatabaseError):
    pass


class OrderValidationError(DatabaseError):
    pass


class InsufficientStockError(OrderValidationError):
    def __init__(self, size: str, available: int):
        super().__init__(
            f"Недостаточно доступного количества для размера {size}. "
            f"Доступно: {available} шт."
        )


class DatabaseConnection:
    def __init__(self, settings: DatabaseSettings | None = None):
        self.settings = settings or DatabaseSettings.from_environment()

    @contextmanager
    def _connect(self, *, row_factory=None):
        try:
            connection = psycopg.connect(
                **self.settings.connection_parameters(),
                row_factory=row_factory,
            )
        except psycopg.Error as error:
            raise DatabaseUnavailableError(
                "Не удалось подключиться к PostgreSQL. Проверьте параметры CHUDO_DB_* "
                "и убедитесь, что база данных создана."
            ) from error
        try:
            with connection:
                yield connection
        except DatabaseError:
            raise
        except psycopg.Error as error:
            logging.exception("Ошибка PostgreSQL")
            raise DatabaseError(f"Операция с базой данных не выполнена: {error}") from error
        finally:
            connection.close()

    def ping(self) -> bool:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone()[0] == 1

    def authenticate(self, login: str) -> dict | None:
        query = """
            SELECT
                user_id,
                login,
                role,
                concat_ws(' ', last_name, first_name, patronymic) AS full_name
            FROM users
            WHERE lower(login) = lower(%s)
        """
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (login.strip(),))
                return cursor.fetchone()

    def list_users(self) -> list[dict]:
        query = """
            SELECT
                user_id,
                login,
                role,
                concat_ws(' ', last_name, first_name, patronymic) AS full_name
            FROM users
            ORDER BY last_name, first_name, patronymic
        """
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()

    def list_categories(self) -> list[str]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
                return [row[0] for row in cursor.fetchall()]

    def list_products(
        self,
        search_text: str = "",
        category: str = "Все категории",
        sort_direction: str = "price_asc",
        calculation_date: date | None = None,
    ) -> list[dict]:
        calculation_date = calculation_date or date.today()
        previous_start, current_start = previous_calendar_month(calculation_date)
        filters = []
        parameters: list = [previous_start, current_start]
        if search_text.strip():
            filters.append("(p.name ILIKE %s OR p.description ILIKE %s)")
            needle = f"%{search_text.strip()}%"
            parameters.extend([needle, needle])
        if category and category != "Все категории":
            filters.append("p.category = %s")
            parameters.append(category)
        where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
        direction = "DESC" if sort_direction == "price_desc" else "ASC"
        query = f"""
            WITH stock AS (
                SELECT product_id, COALESCE(SUM(quantity), 0)::integer AS total_quantity
                FROM stock_items
                GROUP BY product_id
            ), ordered_previous_month AS (
                SELECT DISTINCT previous_stock.product_id
                FROM order_items previous_item
                JOIN orders previous_order ON previous_order.order_id = previous_item.order_id
                JOIN stock_items previous_stock
                    ON previous_stock.stock_item_id = previous_item.stock_item_id
                WHERE previous_order.order_date >= %s
                  AND previous_order.order_date < %s
            )
            SELECT
                p.product_id,
                p.category,
                p.subcategory,
                p.image_filename,
                p.name,
                p.manufacturer,
                p.description,
                p.composition,
                p.price,
                COALESCE(stock.total_quantity, 0) AS total_quantity,
                CASE WHEN previous.product_id IS NULL THEN 25 ELSE 0 END AS discount_percent,
                CASE
                    WHEN previous.product_id IS NULL THEN round(p.price * 0.75, 2)
                    ELSE p.price
                END AS discounted_price
            FROM products p
            LEFT JOIN stock ON stock.product_id = p.product_id
            LEFT JOIN ordered_previous_month previous ON previous.product_id = p.product_id
            {where_sql}
            ORDER BY discounted_price {direction}, p.name ASC
        """
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, tuple(parameters))
                return cursor.fetchall()

    def get_product(self, product_id: int, calculation_date: date | None = None) -> dict | None:
        calculation_date = calculation_date or date.today()
        previous_start, current_start = previous_calendar_month(calculation_date)
        product_query = """
            SELECT
                p.product_id,
                p.category,
                p.subcategory,
                p.image_filename,
                p.name,
                p.manufacturer,
                p.description,
                p.composition,
                p.price,
                COALESCE(SUM(si.quantity), 0)::integer AS total_quantity,
                CASE WHEN EXISTS (
                    SELECT 1
                    FROM order_items previous_item
                    JOIN orders previous_order ON previous_order.order_id = previous_item.order_id
                    JOIN stock_items previous_stock
                        ON previous_stock.stock_item_id = previous_item.stock_item_id
                    WHERE previous_stock.product_id = p.product_id
                      AND previous_order.order_date >= %s
                      AND previous_order.order_date < %s
                ) THEN 0 ELSE 25 END AS discount_percent,
                CASE WHEN EXISTS (
                    SELECT 1
                    FROM order_items previous_item
                    JOIN orders previous_order ON previous_order.order_id = previous_item.order_id
                    JOIN stock_items previous_stock
                        ON previous_stock.stock_item_id = previous_item.stock_item_id
                    WHERE previous_stock.product_id = p.product_id
                      AND previous_order.order_date >= %s
                      AND previous_order.order_date < %s
                ) THEN p.price ELSE round(p.price * 0.75, 2) END AS discounted_price
            FROM products p
            LEFT JOIN stock_items si ON si.product_id = p.product_id
            WHERE p.product_id = %s
            GROUP BY p.product_id
        """
        sizes_query = """
            SELECT si.stock_item_id, s.value AS size, si.quantity
            FROM stock_items si
            JOIN sizes s ON s.size_id = si.size_id
            WHERE si.product_id = %s
            ORDER BY
                CASE WHEN s.value ~ '^[0-9]+([.][0-9]+)?$' THEN s.value::numeric END,
                s.value
        """
        parameters = (
            previous_start,
            current_start,
            previous_start,
            current_start,
            product_id,
        )
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(product_query, parameters)
                product = cursor.fetchone()
                if not product:
                    return None
                cursor.execute(sizes_query, (product_id,))
                product["sizes"] = cursor.fetchall()
                return product

    def create_order(self, client_id: int, items: list[dict], order_date: date | None = None) -> dict:
        order_date = order_date or date.today()
        quantities: dict[int, int] = defaultdict(int)
        for item in items:
            stock_item_id = int(item.get("stock_item_id", 0))
            quantity = int(item.get("quantity", 0))
            if stock_item_id <= 0 or quantity <= 0:
                raise OrderValidationError("Количество каждой позиции должно быть больше нуля.")
            quantities[stock_item_id] += quantity
        if not quantities:
            raise OrderValidationError("Нельзя подтвердить пустой заказ.")

        previous_start, current_start = previous_calendar_month(order_date)
        locked_rows_query = """
            SELECT
                si.stock_item_id,
                si.quantity AS available_quantity,
                si.product_id,
                s.value AS size,
                p.name,
                CASE WHEN EXISTS (
                    SELECT 1
                    FROM order_items previous_item
                    JOIN orders previous_order ON previous_order.order_id = previous_item.order_id
                    JOIN stock_items previous_stock
                        ON previous_stock.stock_item_id = previous_item.stock_item_id
                    WHERE previous_stock.product_id = p.product_id
                      AND previous_order.order_date >= %s
                      AND previous_order.order_date < %s
                ) THEN p.price ELSE round(p.price * 0.75, 2) END AS unit_price
            FROM stock_items si
            JOIN products p ON p.product_id = si.product_id
            JOIN sizes s ON s.size_id = si.size_id
            WHERE si.stock_item_id = ANY(%s)
            FOR UPDATE OF si
        """
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (client_id,))
                if not cursor.fetchone():
                    raise OrderValidationError("Выбранный клиент не найден.")
                cursor.execute(
                    locked_rows_query,
                    (previous_start, current_start, list(quantities)),
                )
                locked_rows = {row["stock_item_id"]: row for row in cursor.fetchall()}
                if len(locked_rows) != len(quantities):
                    raise OrderValidationError("Одна из выбранных товарных позиций больше недоступна.")
                for stock_item_id, quantity in quantities.items():
                    stock = locked_rows[stock_item_id]
                    if quantity > stock["available_quantity"]:
                        raise InsufficientStockError(stock["size"], stock["available_quantity"])

                cursor.execute(
                    "INSERT INTO orders (order_date, client_id) VALUES (%s, %s) RETURNING order_id",
                    (order_date, client_id),
                )
                order_id = cursor.fetchone()["order_id"]
                total = Decimal("0.00")
                for stock_item_id, quantity in quantities.items():
                    stock = locked_rows[stock_item_id]
                    cursor.execute(
                        """
                            INSERT INTO order_items (order_id, stock_item_id, quantity, unit_price)
                            VALUES (%s, %s, %s, %s)
                        """,
                        (order_id, stock_item_id, quantity, stock["unit_price"]),
                    )
                    cursor.execute(
                        "UPDATE stock_items SET quantity = quantity - %s WHERE stock_item_id = %s",
                        (quantity, stock_item_id),
                    )
                    total += Decimal(stock["unit_price"]) * quantity
                return {"order_id": order_id, "total": total}

    def list_orders(self) -> list[dict]:
        query = """
            SELECT
                o.order_id,
                o.order_date,
                concat_ws(' ', u.last_name, u.first_name, u.patronymic) AS client_name,
                COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total
            FROM orders o
            JOIN users u ON u.user_id = o.client_id
            LEFT JOIN order_items oi ON oi.order_id = o.order_id
            GROUP BY o.order_id, u.user_id
            ORDER BY o.order_date DESC, o.order_id DESC
        """
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()

    def get_order(self, order_id: int) -> dict | None:
        order_query = """
            SELECT
                o.order_id,
                o.order_date,
                o.client_id,
                concat_ws(' ', u.last_name, u.first_name, u.patronymic) AS client_name
            FROM orders o
            JOIN users u ON u.user_id = o.client_id
            WHERE o.order_id = %s
        """
        items_query = """
            SELECT
                oi.order_item_id,
                p.name,
                p.manufacturer,
                s.value AS size,
                oi.quantity,
                oi.unit_price,
                oi.quantity * oi.unit_price AS line_total
            FROM order_items oi
            JOIN stock_items si ON si.stock_item_id = oi.stock_item_id
            JOIN products p ON p.product_id = si.product_id
            JOIN sizes s ON s.size_id = si.size_id
            WHERE oi.order_id = %s
            ORDER BY oi.order_item_id
        """
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(order_query, (order_id,))
                order = cursor.fetchone()
                if not order:
                    return None
                cursor.execute(items_query, (order_id,))
                order["items"] = cursor.fetchall()
                order["total"] = sum(
                    (Decimal(item["line_total"]) for item in order["items"]),
                    Decimal("0.00"),
                )
                return order

    def update_order_date(self, order_id: int, new_date: date) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE orders SET order_date = %s WHERE order_id = %s",
                    (new_date, order_id),
                )
                if cursor.rowcount != 1:
                    raise OrderValidationError("Заказ не найден.")

    def remove_order_item(self, order_id: int, order_item_id: int) -> None:
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) AS count FROM order_items WHERE order_id = %s",
                    (order_id,),
                )
                if cursor.fetchone()["count"] <= 1:
                    raise OrderValidationError(
                        "Нельзя удалить последнюю позицию. Удалите заказ целиком."
                    )
                cursor.execute(
                    """
                        SELECT stock_item_id, quantity
                        FROM order_items
                        WHERE order_id = %s AND order_item_id = %s
                        FOR UPDATE
                    """,
                    (order_id, order_item_id),
                )
                item = cursor.fetchone()
                if not item:
                    raise OrderValidationError("Позиция заказа не найдена.")
                cursor.execute(
                    "UPDATE stock_items SET quantity = quantity + %s WHERE stock_item_id = %s",
                    (item["quantity"], item["stock_item_id"]),
                )
                cursor.execute(
                    "DELETE FROM order_items WHERE order_item_id = %s",
                    (order_item_id,),
                )

    def delete_order(self, order_id: int) -> None:
        with self._connect(row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                        SELECT stock_item_id, quantity
                        FROM order_items
                        WHERE order_id = %s
                        FOR UPDATE
                    """,
                    (order_id,),
                )
                items = cursor.fetchall()
                if not items:
                    cursor.execute("SELECT 1 FROM orders WHERE order_id = %s", (order_id,))
                    if not cursor.fetchone():
                        raise OrderValidationError("Заказ не найден.")
                for item in items:
                    cursor.execute(
                        "UPDATE stock_items SET quantity = quantity + %s WHERE stock_item_id = %s",
                        (item["quantity"], item["stock_item_id"]),
                    )
                cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
