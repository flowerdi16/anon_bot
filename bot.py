import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
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
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# =========================
# START
# =========================
@dp.message(Command("start"))
async def start(message: Message):
    await add_user(message.from_user)
    await message.answer("📩 Напиши сообщение — оно уйдёт анонимно.")


# =========================
# USER → GROUP (АНОНИМКА)
# =========================
@dp.message(F.chat.type == "private")
async def user_to_group(message: Message):

    user = message.from_user
    await add_user(user)

    # 🚫 бан чек
    if await is_banned(user.id):
        await message.answer("🚫 Вы заблокированы.")
        return

    # игнор команд
    if message.text and message.text.startswith("/"):
        return

    # ================= TEXT =================
    if message.text:
        sent = await bot.send_message(
            GROUP_ID,
            f"📩 АНОНИМНО:\n\n{message.text}"
        )

    # ================= PHOTO =================
    elif message.photo:
        sent = await bot.send_photo(
            GROUP_ID,
            message.photo[-1].file_id,
            caption="📷 Анонимное фото"
        )

    # ================= VIDEO =================
    elif message.video:
        sent = await bot.send_video(
            GROUP_ID,
            message.video.file_id,
            caption="🎥 Анонимное видео"
        )

    # ================= VOICE =================
    elif message.voice:
        sent = await bot.send_voice(
            GROUP_ID,
            message.voice.file_id
        )

    else:
        return

    await save_message(sent.message_id, user.id)

    await message.answer("✅ Отправлено")


# =========================
# GROUP → USER (REPLY SYSTEM)
# =========================
@dp.message(F.chat.id == GROUP_ID, F.reply_to_message)
async def group_handler(message: Message):

    user_id = await get_user(message.reply_to_message.message_id)

    if not user_id:
        return

    text = message.text or ""

    # ================= BAN =================
    if text == "/ban":
        await ban(user_id)
        await message.reply("🚫 Забанен")
        return

    # ================= UNBAN =================
    if text == "/unban":
        await unban(user_id)
        await message.reply("✅ Разбанен")
        return

    # ================= REPLY =================
    if message.text:
        await bot.send_message(
            user_id,
            f"💬 Ответ:\n\n{text}"
        )

    elif message.photo:
        await bot.send_photo(
            user_id,
            message.photo[-1].file_id,
            caption="💬 Ответ"
        )

    elif message.video:
        await bot.send_video(
            user_id,
            message.video.file_id,
            caption="💬 Ответ"
        )

    elif message.voice:
        await bot.send_voice(
            user_id,
            message.voice.file_id
        )


# =========================
# BANNED LIST
# =========================
@dp.message(Command("banned"))
async def banned_list(message: Message):

    if message.chat.id != GROUP_ID:
        return

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