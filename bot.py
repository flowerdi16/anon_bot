import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

from db import (
    init_db,
    add_user,
    is_banned,
    ban,
    unban,
    get_banned,
    save_message,
    get_user
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
OWNER_IDS = os.getenv("OWNER_IDS")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is empty")

if not GROUP_ID:
    raise ValueError("GROUP_ID is empty")

if not OWNER_IDS:
    raise ValueError("OWNER_IDS is empty")

GROUP_ID = int(GROUP_ID)
OWNER_IDS = [int(x.strip()) for x in OWNER_IDS.split(",")]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# START
# =========================
@dp.message(Command("start"))
async def start(message: Message):
    await add_user(message.from_user)
    await message.answer("Напишите анонимное сообщение.")


# =========================
# USER → GROUP (АНОНИМКА)
# =========================
@dp.message(F.chat.type == "private")
async def user_to_group(message: Message):

    try:
        user = message.from_user
        await add_user(user)

        if await is_banned(user.id):
            await message.answer("🚫 Вы заблокированы.")
            return

        # ❗ ВАЖНО: ВСЕ КОМАНДЫ УХОДЯТ ИЗ ЭТОГО HANDLER
        if message.text and message.text.startswith("/"):
            return

        if message.text:
            sent = await bot.send_message(GROUP_ID, message.text)

        elif message.photo:
            sent = await bot.send_photo(GROUP_ID, message.photo[-1].file_id)

        elif message.video:
            sent = await bot.send_video(GROUP_ID, message.video.file_id)

        else:
            return

        await save_message(sent.message_id, user.id)

        await message.answer("Отправлено.")

    except Exception as e:
        print(f"USER_TO_GROUP ERROR: {e}")


# =========================
# GROUP → USER (REPLY)
# =========================
@dp.message(F.chat.id == GROUP_ID, F.reply_to_message)
async def group_handler(message: Message):

    try:
        user_id = await get_user(message.reply_to_message.message_id)

        if not user_id:
            return

        text = message.text or ""

        if text == "/ban":
            await ban(user_id)
            await message.reply("Забанен.")
            return

        if text == "/unban":
            await unban(user_id)
            await message.reply("Разбанен.")
            return

        if message.text:
            await bot.send_message(user_id, message.text)

        elif message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id)

        elif message.video:
            await bot.send_video(user_id, message.video.file_id)

    except Exception as e:
        print(f"GROUP_HANDLER ERROR: {e}")


# =========================
# BANNED LIST (АДМИН ТОЛЬКО)
# =========================
@dp.message(Command("banned"))
async def banned_list(message: Message):

    if message.chat.type != "private":
        return

    if message.from_user.id not in OWNER_IDS:
        return

    print("BANNED TRIGGERED")

    rows = await get_banned()

    if not rows:
        await message.answer("🚫 Пусто")
        return

    text = "🚫 Забаненные:\n\n"

    for uid, username, name in rows:
        text += (
            f"👤 {name}\n"
            f"@{username or 'no_username'}\n"
            f"ID: {uid}\n\n"
        )

    await message.answer(text)


# =========================
# START BOT
# =========================
async def main():
    await init_db()
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
