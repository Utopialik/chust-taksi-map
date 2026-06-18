import asyncio
import osmnx as ox
import networkx as nx
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8849837890:AAHXXzi0BoGwbOpylsQ0PjpZdF0pzMuBe3c"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

print("Chust yo'llar tarmog'i yuklanmoqda...")
joy_nomi = "Chust, Uzbekistan"
graf = ox.graph_from_place(joy_nomi, network_type="all")
graf = ox.add_edge_speeds(graf)
graf = ox.add_edge_travel_times(graf)
print("🗺️ Tizim bekor qilish tizimi bilan to'liq tayyor!")

# Tariflar
MINIMAL_NARX = 5000       
MINIMAL_MASOFA_KM = 2     
HAR_KM_NARXI = 2000       

# GitHub Pages havolalari
URL_BOSHLANGICH = "https://utopialik.github.io/chust-taksi-map/boshlangich.html"
URL_YAKUNIY = "https://utopialik.github.io/chust-taksi-map/"

class TaksiBuyurtma(StatesGroup):
    boshlangich_joy = State()
    yakuniy_joy = State()

# 🔄 BOTNI RESTART QILISH (AVTO-START)
async def botni_boshlangich_holatga_qaytarish(message: types.Message, state: FSMContext):
    await state.clear()
    bosh_xarita_tugma = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text="📍 Turgan joyimni xaritadan tasdiqlash", 
                web_app=WebAppInfo(url=URL_BOSHLANGICH)
            )
        ]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        f"Yangi buyurtma berish uchun pastdagi tugmani bosing va turgan joyingizni tasdiqlang:",
        reply_markup=bosh_xarita_tugma
    )
    await state.set_state(TaksiBuyurtma.boshlangich_joy)

@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    bosh_xarita_tugma = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text="📍 Turgan joyimni xaritadan tasdiqlash", 
                web_app=WebAppInfo(url=URL_BOSHLANGICH)
            )
        ]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}! 🚖\n"
        f"Chust aqlli taksi xizmatiga xush kelibsiz.\n\n"
        f"Iltimos, pastdagi tugmani bosing, ochilgan xaritada turgan joyingiz to'g'ri ekanligini tekshirib, tasdiqlang:",
        reply_markup=bosh_xarita_tugma
    )
    await state.set_state(TaksiBuyurtma.boshlangich_joy)

# 1-QADAM: Birinchi WebApp'dan koordinatani qabul qilish
@dp.message(TaksiBuyurtma.boshlangich_joy, F.web_app_data)
async def boshlangich_lokatsiya(message: types.Message, state: FSMContext):
    data = json.loads(message.web_app_data.data)
    bosh_lat, bosh_lon = data.get("latitude"), data.get("longitude")
    await state.update_data(bosh_koor=(bosh_lat, bosh_lon))
    
    yakuniy_xarita_tugma = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🗺️ Borar joyni xaritadan belgilash", web_app=WebAppInfo(url=URL_YAKUNIY))]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("📍 Turgan joyingiz qabul qilindi!\n\nEndi boradigan manzilingizni belgilang:", reply_markup=yakuniy_xarita_tugma)
    await state.set_state(TaksiBuyurtma.yakuniy_joy)

