import asyncio
import datetime
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, Update
from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, request, Response
import threading

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
WEBHOOK_HOST = os.getenv("RAILWAY_URL")  # Automatically set by Railway
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"


# Validate required variables
if not all([TOKEN, MONGO_URI, WEBHOOK_HOST]):
    raise ValueError("Missing required environment variables. Check TOKEN, MONGO_URI, and RAILWAY_URL.")

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
collection = db["images"]

# Flask server (for webhooks and Railway health checks)
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Bot is running!", 200

# --- Webhook Handler ---
@app.post(WEBHOOK_PATH)
async def webhook_handler():
    update = Update(**await request.get_json())
    await dp.feed_update(bot=bot, update=update)
    return Response(status=200)

# --- Image Upload Handler ---
@dp.message(lambda msg: msg.photo)
async def handle_photo(message: Message):
    """Saves uploaded image with current date."""
    file_id = message.photo[-1].file_id
    today = datetime.date.today().isoformat()
    caption = message.caption or "No caption"

    collection.insert_one({
        "file_id": file_id,
        "upload_date": today,
        "caption": caption
    })
    await message.reply("✅ Image saved for today!")

# --- Retrieve Image by Date ---
@dp.message(lambda msg: msg.text and len(msg.text) == 10)
async def send_image(message: Message):
    """Sends image based on user-provided date (YYYY-MM-DD)."""
    try:
        query_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
        result = collection.find_one({"upload_date": query_date.isoformat()})

        if result:
            await message.answer_photo(
                photo=result["file_id"],
                caption=f"🗓 Date: {query_date}\n📝 Caption: {result['caption']}"
            )
        else:
            await message.reply("❌ No image found for this date.")
    
    except ValueError:
        await message.reply("⚠️ Invalid date format. Use YYYY-MM-DD.")

# --- Startup ---
async def on_startup():
    """Set webhook and print debug info."""
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to {WEBHOOK_URL}")
    print(f" Railway URL: {WEBHOOK_HOST}")

def run_flask():
    port = int(os.getenv("PORT", 8080))
    from uvicorn import run as uvicorn_run
    uvicorn_run(app, host="0.0.0.0", port=port)

async def main():
    # Start Flask in a separate thread (for Railway health checks)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Set up webhook and start bot
    await on_startup()
    print("🚀 Bot is running with webhooks...")

if __name__ == "__main__":
    asyncio.run(main())