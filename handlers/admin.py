from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import Database
from keyboards.inline_kb import (
    admin_main_keyboard,
    admin_prices_keyboard,
    admin_texts_keyboard
)
from config import ADMIN_IDS

admin_router = Router()

class AdminStates(StatesGroup):
    waiting_for_price = State()
    waiting_for_card = State()
    waiting_for_text = State()
    waiting_for_broadcast = State()

def is_admin(user_id: int) -> bool:
    # Если список админов задан, проверяем наличие ID
    return user_id in ADMIN_IDS

@admin_router.message(Command("myid"))
async def cmd_myid(message: Message):
    """Помощник: показывает пользователю его Telegram ID"""
    user = message.from_user
    await message.answer(
        f"Ваш Telegram ID: <code>{user.id}</code>\n"
        "Скопируйте его и вставьте в файл <code>.env</code> в поле <code>ADMIN_IDS=</code>",
        parse_mode="HTML"
    )

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    if not ADMIN_IDS:
        await message.answer(
            f"⚠️ <b>Внимание!</b> Список администраторов пуст.\n"
            f"Ваш Telegram ID: <code>{user_id}</code>\n\n"
            "Добавьте ваш ID в файл <code>.env</code>:\n"
            f"<code>ADMIN_IDS={user_id}</code>\n"
            "После сохранения перезапустите бота.",
            parse_mode="HTML"
        )
        return

    if not is_admin(user_id):
        await message.answer("⛔️ У вас нет прав доступа к панели администратора.")
        return

    await message.answer(
        "🛠 <b>Панель управления администратора</b>\n\n"
        "Выберите раздел для настройки бота 👇",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "admin_back_to_main")
async def cb_admin_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🛠 <b>Панель управления администратора</b>\n\n"
        "Выберите раздел для настройки бота 👇",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_close")
