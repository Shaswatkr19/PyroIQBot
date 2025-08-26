import os
import time
import asyncio
import requests
import threading
import logging
from flask import Flask, jsonify
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
import google.generativeai as genai

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
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
NEWSDATA_API_KEY = os.environ.get("NEWSDATA_API_KEY")

# Check if all required env vars are present
if not all([BOT_TOKEN, GEMINI_API_KEY, NEWSDATA_API_KEY]):
    missing_vars = []
    if not BOT_TOKEN: missing_vars.append("BOT_TOKEN")
    if not GEMINI_API_KEY: missing_vars.append("GEMINI_API_KEY")
    if not NEWSDATA_API_KEY: missing_vars.append("NEWSDATA_API_KEY")
    raise ValueError(f"❌ Missing environment variables: {', '.join(missing_vars)}")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

print("🚀 Starting Gemini Telegram Bot...")
print("✅ GEMINI_API_KEY loaded:", repr(GEMINI_API_KEY[:2] + "***"))
print("✅ BOT_TOKEN loaded:", repr(BOT_TOKEN[:2] + "***"))
print("✅ NEWSDATA_API_KEY loaded:", repr(NEWSDATA_API_KEY[:2] + "***"))

# ------------------------
# Flask App for Web Service
# ------------------------
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "🤖 Gemini Telegram Bot is running!",
        "features": ["Gemini AI Chat", "Latest Tech News", "Rate Limiting"],
        "version": "2.0.0"
    })

@flask_app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "bot_active": True,
        "services": {
            "gemini_ai": "connected",
            "news_api": "connected",
            "telegram_bot": "running"
        }
    })

@flask_app.route("/stats")
def bot_stats():
    return jsonify({
        "total_users": len(user_last_active),
        "active_sessions": len([u for u, t in user_last_active.items() if time.time() - t < 300])
    })

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🌐 Starting Flask server on port {port}")
    flask_app.run(host="0.0.0.0", port=port, debug=False)

# ------------------------
# Gemini AI Setup
# ------------------------
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# ------------------------
# Cooldown System
# ------------------------
user_last_active = {}

def is_user_allowed(user_id):
    now = time.time()
    if user_id not in user_last_active or now - user_last_active[user_id] > 5:
        user_last_active[user_id] = now
        return True
    return False

# ------------------------
# Gemini Text Generation
# ------------------------
async def get_gemini_reply(prompt):
    retries = 5
    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait_time = 2 ** i
                print(f"⏳ Rate limit hit. Retrying in {wait_time} sec...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Gemini error: {e}")
                return f"❌ Error from Gemini: {e}"
    return "🚫 Too many requests. Try again later."

# ------------------------
# News Fetcher
# ------------------------
def get_latest_tech_news():
    url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&country=in&language=en&category=technology"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("results", [])[:3]
            if not articles:
                return "📰 No tech news found right now. Try again later!"
            
            news_text = "🗞️ *Latest Tech Headlines from India:*\n\n"
            for idx, article in enumerate(articles, 1):
                title = article.get("title", "No Title")
                link = article.get("link", "")
                source = article.get("source_id", "Unknown")
                news_text += f"{idx}. *{title}*\n"
                news_text += f"   📄 Source: {source}\n"
                news_text += f"   🔗 [Read More]({link})\n\n"
            
            news_text += "🔄 _Auto-updated every few hours_"
            return news_text
        else:
            return f"⚠️ Failed to fetch news. Status Code: {response.status_code}"
    except requests.exceptions.Timeout:
        return "⏰ News request timed out. Try again later."
    except Exception as e:
        logger.error(f"News fetch error: {e}")
        return f"❌ Error while fetching news: {e}"

