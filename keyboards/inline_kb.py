from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any

def get_packages_keyboard(packages: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Инлайн-кнопки со списком пакетов Stars"""
    keyboard = []
    for pkg in packages:
        stars = pkg["stars"]
        price = pkg["price"]
        formatted_price = f"{price:,}".replace(",", " ")
        keyboard.append([
            InlineKeyboardButton(
                text=f"{stars} ⭐ — {formatted_price} сум",
                callback_data=f"buy_stars:{stars}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def cancel_order_keyboard() -> InlineKeyboardMarkup:
    """Кнопка отмены при отправке чека"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_action")]
        ]
    )


def get_order_admin_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Кнопки для администратора под карточкой нового заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_order_accept:{order_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_order_reject:{order_id}")
            ]
        ]
    )


def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главная панель администратора"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="💰 Управление ценами", callback_data="admin_prices")],
            [InlineKeyboardButton(text="💳 Реквизиты оплаты", callback_data="admin_requisites")],
            [InlineKeyboardButton(text="📝 Тексты (Инфо/Контакты)", callback_data="admin_texts")],
            [InlineKeyboardButton(text="📢 Рассылка пользователям", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🔙 Закрыть админку", callback_data="admin_close")]
        ]
    )


def admin_prices_keyboard(packages: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Выбор пакета для редактирования цены"""
    keyboard = []
    for pkg in packages:
        stars = pkg["stars"]
        price = pkg["price"]
        keyboard.append([
            InlineKeyboardButton(
                text=f"✏️ {stars} ⭐ (сейчас {price:,} сум)",
                callback_data=f"admin_edit_price:{stars}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_texts_keyboard() -> InlineKeyboardMarkup:
    """Меню редактирования текстов"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ «Как купить»", callback_data="admin_edit_text:how_to_buy")],
            [InlineKeyboardButton(text="✏️ «Правила»", callback_data="admin_edit_text:rules")],
            [InlineKeyboardButton(text="✏️ «Связаться с продавцом»", callback_data="admin_edit_text:seller_contact")],
            [InlineKeyboardButton(text="✏️ «Поддержка»", callback_data="admin_edit_text:support_contact")],
            [InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_back_to_main")]
        ]
    )
