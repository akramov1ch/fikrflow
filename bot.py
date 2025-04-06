import telegram
from telegram.ext import Application, MessageHandler, filters
import asyncio
import re

# Bot tokeni va kanal ID
TOKEN = '7844550136:AAHlX-BKpAo_dT2n7asdytwoNn4jDNfpbmM'
CHANNEL_ID = '-1002571997790'
ALLOWED_USER_ID = 5773326948  # Bu yerga o‘zingizning Telegram user ID’ingizni kiriting

# Xabarlar ro‘yxati va yuborish holati
message_list = []
is_sending = False

async def handle_message(update, context):
    global message_list, is_sending
    # Faqat ruxsat berilgan foydalanuvchidan xabar qabul qilish
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Kechirasiz, bu bot faqat ma’lum bir foydalanuvchi uchun ishlaydi.")
        return
    
    # Foydalanuvchidan kelgan xabarni olish
    raw_message = update.message.text
    # Yangi xabarlarni ajratib olish
    new_messages = re.findall(r'"([^"]*)"', raw_message)
    
    if new_messages:
        # Yangi xabarlarni ro‘yxatga qo‘shish
        message_list.extend(new_messages)
        # Foydalanuvchiga tasdiq xabari
        await update.message.reply_text(f"{len(new_messages)} ta xabar qo‘shildi. Jami: {len(message_list)} ta xabar.")
        # Agar yuborish jarayoni hali boshlanmagan bo‘lsa, ishga tushirish
        if not is_sending:
            is_sending = True
            asyncio.create_task(send_messages_periodically(context, update.effective_user.id))
    else:
        await update.message.reply_text("Xabarlar topilmadi. Qo‘shtirnoq ichida matn yuboring.")

async def send_messages_periodically(context, user_id):
    global message_list, is_sending
    while message_list:
        # Ro‘yxatdan birinchi xabarni olish va formatlash
        message = message_list.pop(0)
        formatted_message = f"-{message}..."
        # Kanalga yuborish
        await context.bot.send_message(chat_id=CHANNEL_ID, text=formatted_message)
        # 1 soat (3600 soniya) kutish
        await asyncio.sleep(3600)
    
    # Ro‘yxat bo‘shaganda
    is_sending = False
    await context.bot.send_message(chat_id=user_id, text="Xabarlar tugadi, yangisini yubor.")

def main():
    # Application obyektini yaratish
    application = Application.builder().token(TOKEN).build()
    # Xabarlar uchun handler qo‘shish
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Botni polling rejimida ishga tushirish
    application.run_polling()

if __name__ == '__main__':
    main()