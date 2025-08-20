import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# ------------------------
# Load .env
# ------------------------
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ BOT_TOKEN or GEMINI_API_KEY is missing!")

# ------------------------
# Flask App
# ------------------------
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Gemini Telegram Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5001))
    flask_app.run(host="0.0.0.0", port=port)

# ------------------------
# Telegram bot handlers
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Hello! Gemini Telegram Bot is alive!")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 Latest news coming soon!")

# ------------------------
# Main entry
# ------------------------
if __name__ == "__main__":
    print("🚀 Starting Flask + Telegram bot service...")
    print(f"✅ BOT_TOKEN loaded: {BOT_TOKEN[:5]}***")
    print(f"✅ GEMINI_API_KEY loaded: {GEMINI_API_KEY[:5]}***")

    # 1️⃣ Start Flask in a background thread
    threading.Thread(target=run_flask, daemon=True).start()

    # 2️⃣ Telegram bot runs in main thread (asyncio safe)
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news))
    application.run_polling(drop_pending_updates=True)