async def cb_admin_close(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Админ-панель закрыта")


# --- СТАТИСТИКА ---
@admin_router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    users_count = await Database.get_users_count()
    stats = await Database.get_orders_stats()

    rev = f"{stats['total_revenue']:,}".replace(",", " ")
    stars_sold = f"{stats['total_stars']:,}".replace(",", " ")

    text = (
        "📊 <b>Статистика сервиса:</b>\n\n"
        f"👥 <b>Всего пользователей в боте:</b> {users_count}\n"
        f"📦 <b>Всего заказов:</b> {stats['total_orders']}\n"
        f"⏳ <b>Ожидают проверки:</b> {stats['pending_orders']}\n"
        f"✅ <b>Успешно выполнено:</b> {stats['approved_orders']}\n\n"
        f"⭐ <b>Всего продано Stars:</b> {stars_sold} ⭐\n"
        f"💰 <b>Общая сумма продаж:</b> {rev} сум\n"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_main")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# --- УПРАВЛЕНИЕ ЦЕНАМИ ---
@admin_router.callback_query(F.data == "admin_prices")
async def cb_admin_prices(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    packages = await Database.get_packages()
    text = (
        "💰 <b>Управление ценами на Stars</b>\n\n"
        "Нажмите на пакет, цену которого вы хотите изменить:"
    )
    await callback.message.edit_text(text, reply_markup=admin_prices_keyboard(packages), parse_mode="HTML")
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_edit_price:"))
async def cb_admin_edit_price(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    stars = int(callback.data.split(":")[1])
    package = await Database.get_package_by_stars(stars)

    await state.set_state(AdminStates.waiting_for_price)
    await state.update_data(editing_stars=stars)

    current_price = f"{package['price']:,}".replace(",", " ")
    text = (
        f"✏️ <b>Изменение цены для пакета: {stars} ⭐</b>\n\n"
        f"Текущая цена: <b>{current_price} сум</b>\n\n"
        "Введите <b>новую цену в сумах</b> (только цифры, например: <code>30000</code>):"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_prices")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@admin_router.message(AdminStates.waiting_for_price)
async def process_new_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    new_price_str = message.text.strip().replace(" ", "")
    if not new_price_str.isdigit() or int(new_price_str) <= 0:
        await message.answer("⚠️ Пожалуйста, введите корректное положительное число (например: <code>30000</code>):", parse_mode="HTML")
        return

    new_price = int(new_price_str)
    data = await state.get_data()
    stars = data.get("editing_stars")

    await Database.update_package_price(stars, new_price)
    await state.clear()

    formatted_price = f"{new_price:,}".replace(",", " ")
    await message.answer(
        f"✅ Цена для <b>{stars} ⭐</b> успешно изменена на <b>{formatted_price} сум</b>!",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )


# --- УПРАВЛЕНИЕ РЕКВИЗИТАМИ ---
@admin_router.callback_query(F.data == "admin_requisites")
async def cb_admin_requisites(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    current_card = await Database.get_setting("payment_card")
    await state.set_state(AdminStates.waiting_for_card)

    text = (
        "💳 <b>Настройка реквизитов для оплаты</b>\n\n"
        f"Текущие реквизиты:\n<code>{current_card}</code>\n\n"
        "Отправьте новые реквизиты сообщением (номер карты, банк или имя получателя):"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back_to_main")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@admin_router.message(AdminStates.waiting_for_card)
async def process_new_card(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    new_card = message.text.strip()
    await Database.set_setting("payment_card", new_card)
    await state.clear()

    await message.answer(
        f"✅ Новые платежные реквизиты сохранены:\n<code>{new_card}</code>",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )


# --- УПРАВЛЕНИЕ ТЕКСТАМИ ---
@admin_router.callback_query(F.data == "admin_texts")
async def cb_admin_texts(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    text = "📝 <b>Выберите раздел, текст которого хотите изменить:</b>"
    await callback.message.edit_text(text, reply_markup=admin_texts_keyboard(), parse_mode="HTML")
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_edit_text:"))
async def cb_admin_edit_text(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    text_key = callback.data.split(":")[1]
    current_val = await Database.get_setting(text_key)

    names = {
        "how_to_buy": "«Как купить»",
        "rules": "«Правила»",
        "seller_contact": "«Связаться с продавцом»",
        "support_contact": "«Поддержка»"
    }

    await state.set_state(AdminStates.waiting_for_text)
    await state.update_data(editing_text_key=text_key)

    text = (
        f"✏️ <b>Редактирование раздела: {names.get(text_key, text_key)}</b>\n\n"
        f"<b>Текущий текст:</b>\n{current_val}\n\n"
        "Отправьте новый текст следующим сообщением (поддерживается форматирование HTML):"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_texts")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@admin_router.message(AdminStates.waiting_for_text)
async def process_new_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    text_key = data.get("editing_text_key")
    new_text = message.html_text or message.text

    await Database.set_setting(text_key, new_text)
    await state.clear()

    await message.answer(
        "✅ Текст успешно обновлён!",
        reply_markup=admin_main_keyboard()
    )


# --- РАССЫЛКА ---
@admin_router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return

    users_count = await Database.get_users_count()
    await state.set_state(AdminStates.waiting_for_broadcast)

    text = (
        "📢 <b>Массовая рассылка сообщений</b>\n\n"
        f"Количество получателей: <b>{users_count} пользователей</b>.\n\n"
        "Отправьте сообщение (текст, фото или пост), которое нужно разослать всем:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back_to_main")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@admin_router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    users = await Database.get_all_users()
    
    status_msg = await message.answer(f"⏳ Рассылка запущена для {len(users)} пользователей...")

    success = 0
    failed = 0

    for uid in users:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"Доставлено: <b>{success}</b>\n"
        f"Не доставлено (заблокировали бота): <b>{failed}</b>",
        parse_mode="HTML"
    )


# --- ОБРАБОТКА ЗАКАЗОВ (ПОДТВЕРЖДЕНИЕ / ОТКЛОНЕНИЕ) ---
@admin_router.callback_query(F.data.startswith("admin_order_accept:"))
async def cb_order_accept(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет прав подтверждать заказы.", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])
    order = await Database.get_order(order_id)

    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    if order["status"] != "pending":
        await callback.answer(f"Этот заказ уже имеет статус: {order['status']}", show_alert=True)
        return

    await Database.update_order_status(order_id, "approved")

    # Обновляем сообщение у администратора
    formatted_price = f"{order['price']:,}".replace(",", " ")
    admin_name = callback.from_user.full_name
    new_caption = (
        f"✅ <b>ЗАКАЗ #{order_id} УСПЕШНО ПОДТВЕРЖДЁН!</b>\n\n"
        f"👤 <b>Покупатель:</b> {order['full_name']} (@{order['username'] or 'нет'} | ID: <code>{order['user_id']}</code>)\n"
        f"⭐️ <b>Количество:</b> {order['stars']} Stars\n"
        f"💰 <b>Сумма:</b> {formatted_price} сум\n"
        f"👨‍💻 <b>Подтвердил:</b> {admin_name}\n"
        f"📅 <b>Статус:</b> ✅ Выполнен"
    )
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML")
    except Exception:
        pass

    # Уведомляем покупателя
    try:
        user_msg = (
            f"🎉 <b>Ваш заказ #{order_id} выполнен!</b>\n\n"
            f"⭐️ <b>{order['stars']} Stars</b> зачислены на ваш аккаунт!\n\n"
            "Спасибо за покупку! Будем рады видеть вас снова. ✨"
        )
        await bot.send_message(chat_id=order["user_id"], text=user_msg, parse_mode="HTML")
    except Exception as e:
        print(f"Не удалось уведомить пользователя {order['user_id']}: {e}")

    await callback.answer("Заказ подтверждён!", show_alert=True)


@admin_router.callback_query(F.data.startswith("admin_order_reject:"))
async def cb_order_reject(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет прав отклонять заказы.", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])
    order = await Database.get_order(order_id)

    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    if order["status"] != "pending":
        await callback.answer(f"Этот заказ уже имеет статус: {order['status']}", show_alert=True)
        return

    await Database.update_order_status(order_id, "rejected")

    # Обновляем сообщение у администратора
    formatted_price = f"{order['price']:,}".replace(",", " ")
    admin_name = callback.from_user.full_name
    new_caption = (
        f"❌ <b>ЗАКАЗ #{order_id} ОТКЛОНЁН!</b>\n\n"
        f"👤 <b>Покупатель:</b> {order['full_name']} (@{order['username'] or 'нет'} | ID: <code>{order['user_id']}</code>)\n"
        f"⭐️ <b>Количество:</b> {order['stars']} Stars\n"
        f"💰 <b>Сумма:</b> {formatted_price} сум\n"
        f"👨‍💻 <b>Отклонил:</b> {admin_name}\n"
        f"📅 <b>Статус:</b> ❌ Отклонён"
    )
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML")
    except Exception:
        pass

    # Уведомляем покупателя
    support_contact = await Database.get_setting("support_contact", "@stars_support")
    try:
        user_msg = (
            f"❌ <b>Ваш заказ #{order_id} был отклонён администратором.</b>\n\n"
            "Причина может быть связана с неверной суммой перевода или нечитаемым чеком.\n"
            f"Если произошла ошибка, пожалуйста, напишите в поддержку: <b>{support_contact}</b>"
        )
        await bot.send_message(chat_id=order["user_id"], text=user_msg, parse_mode="HTML")
    except Exception as e:
        print(f"Не удалось уведомить пользователя {order['user_id']}: {e}")

    await callback.answer("Заказ отклонён!", show_alert=True)
