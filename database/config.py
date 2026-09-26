from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_environment(cls) -> "DatabaseSettings":
        return cls(
            host=os.getenv("CHUDO_DB_HOST", "127.0.0.1"),
            port=int(os.getenv("CHUDO_DB_PORT", "5432")),
            database=os.getenv("CHUDO_DB_NAME", "chudo_obuv"),
            user=os.getenv("CHUDO_DB_USER", "postgres"),
            password=os.getenv("CHUDO_DB_PASSWORD", "67909141"),
        )

    def connection_parameters(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
            "password": self.password,
            "connect_timeout": 5,
        }
