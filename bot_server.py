import os
import threading
import logging
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "✅ Gemini Telegram Bot is running!",
        "version": "1.0.0"
    })

@flask_app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "bot_active": True,
        "timestamp": os.environ.get("RENDER_GIT_COMMIT", "unknown")
    })

def run_flask():
    port = int(os.environ.get("PORT", 5000))  # Render usually uses 5000
    logger.info(f"🌐 Starting Flask server on port {port}")
    flask_app.run(host="0.0.0.0", port=port, debug=False)

# ------------------------
# Telegram bot handlers
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_msg = f"""🚀 Hello {user_name}! 

🤖 **Gemini Telegram Bot** is alive and ready!

Commands:
/start - Show this message
/news - Get latest news
/help - Get help

Just send me any message and I'll respond with Gemini AI!"""
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🆘 **Help & Commands**

• /start - Welcome message
• /news - Latest news (coming soon)
• /help - Show this help

💬 **How to use:**
Just type any message and I'll respond using Gemini AI!

🔧 **Need support?**
Contact the developer for assistance.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 **News Feature**\n\n"
        "🚧 Latest news feature is coming soon!\n"
        "Stay tuned for updates.", 
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_name = update.effective_user.first_name
    
    # Placeholder for Gemini AI integration
    response = f"🤖 Hi {user_name}!\n\nYou said: *{user_message}*\n\n🚧 Gemini AI integration coming soon!"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Sorry, something went wrong. Please try again later."
        )

# ------------------------
# Main entry
# ------------------------
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 STARTING GEMINI TELEGRAM BOT SERVICE")
    print("=" * 50)
    print(f"✅ BOT_TOKEN loaded: {BOT_TOKEN[:10]}***")
    print(f"✅ GEMINI_API_KEY loaded: {GEMINI_API_KEY[:10]}***")
    print(f"🌍 PORT: {os.environ.get('PORT', 5000)}")
    
    try:
        # 1️⃣ Start Flask in a background thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print("✅ Flask server started in background")
        
        # 2️⃣ Setup Telegram bot
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("news", news))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        print("✅ Bot handlers configured")
        print("🤖 Starting Telegram bot polling...")
        print("=" * 50)
        
        # 3️⃣ Start bot (blocks main thread)
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise