from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from pymongo import MongoClient
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# Check if values are loaded correctly (optional, for debugging)
if not TOKEN or not MONGO_URI:
    raise ValueError("Missing BOT_TOKEN or MONGO_URI. Check your .env file.")

print("Bot is starting...")  # Just a confirmation message

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
collection = db["images"]

# Handle image uploads
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    file_id = message.photo[-1].file_id
    today = datetime.date.today().isoformat()

    collection.insert_one({"file_id": file_id, "upload_date": today})
    
    await message.reply("Image saved!")

# Handle date queries
@dp.message_handler()
async def send_image(message: types.Message):
    try:
        query_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
        result = collection.find_one({"upload_date": query_date.isoformat()})

        if result:
            await bot.send_photo(chat_id=message.chat.id, photo=result["file_id"])
        else:
            await message.reply("No image found for this date.")

    except ValueError:
        await message.reply("Please enter a valid date in YYYY-MM-DD format.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
