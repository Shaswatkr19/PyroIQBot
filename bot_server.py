import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import google.generativeai as genai
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
# Load Environment Variables
# ------------------------
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ BOT_TOKEN or GEMINI_API_KEY is missing!")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

print("✅ Environment variables loaded successfully")
print("✅ Gemini AI configured")

# ------------------------
# Flask App
# ------------------------
app = Flask(__name__)

# Global bot application
bot_app = None

@app.route("/")
def home():
    return jsonify({
        "status": "success", 
        "message": "🤖 Gemini Telegram Bot is running!",
        "version": "2.0.0"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "bot_active": True,
        "services": {
            "gemini_ai": "connected",
            "telegram_bot": "running"
        }
    })

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, bot_app.bot)
        
        # Use asyncio.run() to properly handle async update
        asyncio.run(bot_app.process_update(update))
        
        return "OK"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

# ------------------------
# Gemini AI Helper
# ------------------------
async def get_gemini_response(prompt):
    """Get response from Gemini AI with error handling"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini AI error: {e}")
        if "429" in str(e) or "quota" in str(e).lower():
            return "🚫 API quota exceeded. Please try again later."
        return f"❌ AI Error: {str(e)[:100]}..."

# ------------------------
# Bot Command Handlers
# ------------------------
async def start(update: Update, context):
    """Handle /start command"""
    user_name = update.effective_user.first_name
    welcome_msg = f"""🚀 **Hello {user_name}!**

🤖 **Gemini Telegram Bot** is ready to help!

**Features:**
✅ AI-powered chat using Google Gemini
✅ Smart responses to your questions
✅ Help with coding, learning & more!

**Commands:**
• /start - Show this message
• /help - Get detailed help
• /about - Bot information

💬 **Just send me any message and I'll respond with AI magic!** ✨"""
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context):
    """Handle /help command"""
    help_text = """🆘 **Help & Commands**

🤖 **How to use:**
Just type any message and I'll respond using Google's Gemini AI!

**Available Commands:**
• `/start` - Welcome message
• `/help` - Show this help
• `/about` - Bot information

**Examples:**
• "What is Python programming?"
• "Write a funny joke"
• "Explain quantum physics"
• "Help me with JavaScript"

**Features:**
✅ Smart AI responses
✅ Code help & explanations
✅ Learning assistance
✅ Creative writing
✅ Problem solving

💡 **Tip:** Be specific with your questions for better responses!"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context):
    """Handle /about command"""
    about_text = """ℹ️ **About Gemini Bot**

🤖 **Version:** 2.0.0
🧠 **AI Model:** Google Gemini 1.5 Flash
⚡ **Framework:** Python Telegram Bot + Flask
🌐 **Hosting:** Cloud-ready webhook deployment

**Developer:** Your Name
**Last Updated:** December 2024

🔗 **Powered by:**
• Google Gemini AI
• Python Telegram Bot
• Flask Web Framework

❤️ **Made with love for learning and automation!**"""
    
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def handle_message(update: Update, context):
    """Handle regular text messages"""
    try:
        user_msg = update.message.text
        user_name = update.effective_user.first_name
        
        # Handle simple greetings
        greetings = ["hi", "hello", "hey", "hola", "namaste"]
        if user_msg.lower().strip() in greetings:
            await update.message.reply_text(
                f"👋 Hello {user_name}! How can I help you today?",
                parse_mode='Markdown'
            )
            return
        
        # Send typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, 
            action="typing"
        )
        
        # Get AI response
        enhanced_prompt = f"User {user_name} asks: {user_msg}\n\nProvide a helpful, concise response in a friendly tone."
        ai_response = await get_gemini_response(enhanced_prompt)
        
        # Split long messages if needed
        if len(ai_response) > 4000:
            for i in range(0, len(ai_response), 4000):
                await update.message.reply_text(ai_response[i:i+4000])
        else:
            await update.message.reply_text(ai_response)
            
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        await update.message.reply_text(
            "🚧 Something went wrong! Please try again in a moment.\n"
            f"Error: {str(e)[:50]}..."
        )

async def error_handler(update: Update, context):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again later."
        )

# ------------------------
# Bot Setup Function
# ------------------------
def setup_bot():
    """Setup the Telegram bot application"""
    global bot_app
    
    # Create Application
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(CommandHandler("about", about_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    bot_app.add_error_handler(error_handler)
    
    logger.info("✅ Bot handlers configured successfully")
    return bot_app

# ------------------------
# Webhook Setup Route
# ------------------------
@app.route("/set_webhook")
def set_webhook():
    """Set up webhook URL (call this once after deployment)"""
    webhook_url = request.url_root + f"webhook/{BOT_TOKEN}"
    try:
        # Synchronous webhook setup
        import requests as req
        telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        response = req.post(telegram_api_url, data={"url": webhook_url})
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "message": "Webhook set successfully",
                "webhook_url": webhook_url,
                "telegram_response": response.json()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to set webhook",
                "telegram_response": response.json()
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to set webhook: {e}"
        }), 500

# ------------------------
# Initialize Bot
# ------------------------
setup_bot()

# ------------------------
# Run Flask App
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🌐 Starting Flask server on port {port}")
    logger.info("🤖 Telegram bot ready for webhook mode")
    app.run(host="0.0.0.0", port=port, debug=False)