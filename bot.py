import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.payments import GetStarGifts
import logging
import os

# ========== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ==========
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")
# ==========================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

sent_gift_ids = set()
user_languages = {}     # user_id: "ru" or "en"
user_intervals = {}     # user_id: interval in seconds

# ЯЗЫКОВОЕ МЕНЮ
language_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
language_keyboard.add(
    KeyboardButton("Русский 🇷🇺"),
    KeyboardButton("English 🇬🇧")
)

# МЕНЮ ИНТЕРВАЛА
intervals_ru = ReplyKeyboardMarkup(resize_keyboard=True)
intervals_ru.add(
    KeyboardButton("10 секунд🕕"),
    KeyboardButton("5 минут🕕"),
    KeyboardButton("1 час🕕"),
    KeyboardButton("1 день🕕")
)

intervals_en = ReplyKeyboardMarkup(resize_keyboard=True)
intervals_en.add(
    KeyboardButton("10 seconds🕕"),
    KeyboardButton("5 minutes🕕"),
    KeyboardButton("1 hour🕕"),
    KeyboardButton("1 day🕕")
)

# Значения интервалов
interval_values = {
    "10 секунд🕕": 10,
    "5 минут🕕": 300,
    "1 час🕕": 3600,
    "1 день🕕": 86400,
    "10 seconds🕕": 10,
    "5 minutes🕕": 300,
    "1 hour🕕": 3600,
    "1 day🕕": 86400
}


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer("Выбери язык / Choose language:", reply_markup=language_keyboard)


@dp.message_handler(lambda m: m.text in ["Русский 🇷🇺", "English 🇬🇧"])
async def language_handler(message: types.Message):
    user_id = message.from_user.id
    if message.text == "Русский 🇷🇺":
        user_languages[user_id] = "ru"
        await message.answer("Язык установлен: русский 🇷🇺\n\nВыбери время проверки появления новых подарков 🕕", reply_markup=intervals_ru)
    else:
        user_languages[user_id] = "en"
        await message.answer("Language set: English 🇬🇧\n\nChoose how often to check for new gifts 🕕", reply_markup=intervals_en)


@dp.message_handler(lambda m: m.text in interval_values)
async def interval_handler(message: types.Message):
    user_id = message.from_user.id
    interval = interval_values[message.text]
    user_intervals[user_id] = interval

    lang = user_languages.get(user_id, "en")
    if lang == "ru":
        await message.answer(f"✅ Время проверки установлено: каждые {message.text.split()[0]} ✅")
    else:
        await message.answer(f"✅ Check interval set to: every {message.text.split()[0]} ✅")


@dp.message_handler(commands=["settings"])
async def settings_menu(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "en")

    if lang == "ru":
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Сменить язык"), KeyboardButton("Сменить время проверки"))
        await message.answer("⚙️ Настройки:", reply_markup=keyboard)
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Change language"), KeyboardButton("Change check interval"))
        await message.answer("⚙️ Settings:", reply_markup=keyboard)


@dp.message_handler(lambda m: m.text in ["Сменить язык", "Change language"])
async def change_language_menu(message: types.Message):
    await message.answer("Выбери язык / Choose language:", reply_markup=language_keyboard)


@dp.message_handler(lambda m: m.text in ["Сменить время проверки", "Change check interval"])
async def change_interval_menu(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "en")

    if lang == "ru":
        await message.answer("Выбери новое время проверки подарков 🕕", reply_markup=intervals_ru)
    else:
        await message.answer("Choose new check interval 🕕", reply_markup=intervals_en)


async def check_gifts():
    await client.start()
    while True:
        try:
            gifts = await client(GetStarGifts())
            for gift in gifts.gifts:
                if gift.id not in sent_gift_ids:
                    sent_gift_ids.add(gift.id)

                    for user_id in user_intervals:
                        lang = user_languages.get(user_id, "en")

                        if lang == "ru":
                            msg = (
                                "❗️НОВЫЙ ПОДАРОК ❗️\n"
                                f"{gift.title.text}\n"
                                f"Цена: {gift.star_count}⭐️\n"
                                f"Всего выпущено: {gift.total_count}\n"
                                f"Осталось: {gift.remaining_count}"
                            )
                            if gift.unique:
                                msg += "\nМожно сделать подарок уникальным ✅"
                        else:
                            msg = (
                                "❗️NEW GIFT ❗️\n"
                                f"{gift.title.text}\n"
                                f"Price: {gift.star_count}⭐️\n"
                                f"Total issued: {gift.total_count}\n"
                                f"Remaining: {gift.remaining_count}"
                            )
                            if gift.unique:
                                msg += "\nThis gift can be made unique ✅"

                        await bot.send_message(user_id, msg)

        except Exception as e:
            logging.error(f"[ОШИБКА] {e}")

        await asyncio.sleep(5)


async def main():
    asyncio.create_task(check_gifts())
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
