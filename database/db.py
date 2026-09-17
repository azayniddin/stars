import aiosqlite
from typing import List, Optional, Tuple, Dict, Any
from config import DB_PATH

DEFAULT_PACKAGES = [
    (50, 14000),
    (100, 28000),
    (250, 70000),
    (500, 140000),
    (1000, 280000),
]

DEFAULT_SETTINGS = {
    "payment_card": "8600 0000 0000 0000 (HUMO / UZCARD)",
    "seller_contact": "@stars_seller",
    "support_contact": "@stars_support",
    "how_to_buy": (
        "📋 <b>Инструкция по покупке Stars:</b>\n\n"
        "1️⃣ Нажмите <b>«⭐ Купить Stars»</b> в меню.\n"
        "2️⃣ Выберите желаемое количество Stars (например: 100 ⭐).\n"
        "3️⃣ Переведите точную сумму на указанные реквизиты.\n"
        "4️⃣ Отправьте фото (скриншот) чека об оплате в чат с ботом.\n"
        "5️⃣ Дождитесь проверки администратором, и Stars поступят на ваш аккаунт!"
    ),
    "rules": (
        "📜 <b>Правила сервиса:</b>\n\n"
        "• Все платежи принимаются в национальной валюте (UZS).\n"
        "• Всегда сохраняйте чек до полного зачисления Stars.\n"
        "• В случае спорных вопросов обращайтесь в <b>«Поддержку»</b> с чеком оплаты.\n"
        "• Обработка заказов занимает от 5 до 15 минут в рабочее время."
    ),
}

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица пакетов Stars
        await db.execute("""
            CREATE TABLE IF NOT EXISTS packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stars INTEGER UNIQUE,
                price INTEGER,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Таблица заказов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                stars INTEGER,
                price INTEGER,
                receipt_file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица настроек
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Добавляем стандартные пакеты если пусто
        async with db.execute("SELECT COUNT(*) FROM packages") as cursor:
            count = (await cursor.fetchone())[0]
            if count == 0:
                for stars, price in DEFAULT_PACKAGES:
                    await db.execute(
                        "INSERT INTO packages (stars, price) VALUES (?, ?)",
                        (stars, price)
                    )

        # Добавляем стандартные настройки если пусто
        for key, val in DEFAULT_SETTINGS.items():
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, val)
            )

        await db.commit()


class Database:
    @staticmethod
    async def add_user(user_id: int, username: Optional[str], full_name: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
                (user_id, username, full_name)
            )
            await db.commit()

    @staticmethod
    async def get_all_users() -> List[int]:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                rows = await cursor.fetchall()
                return [r[0] for r in rows]

    @staticmethod
    async def get_users_count() -> int:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    @staticmethod
    async def get_packages() -> List[Dict[str, Any]]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM packages WHERE is_active = 1 ORDER BY stars ASC") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    @staticmethod
    async def get_package_by_stars(stars: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM packages WHERE stars = ?", (stars,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    @staticmethod
    async def update_package_price(stars: int, new_price: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO packages (stars, price, is_active) VALUES (?, ?, 1) "
                "ON CONFLICT(stars) DO UPDATE SET price = excluded.price, is_active = 1",
                (stars, new_price)
            )
            await db.commit()

    @staticmethod
    async def create_order(user_id: int, username: Optional[str], full_name: str, stars: int, price: int, receipt_file_id: str) -> int:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "INSERT INTO orders (user_id, username, full_name, stars, price, receipt_file_id, status) VALUES (?, ?, ?, ?, ?, ?, 'pending')",
                (user_id, username, full_name, stars, price, receipt_file_id)
            )
            await db.commit()
            return cursor.lastrowid

    @staticmethod
    async def get_order(order_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    @staticmethod
    async def update_order_status(order_id: int, status: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
            await db.commit()

    @staticmethod
    async def get_orders_stats() -> Dict[str, Any]:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM orders") as cursor:
                total_orders = (await cursor.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'") as cursor:
                pending_orders = (await cursor.fetchone())[0]
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(price), 0), COALESCE(SUM(stars), 0) FROM orders WHERE status = 'approved'") as cursor:
                row = await cursor.fetchone()
                approved_orders, total_revenue, total_stars = row[0], row[1], row[2]

            return {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "approved_orders": approved_orders,
                "total_revenue": total_revenue,
                "total_stars": total_stars
            }

    @staticmethod
    async def get_setting(key: str, default: str = "") -> str:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else default

    @staticmethod
    async def set_setting(key: str, value: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value)
            )
            await db.commit()
