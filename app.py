from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

import messages
from database import DatabaseConnection
from frames import (
    CartFrame,
    CatalogFrame,
    LoginFrame,
    OrderClientFrame,
    OrderDetailFrame,
    OrdersFrame,
    ProductDetailFrame,
)
from storage import AppSession
from styles import STYLE_SHEET


PROJECT_ROOT = Path(__file__).resolve().parent


class MainWindow(QMainWindow):
    def __init__(self, database: DatabaseConnection | None = None):
        super().__init__()
        self.setWindowTitle("Чудо Обувь — система оформления заказов")
        self.setMinimumSize(1050, 760)
        self.resize(1280, 850)
        self.database = database or DatabaseConnection()
        self.session = AppSession()
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.frames: dict[str, object] = {}
        self.show_login(recreate=True)

    def _show(self, key: str, factory, *, recreate: bool = False):
        if recreate and key in self.frames:
            old_frame = self.frames.pop(key)
            self.stack.removeWidget(old_frame)
            old_frame.deleteLater()
        frame = self.frames.get(key)
        if frame is None:
            frame = factory()
            self.frames[key] = frame
            self.stack.addWidget(frame)
        self.stack.setCurrentWidget(frame)
        if not recreate and hasattr(frame, "on_show"):
            frame.on_show()

    def show_login(self, *, recreate: bool = False):
        self._show("login", lambda: LoginFrame(self), recreate=recreate)

    def show_catalog(self, *, recreate: bool = False):
        self._show("catalog", lambda: CatalogFrame(self), recreate=recreate)

    def show_product(self, product_id: int):
        self._show(
            "product_detail",
            lambda: ProductDetailFrame(self, product_id),
            recreate=True,
        )

    def show_cart(self):
        if not self.session.is_authenticated:
            messages.show_warning(
                "Оформление заказа доступно после входа по логину.",
                "Требуется авторизация",
                self,
            )
            return
        self._show("cart", lambda: CartFrame(self), recreate=True)

    def show_orders(self):
        if not self.session.can_manage_orders:
            messages.show_error(
                "Список заказов доступен только менеджеру и администратору.",
                "Недостаточно прав",
                self,
            )
            return
        self._show("orders", lambda: OrdersFrame(self))

    def show_order_client(self):
        if not self.session.can_manage_orders:
            return
        self._show("order_client", lambda: OrderClientFrame(self), recreate=True)

    def show_order(self, order_id: int):
        if not self.session.can_manage_orders:
            return
        self._show(
            "order_detail",
            lambda: OrderDetailFrame(self, order_id),
            recreate=True,
        )

    def sign_out(self):
        if not self.session.order_draft.is_empty() and not messages.ask_confirmation(
            "В незавершённом заказе есть позиции. Выйти и удалить их?",
            "Незавершённый заказ",
            self,
        ):
            return
        self.session.sign_out()
        for key, frame in list(self.frames.items()):
            if key == "login":
                continue
            self.stack.removeWidget(frame)
            frame.deleteLater()
            self.frames.pop(key, None)
        self.show_login(recreate=True)

    def closeEvent(self, event) -> None:
        if self.session.order_draft.is_empty():
            event.accept()
            return
        if messages.ask_confirmation(
            "Закрыть приложение? Незавершённый заказ не будет сохранён.",
            "Незавершённый заказ",
            self,
        ):
            event.accept()
        else:
            event.ignore()


def create_application(argv=None) -> QApplication:
    application = QApplication(argv if argv is not None else sys.argv)
    application.setApplicationName("Чудо Обувь")
    application.setOrganizationName("Чудо Обувь")
    if "Calibri" not in QFontDatabase.families():
        fonts_dir = Path(os.getenv("WINDIR", r"C:\Windows")) / "Fonts"
        for filename in ("calibri.ttf", "calibrib.ttf", "calibrii.ttf"):
            font_path = fonts_dir / filename
            if font_path.is_file():
                QFontDatabase.addApplicationFont(str(font_path))
    application.setFont(QFont("Calibri", 11))
    application.setStyleSheet(STYLE_SHEET)
    icon_path = PROJECT_ROOT / "resources" / "app.ico"
    if icon_path.is_file():
        application.setWindowIcon(QIcon(str(icon_path)))
    return application


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    application = create_application()
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
