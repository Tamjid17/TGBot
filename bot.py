import asyncio
import datetime
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask
import threading
# Load environment variables
load_dotenv()

TOKEN = os.getenv("TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

if not TOKEN or not MONGO_URI:
    raise ValueError("Missing BOT_TOKEN or MONGO_URI. Check your .env file.")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
collection = db["images"]

# --- Image Upload Handler ---
@dp.message()
async def handle_photo(message: Message):
    """Saves uploaded image with the current date."""
    if message.photo:
        file_id = message.photo[-1].file_id
        today = datetime.date.today().isoformat()
        caption = message.caption if message.caption else "No caption"

        collection.insert_one({"file_id": file_id, "upload_date": today, "caption": caption})
        await message.reply("✅ Image saved for today!")

# --- Retrieve Image by Date ---
@dp.message()
async def send_image(message: Message):
    """Sends an image based on user-provided date."""
    try:
        query_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
        result = collection.find_one({"upload_date": query_date.isoformat()})

        if result:
            await bot.send_photo(chat_id=message.chat.id, photo=result["file_id"], caption=f"🗓 Date: {query_date}\n📝 Caption: {result['caption']}")
        else:
            await message.reply("❌ No image found for this date.")
    
    except ValueError:
        await message.reply("⚠️ Please enter a valid date in YYYY-MM-DD format.")

# Flask server to keep Railway active
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"
    print("Railway URL:", os.getenv("RAILWAY_URL", "Not found"))

def run_flask():
    app.run(host="0.0.0.0", port=8080)

async def main():
    """Start the bot."""
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(main())
