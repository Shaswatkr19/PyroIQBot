import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# ------------------------
# Setup Logging
# ------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)  # single-threaded dispatcher

@app.route("/")
def home():
    return jsonify({"status": "success", "message": "✅ Gemini Telegram Bot is running!"})

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# ------------------------
# Bot Handlers
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_msg = f"""🚀 Hello {user_name}!

🤖 **Gemini Telegram Bot** is alive and ready!

Commands:
/start - Show this message
/news - Get latest news
/help - Show help

Just send me any message and I'll respond with Gemini AI!"""
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🆘 **Help & Commands**
• /start - Welcome message
• /news - Latest news
• /help - Show this help
💬 Type any message and I'll respond using Gemini AI!"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚧 News feature coming soon!", parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    user_name = update.effective_user.first_name
    response = f"🤖 Hi {user_name}! You said: *{user_msg}*\n🚧 Gemini AI coming soon!"
    await update.message.reply_text(response, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Something went wrong. Try again later.")

# Add handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("news", news))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
dispatcher.add_error_handler(error_handler)

# ------------------------
# Run Flask
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🌐 Flask running on port {port}")
    app.run(host="0.0.0.0", port=port)