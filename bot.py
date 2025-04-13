import telegram
from telegram.ext import Application, MessageHandler, filters
import asyncio
import re
from datetime import datetime, timedelta
import pytz

TOKEN = '7844550136:AAHlX-BKpAo_dT2n7asdytwoNn4jDNfpbmM'
CHANNEL_ID = '-1002571997790'
ALLOWED_USER_ID = 5773326948  

message_list = []
is_sending = False

# O'zbekiston vaqt mintaqasi
UZ_TIMEZONE = pytz.timezone('Asia/Tashkent')

# Xabar yuborish vaqtlari (soat:minut)
SEND_TIMES = [
    (7, 0),   # 07:00
    (12, 0),  # 12:00
    (18, 0),  # 18:00
    (21, 0),  # 21:00
]

async def handle_message(update, context):
    global message_list, is_sending
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Kechirasiz, bu bot faqat ma’lum bir foydalanuvchi uchun ishlaydi.")
        return
    
    raw_message = update.message.text
    new_messages = re.findall(r'"([^"]*)"', raw_message)
    
    if new_messages:
        message_list.extend(new_messages)
        await update.message.reply_text(f"{len(new_messages)} ta xabar qo‘shildi. Jami: {len(message_list)} ta xabar.")
        if not is_sending:
            is_sending = True
            asyncio.create_task(send_messages_periodically(context, update.effective_user.id))
    else:
        await update.message.reply_text("Xabarlar topilmadi. Qo‘shtirnoq ichida matn yuboring.")

def get_next_send_time():
    """Keyingi yuborish vaqtini aniqlash."""
    now = datetime.now(UZ_TIMEZONE)
    today = now.date()
    next_time = None
    min_diff = timedelta(days=1)

    for hour, minute in SEND_TIMES:
        candidate = UZ_TIMEZONE.localize(datetime(today.year, today.month, today.day, hour, minute))
        if now > candidate:
            # Agar vaqt o'tib ketgan bo'lsa, ertangi kunni hisoblaymiz
            candidate = candidate + timedelta(days=1)
        diff = candidate - now
        if diff < min_diff:
            min_diff = diff
            next_time = candidate

    return next_time

async def send_messages_periodically(context, user_id):
    global message_list, is_sending
    while message_list:
        next_send_time = get_next_send_time()
        now = datetime.now(UZ_TIMEZONE)
        seconds_until_next = (next_send_time - now).total_seconds()

        if seconds_until_next > 0:
            await asyncio.sleep(seconds_until_next)

        # Xabar yuborish
        if message_list:  # Ro'yxat bo'sh emasligini tekshiramiz
            message = message_list.pop(0)
            formatted_message = f"-{message}..."
            await context.bot.send_message(chat_id=CHANNEL_ID, text=formatted_message)
    
    is_sending = False
    await context.bot.send_message(chat_id=user_id, text="Xabarlar tugadi, yangisini yubor.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()