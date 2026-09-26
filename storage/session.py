from __future__ import annotations

from dataclasses import dataclass

from services.order_draft import OrderDraft


AUTHORIZED_ROLE = "Авторизованный пользователь"
MANAGER_ROLE = "Менеджер"
ADMIN_ROLE = "Администратор"


@dataclass(frozen=True)
class UserSession:
    user_id: int
    login: str
    full_name: str
    role: str


class AppSession:
    def __init__(self) -> None:
        self.user: UserSession | None = None
        self.order_draft = OrderDraft()
        self.order_client: UserSession | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    @property
    def can_order(self) -> bool:
        return self.user is not None

    @property
    def can_manage_orders(self) -> bool:
        return bool(self.user and self.user.role in {MANAGER_ROLE, ADMIN_ROLE})

    @property
    def is_admin(self) -> bool:
        return bool(self.user and self.user.role == ADMIN_ROLE)

    @property
    def display_name(self) -> str:
        return self.user.full_name if self.user else "Неавторизованный пользователь"

    def sign_in(self, user_data: dict) -> None:
        self.user = UserSession(
            user_id=int(user_data["user_id"]),
            login=str(user_data["login"]),
            full_name=str(user_data["full_name"]),
            role=str(user_data["role"]),
        )
        self.order_client = self.user
        self.order_draft.clear()

    def enter_as_guest(self) -> None:
        self.user = None
        self.order_client = None
        self.order_draft.clear()

    def select_order_client(self, user_data: dict) -> None:
        self.order_client = UserSession(
            user_id=int(user_data["user_id"]),
            login=str(user_data["login"]),
            full_name=str(user_data["full_name"]),
            role=str(user_data["role"]),
        )
        self.order_draft.clear()

    def sign_out(self) -> None:
        self.enter_as_guest()
