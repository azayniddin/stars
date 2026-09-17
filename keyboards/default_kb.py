from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Главное меню по ТЗ клиента:
    ⭐ Купить Stars
    💰 Цены
    📋 Как купить
    🆘 Поддержка
    📜 Правила
    👤 Связаться с продавцом
    """
    kb = [
        [KeyboardButton(text="⭐ Купить Stars")],
        [KeyboardButton(text="💰 Цены"), KeyboardButton(text="📋 Как купить")],
        [KeyboardButton(text="🆘 Поддержка"), KeyboardButton(text="📜 Правила")],
        [KeyboardButton(text="👤 Связаться с продавцом")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие из меню..."
    )
