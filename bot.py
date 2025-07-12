
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.payments import GetStarGifts
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

sent_gift_ids = set()
user_languages = {}
user_intervals = {}

language_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Русский 🇷🇺"),
    KeyboardButton("English 🇬🇧")
)

intervals_ru = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("10 секунд🕕"),
    KeyboardButton("5 минут🕕"),
    KeyboardButton("1 час🕕"),
    KeyboardButton("1 день🕕")
)

intervals_en = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("10 seconds🕕"),
    KeyboardButton("5 minutes🕕"),
    KeyboardButton("1 hour🕕"),
    KeyboardButton("1 day🕕")
)

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
        await message.answer("Язык установлен: русский 🇷🇺\n\nВыбери время проверки 🕕", reply_markup=intervals_ru)
    else:
        user_languages[user_id] = "en"
        await message.answer("Language set: English 🇬🇧\n\nChoose check interval 🕕", reply_markup=intervals_en)

@dp.message_handler(lambda m: m.text in interval_values)
async def interval_handler(message: types.Message):
    user_id = message.from_user.id
    interval = interval_values[message.text]
    user_intervals[user_id] = interval

    lang = user_languages.get(user_id, "en")
    if lang == "ru":
        await message.answer(f"✅ Проверка каждые {message.text.split()[0]} ✅")
    else:
        await message.answer(f"✅ Check every {message.text.split()[0]} ✅")

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
                        msg = (f"❗️НОВЫЙ ПОДАРОК ❗️\n{gift.title.text}\nЦена: {gift.star_count}⭐️\n"
                               f"Всего: {gift.total_count}\nОсталось: {gift.remaining_count}") if lang == "ru" else (
                               f"❗️NEW GIFT ❗️\n{gift.title.text}\nPrice: {gift.star_count}⭐️\n"
                               f"Total: {gift.total_count}\nLeft: {gift.remaining_count}")
                        if gift.unique:
                            msg += "\nУникальный ✅" if lang == "ru" else "\nUnique ✅"
                        await bot.send_message(user_id, msg)
        except Exception as e:
            logging.error(f"[ERROR] {e}")
        await asyncio.sleep(5)

async def main():
    asyncio.create_task(check_gifts())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
