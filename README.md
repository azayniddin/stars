# ⭐️ Telegram Stars Bot / Бот для продажи Telegram Stars

Telegram-бот для автоматизации продажи Telegram Stars за сумы (UZS) с удобной админ-панелью, приёмом чеков и уведомлениями.

---

## 🇺🇿 O‘zbekcha Yo‘riqnoma

### 🚀 Qanday ishga tushiriladi?

1. **Virtual muhitni faollashtirish va kutubxonalarni o‘rnatish (agar o‘rnatilmagan bo‘lsa):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Sozlamalar (`.env` fayli):**
   Faylni oching va kerakli ma'lumotlarni kiriting:
   ```env
   BOT_TOKEN=8610019500:AAHMI3arF9nxEerOrsSDGJwdoKyzVX3Uhm4
   ADMIN_IDS=123456789
   ```
   > 💡 **O‘z Telegram ID raqamingizni qayerdan bilish mumkin?**  
   > Botni ishga tushirib, botga `/myid` deb yozsangiz, bot sizning ID raqamingizni chiqarib beradi. O'sha raqamni `ADMIN_IDS=` ga yozasiz.

3. **Botni ishga tushirish:**
   ```bash
   .venv/bin/python main.py
   ```

---

## 🇷🇺 Инструкция для клиента (на русском языке)

### 🌟 Возможности бота

* **Главное меню:**
  * `⭐ Купить Stars` — выбор нужного пакета и моментальное оформление заказа;
  * `💰 Цены` — просмотр актуального прайс-листа;
  * `📋 Как купить` — подробная пошаговая инструкция для покупателей;
  * `🆘 Поддержка` — связь со службой поддержки;
  * `📜 Правила` — правила сервиса и условия гарантии;
  * `👤 Связаться с продавцом` — прямой контакт с продавцом.

* **Процесс покупки:**
  1. Покупатель выбирает количество Stars (50, 100, 250, 500, 1000).
  2. Бот выдаёт реквизиты карты и точную сумму.
  3. Покупатель переводит средства и отправляет скриншот чека.
  4. Администратор моментально получает фото чека с кнопками `✅ Подтвердить` и `❌ Отклонить`.
  5. При подтверждении покупатель получает уведомление об успешной отправке Stars.

* **Админ-панель (`/admin`):**
  * 📊 **Статистика**: число пользователей, общее число заказов, выручка и количество проданных звёзд;
  * 💰 **Управление ценами**: изменение цен на любые пакеты прямо в Telegram;
  * 💳 **Реквизиты оплаты**: удобная смена номера карты;
  * 📝 **Тексты**: изменение инструкций, правил и контактов;
  * 📢 **Рассылка**: отправка сообщений всем пользователям бота в один клик.

---

### ⚙️ Запуск и настройка бота

1. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. В файле `.env` укажите ваш Telegram ID:
   ```env
   BOT_TOKEN=8610019500:AAHMI3arF9nxEerOrsSDGJwdoKyzVX3Uhm4
   ADMIN_IDS=ВАШ_ТЕЛЕГРАМ_ID
   ```
   *(Чтобы узнать свой ID, отправьте команду `/myid` боту)*.

3. Запустите бота:
   ```bash
   python main.py
   ```
