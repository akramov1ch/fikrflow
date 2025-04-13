import telegram
from telegram.ext import Application, MessageHandler, filters
import asyncio
import re
import os
from typing import List
import logging
from datetime import datetime, time
import json
import pytz

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Atrof-muhit o‘zgaruvchilaridan ma‘lumotlarni olish
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
ALLOWED_USER_ID = int(os.getenv('ALLOWED_USER_ID', 0))
SCHEDULE_TIMES = json.loads(os.getenv('SCHEDULE_TIMES', '["07:00", "12:00", "19:00", "21:00"]'))

# O‘zbekiston vaqt zonasi
UZBEKISTAN_TZ = pytz.timezone('Asia/Tashkent')

# Xabarlar ro‘yxati va holatni saqlash uchun sinf
class MessageQueue:
    def __init__(self):
        self.messages: List[str] = []
        self.is_sending = False

    def add_messages(self, messages: List[str]):
        self.messages.extend(messages)

    def get_message(self) -> str:
        return self.messages.pop(0) if self.messages else None

    def count(self) -> int:
        return len(self.messages)

message_queue = MessageQueue()

async def handle_message(update, context):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Kechirasiz, bu bot faqat ma‘lum bir foydalanuvchi uchun ishlaydi.")
        return

    raw_message = update.message.text
    new_messages = re.findall(r'"([^"]*)"', raw_message)

    if new_messages:
        message_queue.add_messages(new_messages)
        next_time = get_next_scheduled_time()
        await update.message.reply_text(
            f"{len(new_messages)} ta xabar qo‘shildi. Jami: {message_queue.count()} ta xabar.\n"
            f"Keyingi xabar O‘zbekiston vaqti bilan {next_time} da yuboriladi."
        )
        if not message_queue.is_sending:
            message_queue.is_sending = True
            asyncio.create_task(send_messages_by_schedule(context, update.effective_user.id))
    else:
        await update.message.reply_text(
            "Xabarlar topilmadi. Iltimos, qo‘shtirnoq ichida matn yuboring, masalan: \"xabar 1\" \"xabar 2\""
        )

def get_next_scheduled_time() -> str:
    """O‘zbekiston vaqti bilan keyingi jadval vaqtini qaytaradi."""
    now = datetime.now(UZBEKISTAN_TZ)
    today = now.date()
    schedule_times = sorted(SCHEDULE_TIMES)
    for t in schedule_times:
        hour, minute = map(int, t.split(":"))
        scheduled_time = datetime.combine(today, time(hour, minute), tzinfo=UZBEKISTAN_TZ)
        if scheduled_time > now:
            return t
    # Agar bugungi vaqtlar tugagan bo‘lsa, ertangi birinchi vaqt
    return schedule_times[0]

async def send_messages_by_schedule(context, user_id):
    while message_queue.count() > 0:
        try:
            now = datetime.now(UZBEKISTAN_TZ)
            current_time = now.strftime("%H:%M")
            if current_time in SCHEDULE_TIMES:
                message = message_queue.get_message()
                if message:
                    formatted_message = f"-{message}..."
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=formatted_message)
                    logger.info(f"Xabar yuborildi (O‘zbekiston vaqti: {current_time}): {formatted_message}")
                    next_time = get_next_scheduled_time()
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Xabar yuborildi: {formatted_message}\n"
                             f"Keyingi xabar O‘zbekiston vaqti bilan {next_time} da."
                    )
                await asyncio.sleep(60)  # Keyingi daqiqaga o‘tish uchun
            await asyncio.sleep(30)  # Har 30 soniyada tekshiramiz
        except telegram.error.TelegramError as e:
            logger.error(f"Xabar yuborishda xato: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Xabar yuborishda xato yuz berdi: {e}. Keyinroq qayta urinib ko‘ramiz."
            )
            await asyncio.sleep(60)

    message_queue.is_sending = False
    await context.bot.send_message(chat_id=user_id, text="Xabarlar tugadi, yangisini yuboring.")
    logger.info("Xabarlar ro‘yxati bo‘shadi.")

def main():
    if not all([TOKEN, CHANNEL_ID, ALLOWED_USER_ID]):
        logger.error("TELEGRAM_TOKEN, CHANNEL_ID yoki ALLOWED_USER_ID o‘rnatilmagan!")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot ishga tushdi...")
    application.run_polling()

if __name__ == '__main__':
    main()