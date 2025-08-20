import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ------------------------
# 🔑 Load environment variables
# ------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ BOT_TOKEN or GEMINI_API_KEY is missing in environment variables!")

# ------------------------
# 🌐 Flask App (for Render health check)
# ------------------------
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Gemini Telegram Bot is running on Render!"

# ------------------------
# 🤖 Telegram Bot
# ------------------------
def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hello! 🚀 Gemini Telegram Bot is alive and running!")

    async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📰 Latest news feature coming soon!")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news))

    # Run bot polling
    application.run_polling(drop_pending_updates=True)

# ------------------------
# 🚀 Main Entry
# ------------------------
if __name__ == "__main__":
    print("🚀 Starting Flask + Telegram bot service...")

    # ✅ Run Telegram bot in background thread
    threading.Thread(target=run_bot, daemon=True).start()

    # ✅ Run Flask server for Render (must bind to $PORT)
    port = int(os.environ.get("PORT", 5001))
    flask_app.run(host="0.0.0.0", port=port)