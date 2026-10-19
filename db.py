import sqlite3
import os
from tkinter import messagebox

DB_PATH = "recipes.db"
INIT_SQL_PATH = "init.sql"

def get_connection():
    """Возвращает подключение к БД с включенными внешними ключами."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по имени (row['title'])
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Создаёт БД из init.sql, если файла ещё нет."""
    if not os.path.exists(DB_PATH):
        if not os.path.exists(INIT_SQL_PATH):
            messagebox.showerror("Ошибка", f"Не найден файл {INIT_SQL_PATH}! Положите его в папку с программой.")
            return False
        try:
            conn = get_connection()
            with open(INIT_SQL_PATH, "r", encoding="cp1251") as f:
                conn.executescript(f.read())
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            messagebox.showerror("Ошибка БД", f"Не удалось создать БД:\n{e}")
            return False
    return True