# 2-QADAM: Ikkinchi WebApp'dan koordinatani olib hisoblash
@dp.message(TaksiBuyurtma.yakuniy_joy, F.web_app_data)
async def yakuniy_webapp_lokatsiya(message: types.Message, state: FSMContext):
    data = json.loads(message.web_app_data.data)
    yakuniy_lat, yakuniy_lon = data.get("latitude"), data.get("longitude")
    
    foydalanuvchi_mawlumoti = await state.get_data()
    bosh_lat, bosh_lon = foydalanuvchi_mawlumoti['bosh_koor']
    
    kutish_xabari = await message.answer("🔄 Yo'nalish chizilmoqda va narx hisoblanmoqda...", reply_markup=ReplyKeyboardRemove())

    try:
        boshlangich_nuqta = ox.nearest_nodes(graf, X=bosh_lon, Y=bosh_lat)
        yakuniy_nuqta = ox.nearest_nodes(graf, X=yakuniy_lon, Y=yakuniy_lat)

        masofa_km = nx.shortest_path_length(graf, boshlangich_nuqta, yakuniy_nuqta, weight="length") / 1000
        vaqt_minut = nx.shortest_path_length(graf, boshlangich_nuqta, yakuniy_nuqta, weight="travel_time") / 60

        if masofa_km <= MINIMAL_MASOFA_KM:
            jami_yo_l_haqi = MINIMAL_NARX
        else:
            jami_yo_l_haqi = MINIMAL_NARX + ((masofa_km - MINIMAL_MASOFA_KM) * HAR_KM_NARXI)

        await kutish_xabari.delete()
        
        # 🎛️ BUYURTMA CHIQGANDA IKKITA OPTSIYA: Safarni tugatish yoki Bekor qilish
        harakat_tugmalari = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Manzilga yetdik (Safar tugadi)", callback_data="safar_yakunlandi")],
                [InlineKeyboardButton(text="❌ Safarni bekor qilish", callback_data="safar_bekor_qilish")]
            ]
        )

        await message.answer(
            f"🚖 **BUYURTMA CHEKI HISOBLANDI:**\n\n"
            f"📏 **Masofa:** {masofa_km:.2f} km\n"
            f"⏱️ **Taxminiy vaqt:** {int(vaqt_minut)} minut\n"
            f"💰 **Yo'l haqi:** {int(jami_yo_l_haqi):,} so'm\n\n"
            f"Haydovchi qidirilmoqda... 🔄".replace(',', ' '),
            reply_markup=harakat_tugmalari
        )
    except Exception:
        await message.answer("❌ Marshrutni hisoblashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        await botni_boshlangich_holatga_qaytarish(message, state)

# 3-QADAM (A variant): Safar muvaffaqiyatli tugaganda baholash
@dp.callback_query(F.data == "safar_yakunlandi")
async def safar_tugadi_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    
    yulduzlar = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="⭐ 1", callback_data="baho_1"),
            InlineKeyboardButton(text="⭐ 2", callback_data="baho_2"),
            InlineKeyboardButton(text="⭐ 3", callback_data="baho_3"),
            InlineKeyboardButton(text="⭐ 4", callback_data="baho_4"),
            InlineKeyboardButton(text="⭐ 5", callback_data="baho_5")
        ]]
    )
    await callback.message.answer("🏁 Siz manzilga yetib keldingiz!\n\nSafar sizga manzur bo'ldimi? Haydovchini baholang:", reply_markup=yulduzlar)

@dp.callback_query(F.data.startswith("baho_"))
async def baholash_ijrosi(callback: types.CallbackQuery, state: FSMContext):
    baho_qiymati = callback.data.split("_")[1]
    await callback.answer(f"Siz {baho_qiymati} baho berdingiz!")
    await callback.message.delete()
    
    # 📝 Bu yerda kelajakda haydovchining reytingini ma'lumotlar bazasiga (DB) yozib qo'yamiz.
    print(f"Tahlil: Foydalanuvchi haydovchiga {baho_qiymati} yulduz berdi.")
    
    await callback.message.answer("❤️ Xizmatimizdan foydalanganingiz uchun rahmat!")
    await botni_boshlangich_holatga_qaytarish(callback.message, state)


# 4-QADAM (B variant): Safar BEKOR QILINGANDA so'rovnoma chiqarish
@dp.callback_query(F.data == "safar_bekor_qilish")
async def bekor_qilish_oynasi(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    
    # 📑 Sabablar so'rovnomasi
    sabablar_menyusi = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗓️ Rejalarim o'zgardi", callback_data="sabab_rejalar_ozgardi")],
            [InlineKeyboardButton(text="⏳ Haydovchi uzoq kutdirdi", callback_data="sabab_uzoq_kutdirdi")],
            [InlineKeyboardButton(text="🚖 Boshqa mashina topdim", callback_data="sabab_boshqa_taksi")],
            [InlineKeyboardButton(text="✍️ Xato buyurtma beribman", callback_data="sabab_xato_tanlov")]
        ]
    )
    
    await callback.message.answer(
        "🤔 **Safarni bekor qilish sababini ko'rsating:**\n\n"
        "Sizning fikringiz haydovchilarimiz ish sifatini yaxshilashga va tizimni nazorat qilishga yordam beradi.",
        reply_markup=sabablar_menyusi
    )

@dp.callback_query(F.data.startswith("sabab_"))
async def bekor_sababi_ijrosi(callback: types.CallbackQuery, state: FSMContext):
    tanlangan_sabab = callback.data.split("sabab_")[1]
    await callback.answer("Buyurtma bekor qilindi.")
    await callback.message.delete()
    
    # 📈 TAHLIL UCHUN: Qaysi sabab ko'p bosilayotganini terminalga/baza ga yozamiz.
    # Masalan, agar "uzoq_kutdirdi" ko'p chiqsa, demak o'sha haydovchi vaqtida bormayapti!
    print(f"🚨 Tahlil Tizimi: Safar bekor qilindi. Sabab: {tanlangan_sabab}")
    
    await callback.message.answer("❌ Safaringiz bekor qilindi. Arizangiz tizim muhandislari tomonidan ko'rib chiqiladi.")
    
    # Avtomat yangi buyurtma olish rejimiga qaytaramiz
    await botni_boshlangich_holatga_qaytarish(callback.message, state)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())