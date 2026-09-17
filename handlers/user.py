from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import Database
from keyboards.default_kb import main_menu_keyboard
from keyboards.inline_kb import (
    get_packages_keyboard,
    cancel_order_keyboard,
    get_order_admin_keyboard
)
from config import ADMIN_IDS

user_router = Router()

class OrderStates(StatesGroup):
    waiting_for_receipt = State()

@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await Database.add_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    welcome_text = (
        f"Здравствуйте, <b>{user.first_name}</b>! 👋\n\n"
        "Добро пожаловать в сервис по покупке <b>Telegram Stars</b> ⭐️\n\n"
        "У нас вы можете быстро, безопасно и выгодно приобрести звёзды для любых целей.\n"
        "Выберите нужное действие в меню ниже 👇"
    )
    await message.answer(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")


@user_router.message(F.text == "⭐ Купить Stars")
async def btn_buy_stars(message: Message):
    packages = await Database.get_packages()
    if not packages:
        await message.answer("В данный момент пакеты Stars недоступны. Обратитесь к администратору.")
        return

    text = (
        "⭐️ <b>Выберите желаемое количество Stars:</b>\n\n"
        "Нажмите на подходящий пакет ниже для перехода к оплате 👇"
    )
    await message.answer(text, reply_markup=get_packages_keyboard(packages), parse_mode="HTML")


@user_router.message(F.text == "💰 Цены")
async def btn_prices(message: Message):
    packages = await Database.get_packages()
    text = "💰 <b>Актуальные цены на Telegram Stars:</b>\n\n"
    for pkg in packages:
        stars = pkg["stars"]
        price = f"{pkg['price']:,}".replace(",", " ")
        text += f"• <b>{stars} ⭐</b> — {price} сум\n"
    
    text += "\n<i>Для заказа перейдите в раздел «⭐ Купить Stars»</i>"
    await message.answer(text, parse_mode="HTML")


@user_router.message(F.text == "📋 Как купить")
async def btn_how_to_buy(message: Message):
    text = await Database.get_setting("how_to_buy")
    await message.answer(text, parse_mode="HTML")


@user_router.message(F.text == "📜 Правила")
async def btn_rules(message: Message):
    text = await Database.get_setting("rules")
    await message.answer(text, parse_mode="HTML")


@user_router.message(F.text == "🆘 Поддержка")
async def btn_support(message: Message):
    contact = await Database.get_setting("support_contact", "@stars_support")
    clean_username = contact.replace("@", "").replace("https://t.me/", "")
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать в поддержку", url=f"https://t.me/{clean_username}")]
        ]
    )
    text = (
        "🆘 <b>Служба поддержки</b>\n\n"
        "Если у вас возникли вопросы по оплате, получению Stars или работе сервиса, "
        f"напишите нашему специалисту: <b>{contact}</b>.\n\n"
        "Мы всегда рады вам помочь!"
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@user_router.message(F.text == "👤 Связаться с продавцом")
async def btn_seller(message: Message):
    contact = await Database.get_setting("seller_contact", "@stars_seller")
    clean_username = contact.replace("@", "").replace("https://t.me/", "")
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Связаться с продавцом", url=f"https://t.me/{clean_username}")]
        ]
    )
    text = (
        "👤 <b>Связь с продавцом</b>\n\n"
        f"По всем прямым вопросам и индивидуальным заказам обращайтесь к: <b>{contact}</b>"
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@user_router.callback_query(F.data.startswith("buy_stars:"))
async def cb_buy_stars(callback: CallbackQuery, state: FSMContext):
    stars = int(callback.data.split(":")[1])
    package = await Database.get_package_by_stars(stars)

    if not package:
        await callback.answer("Ошибка: данный пакет не найден.", show_alert=True)
        return

    price = package["price"]
    formatted_price = f"{price:,}".replace(",", " ")
    payment_card = await Database.get_setting("payment_card", "8600 0000 0000 0000")

    await state.set_state(OrderStates.waiting_for_receipt)
    await state.update_data(stars=stars, price=price)

    text = (
        f"⭐️ <b>Оформление заказа: {stars} Stars</b>\n\n"
        f"💵 <b>Сумма к оплате:</b> {formatted_price} сум\n\n"
        f"💳 <b>Реквизиты для оплаты:</b>\n"
        f"<code>{payment_card}</code>\n"
        f"<i>(нажмите на номер карты, чтобы скопировать)</i>\n\n"
        "❗️ <b>После оплаты:</b>\n"
        "Пожалуйста, <b>отправьте фото (скриншот) чека</b> в этот чат.\n\n"
        "<i>Как только вы отправите чек, уведомление сразу же поступит продавцу.</i>"
    )
    await callback.message.edit_text(text, reply_markup=cancel_order_keyboard(), parse_mode="HTML")
    await callback.answer()


@user_router.callback_query(F.data == "cancel_action")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "Действие отменено. Главное меню доступно ниже:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer("Отменено")


@user_router.message(OrderStates.waiting_for_receipt, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]
    file_id = photo.file_id
    await _finalize_order(message, state, bot, file_id, is_document=False)


@user_router.message(OrderStates.waiting_for_receipt, F.document)
async def process_receipt_document(message: Message, state: FSMContext, bot: Bot):
    doc = message.document
    file_id = doc.file_id
    await _finalize_order(message, state, bot, file_id, is_document=True)


@user_router.message(OrderStates.waiting_for_receipt)
async def process_receipt_invalid(message: Message):
    await message.answer(
        "⚠️ <b>Пожалуйста, отправьте именно фото или документ (скриншот чека) об оплате.</b>\n"
        "Или нажмите кнопку «❌ Отменить заказ» ниже.",
        reply_markup=cancel_order_keyboard(),
        parse_mode="HTML"
    )


async def _finalize_order(message: Message, state: FSMContext, bot: Bot, file_id: str, is_document: bool):
    data = await state.get_data()
    stars = data.get("stars", 0)
    price = data.get("price", 0)
    formatted_price = f"{price:,}".replace(",", " ")
    user = message.from_user

    order_id = await Database.create_order(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        stars=stars,
        price=price,
        receipt_file_id=file_id
    )

    await state.clear()

    # Сообщение покупателю
    user_confirm_text = (
        f"✅ <b>Ваш чек получен! Заказ #{order_id} оформлен.</b>\n\n"
        f"⭐ <b>Количество Stars:</b> {stars} ⭐\n"
        f"💰 <b>Сумма:</b> {formatted_price} сум\n"
        f"⏳ <b>Статус:</b> На проверке у администратора\n\n"
        "Мы уведомим вас здесь, как только платёж будет проверен и Stars зачислены на ваш аккаунт!"
    )
    await message.answer(user_confirm_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

    # Уведомление продавцу/администратору
    username_display = f"@{user.username}" if user.username else "Отсутствует"
    admin_caption = (
        f"🔔 <b>НОВЫЙ ЗАКАЗ #{order_id}!</b>\n\n"
        f"👤 <b>Покупатель:</b> {user.full_name}\n"
        f"🔗 <b>Username:</b> {username_display}\n"
        f"🆔 <b>ID пользователя:</b> <code>{user.id}</code>\n\n"
        f"⭐️ <b>Количество Stars:</b> {stars}\n"
        f"💰 <b>Сумма:</b> {formatted_price} сум\n"
        f"📅 <b>Статус:</b> ⏳ Ожидает подтверждения\n\n"
        "Проверьте чек и нажмите нужную кнопку:"
    )

    admin_kb = get_order_admin_keyboard(order_id)

    # Рассылаем всем админам из config
    for admin_id in ADMIN_IDS:
        try:
            if is_document:
                await bot.send_document(
                    chat_id=admin_id,
                    document=file_id,
                    caption=admin_caption,
                    reply_markup=admin_kb,
                    parse_mode="HTML"
                )
            else:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=admin_caption,
                    reply_markup=admin_kb,
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")
