import logging
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
import sqlite3

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize SQLite database
conn = sqlite3.connect('images.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS images
             (date TEXT, file_id TEXT, caption TEXT)''')
conn.commit()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save image with current date"""
    user = update.message.from_user
    file_id = update.message.photo[-1].file_id
    caption = update.message.caption or "No caption"
    today = datetime.today().strftime('%Y-%m-%d')

    # Store in database
    c.execute("INSERT INTO images VALUES (?, ?, ?)", (today, file_id, caption))
    conn.commit()

    await update.message.reply_text(f"✅ Image saved for {today}!")

async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return images for given date"""
    text = update.message.text
    try:
        # Validate date format
        input_date = datetime.strptime(text, '%Y-%m-%d').strftime('%Y-%m-%d')
        c.execute("SELECT file_id, caption FROM images WHERE date=?", (input_date,))
        results = c.fetchall()

        if not results:
            await update.message.reply_text("❌ No images found for this date")
            return

        for file_id, caption in results:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=file_id,
                caption=f"📅 {input_date}\n📝 {caption}"
            )

    except ValueError:
        await update.message.reply_text("⚠️ Please use YYYY-MM-DD format")

if __name__ == '__main__':
    # Get token from Railway environment variables
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        raise ValueError("Missing BOT_TOKEN environment variable")

    # Create bot application
    application = ApplicationBuilder().token(TOKEN).build()

    # Add handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date))

    # Start polling
    application.run_polling()