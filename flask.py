import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ✅ Telegram & Gemini setup
BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running on Render!"

# ✅ Start Telegram bot in separate thread
def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hello! Gemini bot is alive 🚀")

    application.add_handler(CommandHandler("start", start))

    application.run_polling()

if __name__ == "__main__":
    # run telegram bot in background
    threading.Thread(target=run_bot).start()

    # run dummy web server for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)