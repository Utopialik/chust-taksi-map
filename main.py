import asyncio
import logging
import sys
import osmnx as ox
import networkx as nx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 1. Loglarni sozlash (Serverda bot ishini kuzatish uchun)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 2. Yangi Telegram Bot Tokeni
BOT_TOKEN = "8849837890:AAERNz-ldIskYt8x2QnFq5wcr9JgI0KzAME"

# 3. Bot va Dispatcherlarni ishga tushirish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Global o'zgaruvchi (Chust shahri yo'llar tarmog'i grafigi)
G = None

def load_chust_map():
    """Chust shahri yo'llar tarmog'ini yuklash va xotiraga joylash"""
    global G
    logging.info("🗺️ Chust yo'llar tarmog'i yuklanmoqda...")
    try:
        # Chust shahri chegarasi bo'yicha drive (avtomobil) yo'llarini yuklaymiz
        G = ox.graph_from_place("Chust, Namangan Region, Uzbekistan", network_type="drive")
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        logging.info("🗺️ Tizim geolokatsiya va xaritalar bilan to'liq tayyor!")
    except Exception as e:
        logging.error(f"❌ Xaritani yuklashda xatolik yuz berdi: {e}")

# 4. Asosiy menyu tugmalari
def get_main_keyboard():
    button_location = KeyboardButton(text="📍 Geolokatsiyani yuborish", request_location=True)
    button_rates = KeyboardButton(text="🚖 Tariflar va Narxlar")
    button_help = KeyboardButton(text="ℹ️ Yordam va Qo'llab-quvvatlash")
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [button_location],
            [button_rates, button_help]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# 5. /start buyrug'i uchun handler
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Assalomu alaykum, {message.from_user.first_name}! Chust yo'nalishli taksi botiga xush kelibsiz.\n\n"
        "🚕 Bizning bot orqali o'zingiz turgan joyga eng yaqin taksi yo'nalishini aniqlashingiz mumkin.\n\n"
        "Xizmatdan foydalanish uchun pastdagi **📍 Geolokatsiyani yuborish** tugmasini bosing 👇",
        reply_markup=get_main_keyboard()
    )

# 6. Tariflar bo'limi uchun handler
@dp.message(lambda message: message.text == "🚖 Tariflar va Narxlar")
async def show_rates(message: types.Message):
    await message.answer(
        "🚖 **Chust Taksi tariflari va joriy narxlari:**\n\n"
        "🔹 **Shahar ichida:** 10,000 so'm (sobit narx)\n"
        "🔸 **Yo'nalishli taksi (Damas/Cobalt):** Har bir yo'lovchi uchun 3,000 so'mdan\n"
        "🔹 **Viloyat markaziga (Namangan shahri):** 15,000 so'm (odam boshiga)\n\n"
        "✨ Masofaga qarab narxlar aniq hisoblanishi uchun geolokatsiyangizni yuboring."
    )

# 7. Yordam bo'limi uchun handler
@dp.message(lambda message: message.text == "ℹ️ Yordam va Qo'llab-quvvatlash")
async def show_help(message: types.Message):
    await message.answer(
        "ℹ️ **Yordam markazi**\n\n"
        "Muammo yoki takliflar yuzasidan administratorimizga murojaat qilishingiz mumkin.\n"
        "📞 **Aloqa:** +998 (9x) xxx-xx-xx\n"
        "🤖 **Bot versiyasi:** 1.0.0 (Stabil)\n\n"
        "Chust yo'llar xaritasi doimiy ravishda yangilanib boriladi."
    )

# 8. Lokatsiya xabarlarini qayta ishlash va eng yaqin xarita nuqtasini topish
@dp.message(lambda message: message.location is not None)
async def handle_location(message: types.Message):
    user_lat = message.location.latitude
    user_lon = message.location.longitude
    
    await message.answer("🔄 Geolokatsiyangiz qabul qilindi. Chust yo'llar tarmog'idan sizga eng yaqin nuqta hisoblanmoqda...")
    
    if G is None:
        await message.answer("⚠️ Kechirasiz, xarita tizimi serverda qayta yuklanmoqda. Birozdan so'ng qayta urinib ko'ring.")
        return

    try:
        # Geodezik koordinatalar yordamida Chust xaritasidan eng yaqin tugunni (node) topamiz
        nearest_node = ox.nearest_nodes(G, X=user_lon, Y=user_lat)
        
        await message.answer(
            f"✅ **Muvaffaqiyatli aniqlandi!**\n\n"
            f"📍 Sizning joriy koordinatalaringiz:\n"
            f"🌐 Kenglik (Lat): `{user_lat}`\n"
            f"🌐 Uzunlik (Lon): `{user_lon}`\n\n"
            f"🚖 Chust yo'llar tarmog'idagi eng yaqin tugun identifikatori: `{nearest_node}`\n\n"
            f"Haydovchilar bilan aloqa o'rnatilmoqda, iltimos kutib turing!"
        )
    except Exception as e:
        logging.error(f"Yo'nalish topishda xatolik: {e}")
        await message.answer("❌ Kechirasiz, koordinatalarni xaritaga bog'lashda texnik xatolik yuz berdi.")

# 9. Botni toza ishga tushirish (Webhook va eski xabarlarni tozalash bilan)
async main():
    # 1. Avval xaritani xotiraga yuklab olamiz
    load_chust_map()
    
    # 2. Telegram serverida qolib ketgan eski so'rovlarni (updates) butunlay o'chiramiz
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 3. Pollingni boshlaymiz
    logging.info("🚀 Bot polling rejimida toza start oldi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Bot serverda to'xtatildi!")