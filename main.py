
import asyncio
import logging
import sys
import osmnx as ox
import networkx as nx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# 1. Loglarni sozlash (Serverda nima bo'layotganini ko'rish uchun)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 2. To'g'rilangan Telegram Bot Tokeni (Barcha belgilari bilan)
BOT_TOKEN = "8849837890:AAERNz-ldIskYt8x2QnFq5wcr9JgI0KzAME"

# 3. Aiogram bot va dispatcherini ishga tushirish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 4. Global o'zgaruvchilar (Chust yo'llar grafigi)
G = None

def load_chust_map():
    """Chust shahri yo'llar tarmog'ini yuklash va optimallashtirish"""
    global G
    logging.info("🗺️ Chust yo'llar tarmog'i yuklanmoqda...")
    try:
        # Chust shahri chegarasi bo'yicha yo'llarni yuklab olamiz
        G = ox.graph_from_place("Chust, Namangan Region, Uzbekistan", network_type="drive")
        # Marshrut hisoblash tezlashishi uchun grafikni tezliklar bilan boyitamiz
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        logging.info("🗺️ Tizim bekor qilish tizimi bilan to'liq tayyor!")
    except Exception as e:
        logging.error(f"❌ Xaritani yuklashda xatolik: {e}")

# 5. Tugmalarni yaratish
def get_main_keyboard():
    button_location = KeyboardButton(text="📍 Geolokatsiyani yuborish", request_location=True)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_location]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# 6. /start buyrug'i uchun handler
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Assalomu alaykum! Chust yo'nalishli taksi botiga xush kelibsiz.\n\n"
        "Yaxshimisiz? Sizga eng yaqin haydovchi va eng maqbul yo'nalishni aniqlashimiz uchun "
        "pastdagi tugma orqali geolokatsiyangizni ulashing 👇",
        reply_markup=get_main_keyboard()
    )

# 7. Lokatsiya xabarlarini qayta ishlash uchun handler
@dp.message(lambda message: message.location is not None)
async def handle_location(message: types.Message):
    user_lat = message.location.latitude
    user_lon = message.location.longitude
    
    await message.answer("🔄 Geolokatsiyangiz qabul qilindi. Eng yaqin nuqta va yo'nalish hisoblanmoqda, iltimos kuting...")
    
    if G is None:
        await message.answer("⚠️ Tizimda xaritalar hali to'liq yuklanmagan. Birozdan so'ng qayta urinib ko'ring.")
        return

    try:
        # Foydalanuvchiga eng yaqin bo'lgan yo'l tarmog'i nuqtasini topamiz
        nearest_node = ox.nearest_nodes(G, X=user_lon, Y=user_lat)
        
        await message.answer(
            f"✅ Muvaffaqiyatli! Chust yo'llar tarmog'idan sizga eng yaqin tugun nuqtasi topildi.\n"
            f"Kenglik: {user_lat}\n"
            f"Uzunlik: {user_lon}\n\n"
            f"🚖 Tez orada sizga taksi yo'nalishi va haydovchi haqida ma'lumot yuboriladi!"
        )
    except Exception as e:
        logging.error(f"Yo'nalish hisoblashda xatolik: {e}")
        await message.answer("❌ Kechirasiz, yo'nalishni hisoblashda texnik xatolik yuz berdi.")

# 8. Botni ishga tushirish (Polling) ochish qismi
async def main():
    # Birinchi bo'lib xaritani xotiraga yuklaymiz
    load_chust_map()
    
    # Telegramdagi eski so'rovlarni (Webhook yoki qolib ketgan xabarlarni) tozalaymiz
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Pollingni boshlaymiz
    logging.info("🚀 Bot polling rejimida ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Bot to'xtatildi!")