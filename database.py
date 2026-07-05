# -*- coding: utf-8 -*-
"""
database.py
Хранение истории обработанных запросов в базе данных SQLite.
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "history.db"


def init_db() -> None:
    """Создать таблицу истории, если она ещё не существует."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS requests (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp  TEXT    NOT NULL,
            filename   TEXT    NOT NULL,
            count      INTEGER NOT NULL,
            result     TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_request(filename: str, stats: dict) -> None:
    """Сохранить один запрос в историю."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO requests (timestamp, filename, count, result) VALUES (?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
         filename,
         stats["count"],
         json.dumps(stats, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 50) -> list:
    """Получить последние записи истории (для вывода и отчётов)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, timestamp, filename, count FROM requests "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
