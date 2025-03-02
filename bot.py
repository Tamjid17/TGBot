import logging
import os
from datetime import datetime
import sqlite3
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
conn = sqlite3.connect('images.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS images
            (date TEXT, file_id TEXT, caption TEXT)''')
conn.commit()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save image with current date"""
    try:
        file_id = update.message.photo[-1].file_id
        caption = update.message.caption or "No caption"
        today = datetime.now().strftime('%Y-%m-%d')

        # Simple synchronous DB operation
        c.execute("INSERT INTO images VALUES (?, ?, ?)", (today, file_id, caption))
        conn.commit()

        await update.message.reply_text(f"✅ Image saved for {today}!")
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        await update.message.reply_text("❌ Failed to save image")

async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return images for given date"""
    try:
        text = update.message.text.strip()
        input_date = datetime.strptime(text, '%Y-%m-%d').strftime('%Y-%m-%d')
        
        c.execute("SELECT file_id, caption FROM images WHERE date=?", (input_date,))
        results = c.fetchall()

        if not results:
            await update.message.reply_text("❌ No images found for this date")
            return

        for file_id, caption in results:
            await update.message.reply_photo(
                photo=file_id,
                caption=f"📅 {input_date}\n📝 {caption}"
            )
    except ValueError:
        await update.message.reply_text("⚠️ Please use YYYY-MM-DD format")
    except Exception as e:
        logger.error(f"Error retrieving images: {e}")
        await update.message.reply_text("❌ Failed to retrieve images")

def main() -> None:
    """Start the bot"""
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        raise ValueError("Missing BOT_TOKEN environment variable")

    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date))

    # Start polling
    application.run_polling()

if __name__ == '__main__':
    main()