# ------------------------
# Bot Handlers
# ------------------------
async def start(update, context):
    user_name = update.effective_user.first_name
    intro_text = (
        f"👋 Hey {user_name}! Main Gemini AI se live connected hoon! 🤖\n\n"
        "🚀 *What I can do:*\n"
        "• Answer any question using Google's Gemini AI\n"
        "• Get latest tech news from India\n"
        "• Help with coding, learning, jokes & more!\n\n"
        "🔹 *Try these commands:*\n"
        "`What is Python programming?`\n"
        "`Tell me latest tech news`\n"
        "`Write a funny joke`\n"
        "`How to learn machine learning?`\n\n"
        "⚡ *Commands:*\n"
        "/start - Show this message\n"
        "/stop - Say goodbye\n"
        "/help - Get help\n\n"
        "🎯 Just type anything and I'll respond with AI magic! ✨"
    )
    await update.message.reply_text(intro_text, parse_mode='Markdown')

async def help_command(update, context):
    help_text = (
        "🆘 *Help & Commands*\n\n"
        "🤖 *How to use:*\n"
        "Just type any message and I'll respond using Gemini AI!\n\n"
        "📰 *For news:* Type any of these words:\n"
        "• `news`\n"
        "• `headlines`\n"
        "• `latest news`\n\n"
        "⚡ *Rate Limit:* 1 message per 5 seconds\n\n"
        "🔧 *Features:*\n"
        "✅ Gemini AI responses\n"
        "✅ Latest tech news\n"
        "✅ Smart rate limiting\n"
        "✅ Error handling\n\n"
        "Need more help? Just ask me anything!"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stop(update, context):
    user_name = update.effective_user.first_name
    goodbye_text = (
        f"🙏 Thank you {user_name} for chatting with me!\n"
        "Hope I helped you today! 🌟\n\n"
        "You can come back anytime by typing /start 💬\n\n"
        "Have a great day ahead! 🌈✨"
    )
    await update.message.reply_text(goodbye_text)

async def handle_message(update, context):
    user_msg = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Handle greetings
    if user_msg.lower() in ["hi", "hello", "hey", "start", "yo"]:
        await start(update, context)
        return

    # Rate limiting
    if not is_user_allowed(user_id):
        await update.message.reply_text(
            "😅 Thoda ruk ja bhai! 5 seconds mein ek baar hi message bhej sakta hai.\n"
            "⏰ Wait karo aur phir try karo!"
        )
        return

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Check for news-related requests
    news_keywords = ["news", "headlines", "latest news", "tech news", "technology news"]
    if any(word in user_msg.lower() for word in news_keywords):
        news = get_latest_tech_news()
        await update.message.reply_text(
            news, 
            parse_mode="Markdown", 
            disable_web_page_preview=False
        )
        return

    # Handle regular AI chat
    try:
        # Add user context to prompt
        enhanced_prompt = f"User {user_name} asks: {user_msg}\n\nPlease provide a helpful, concise response."
        bot_reply = await get_gemini_reply(enhanced_prompt)
        
        # Split long messages
        if len(bot_reply) > 4000:
            for i in range(0, len(bot_reply), 4000):
                await update.message.reply_text(bot_reply[i:i+4000])
        else:
            await update.message.reply_text(bot_reply)
            
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        await update.message.reply_text(
            f"Oops! System thoda tilt ho gaya 😵‍💫⚙️\n"
            f"Error: {str(e)[:100]}...\n\n"
            "Try again in a few seconds!"
        )

# ------------------------
# Error Handler
# ------------------------
async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Something went wrong! Try again later.\n"
            "If the issue persists, contact support."
        )

# ------------------------
# Main Application
# ------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 STARTING GEMINI TELEGRAM BOT WITH FLASK SERVER")
    print("=" * 60)
    
    try:
        # 1️⃣ Start Flask server in background
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print("✅ Flask server started in background")
        
        # 2️⃣ Setup Telegram bot
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("stop", stop))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Add error handler
        app.add_error_handler(error_handler)
        
        print("✅ Bot handlers configured")
        print("🤖 Starting Telegram bot polling...")
        print("=" * 60)
        
        # 3️⃣ Run bot (blocks main thread)
        app.run_polling(drop_pending_updates=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise