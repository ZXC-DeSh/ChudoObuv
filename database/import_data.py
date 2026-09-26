from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg

from database.config import DatabaseSettings
from frames.importer import generate_database_sql, prepare_task2_data


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Проверка и импорт фактических данных TASK2.")
    parser.add_argument(
        "--resources",
        type=Path,
        default=PROJECT_ROOT / "database" / "resources" / "import",
        help="Каталог с пятью файлами *_import.xlsx.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Пересоздать таблицы и загрузить данные в PostgreSQL.",
    )
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    arguments = parse_arguments()
    prepared = prepare_task2_data(arguments.resources)
    print("Проверка файлов завершена:")
    for entity, count in prepared.counts.items():
        print(f"  {entity}: {count}")
    if not arguments.apply:
        print("База данных не изменена. Для импорта добавьте параметр --apply.")
        return 0

    sql_text = generate_database_sql(prepared, PROJECT_ROOT / "database" / "schema.sql")
    settings = DatabaseSettings.from_environment()
    with psycopg.connect(**settings.connection_parameters()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql_text, prepare=False)
    print("Структура и данные TASK2 загружены в PostgreSQL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
