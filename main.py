from dotenv import load_dotenv
import os
import requests
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, filters, ContextTypes
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from dataclasses import dataclass
import json

nest_asyncio.apply()

load_dotenv()

API_KEY = "b8d353c258fc4e5dc1b449085a838c4a"
UNSPLASH_API_KEY = "B7Lwnk7QFIbp_JpMCf9tVeEOrBElmQUtEG2CzStYC0c"

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("⛔ توکن بات تلگرام در `.env` تنظیم نشده است!")

ORIGIN, DESTINATION = range(2)

city_translation = {
    "تهران": "Tehran",
    "مشهد": "Mashhad",
    "اصفهان": "Isfahan",
    "شیراز": "Shiraz",
    "کرج": "Karaj",
    "تبریز": "Tabriz",
    "اهواز": "Ahvaz",
    "کرمان": "Kerman",
    "یزد": "Yazd",
    "کرمانشاه": "Kermanshah"
}


@dataclass
class Coordinates:
    latitude: float
    longitude: float

    def coordinates(self):
        return self.latitude, self.longitude

def get_coordinates(address):
    geolocator = Nominatim(user_agent='distance_calculator')
    location = geolocator.geocode(address)

    if location:
        return Coordinates(latitude=location.latitude, longitude=location.longitude)

def calculate_distance_km(home: Coordinates, target: Coordinates):
    if home and target:
        distance = geodesic(home.coordinates(), target.coordinates()).kilometers
        return distance

def calculate_travel_time(distance_km, speed_kmh):
    if distance_km and speed_kmh > 0:
        time_hours = distance_km / speed_kmh
        if time_hours < 1:
            minutes = time_hours * 60
            return f"{minutes:.0f} دقیقه"
        rounded_hours = round(time_hours)
        return f"{rounded_hours} ساعت"
    return None

def get_weather(city_name):
    translated_city = city_translation.get(city_name, city_name)
    url = f"{BASE_URL}?q={translated_city}&appid={API_KEY}&lang=fa&units=metric"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]

        return (
            f"🌤️ وضعیت آب و هوا در {city_name}:\n\n"
            f"☁️ توضیحات: {description}\n"
            f"🌡️ دما: {temperature}°C\n"
            f"💧 رطوبت: {humidity}%"
        )
    else:
        return "متاسفانه نتواستم وضعیت آب و هوا رو پیدا کنم."

def get_city_image(city_name):
    url = f"https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {UNSPLASH_API_KEY}"}
    params = {"query": city_name, "per_page": 1}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            return data["results"][0]["urls"]["regular"]
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "به بات راهنمای سفر خوش اومدی!\n"
        "برای اینکه ببینی سفرت چقدر دور و درازه روی /calculate بزن.\n"
    )

async def calculate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً شهر مبدا را وارد کن:")
    return ORIGIN

async def get_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['origin'] = update.message.text
    await update.message.reply_text("ممنون! حالا شهر مقصد را وارد کن:")
    return DESTINATION

async def get_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        origin = context.user_data['origin']
        destination = update.message.text

        home_coordinates = get_coordinates(origin)
        target_coordinates = get_coordinates(destination)

        if home_coordinates and target_coordinates:
            distance = calculate_distance_km(home_coordinates, target_coordinates)

            car_time = calculate_travel_time(distance, 80)
            train_time = calculate_travel_time(distance, 120)
            plane_time = calculate_travel_time(distance, 800)

            keyboard = [
                [InlineKeyboardButton("اطلاعات شهر مقصد", callback_data=f"info_{destination}")],
                [InlineKeyboardButton("وضعیت آب و هوا", callback_data=f"weather_{destination}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"مسافت بین:\n\n"
                f"🏠 مبدا: {origin}\n📍 مقصد: {destination}\n\n"
                f"🌍 {distance:.2f} کیلومتر\n\n"
                f"⏳ زمان تقریبی سفر:\n"
                f"🚗 ماشین: {car_time}\n"
                f"🚆 قطار: {train_time}\n"
                f"✈️ هواپیما: {plane_time}",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("آدرس‌ها قابل پیدا کردن نیستند. دوباره تلاش کنید.")
    except Exception as e:
        await update.message.reply_text(f"یک خطا رخ داد: {e}")

    return ConversationHandler.END

async def city_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        city_name = update.callback_query.data.split("_")[1]
        with open("cities.json", "r", encoding="utf-8") as file:
            cities = json.load(file)

        city_data = cities.get(city_name)
        if city_data:
            image_url = get_city_image(city_name)
            if image_url:
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_url)

            message = (
                f"📍 اطلاعات شهر {city_name}:\n\n"
                f"👥 جمعیت: {city_data['population']}\n"
                f"📜 تاریخچه: {city_data['history']}\n"
                f"🍴 غذاها: {', '.join(city_data['food'])}\n"
                f"🏞️ مکان‌های دیدنی: {', '.join(city_data['places'])}\n"
            )
            await update.callback_query.message.reply_text(message)
        else:
            await update.callback_query.message.reply_text("اطلاعاتی درباره این شهر یافت نشد.")
    except Exception as e:
        await update.callback_query.message.reply_text(f"یک خطا رخ داد: {e}")

async def weather_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        city_name = update.callback_query.data.split("_")[1]
        weather_data = get_weather(city_name)
        await update.callback_query.message.reply_text(weather_data)
    except Exception as e:
        await update.callback_query.message.reply_text(f"یک خطا رخ داد: {e}")

def run_bot():
    application = ApplicationBuilder().token("7289614860:AAE0s159mR66SlZaQNK33QEdOJTG1wxUmS0").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("calculate", calculate_start)],
        states={
            ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_origin)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_destination)],
        },
        fallbacks=[CommandHandler("cancel", lambda update, context: update.message.reply_text("فرآیند لغو شد."))],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(city_info, pattern="^info_"))
    application.add_handler(CallbackQueryHandler(weather_info, pattern="^weather_"))
    application.add_handler(conv_handler)

    print("Bot is running... Press Ctrl+C to stop.")
    application.run_polling()

run_bot()