import os
import time
import asyncio
import threading
import requests
import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import google.generativeai as genai
from dotenv import load_dotenv

# ------------------------
# Logging setup
# ------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------------
# Load environment variables
# ------------------------
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
NEWSDATA_API_KEY = os.environ.get("NEWSDATA_API_KEY")

if not all([BOT_TOKEN, GEMINI_API_KEY, NEWSDATA_API_KEY]):
    missing = [v for v, k in zip([BOT_TOKEN, GEMINI_API_KEY, NEWSDATA_API_KEY], ["BOT_TOKEN","GEMINI_API_KEY","NEWSDATA_API_KEY"]) if not v]
    raise ValueError(f"❌ Missing env vars: {', '.join(missing)}")

# ------------------------
# Configure Gemini
# ------------------------
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# ------------------------
# Flask app
# ------------------------
app = Flask(__name__)
telegram_app = None
user_last_active = {}

# ------------------------
# Rate limiting helper
# ------------------------
def is_user_allowed(user_id):
    now = time.time()
    if user_id not in user_last_active or now - user_last_active[user_id] > 5:
        user_last_active[user_id] = now
        return True
    return False

# ------------------------
# Gemini AI reply
# ------------------------
async def get_gemini_reply(prompt):
    retries = 3
    for i in range(retries):
        try:
            logger.info(f"Sending prompt to Gemini: {prompt[:100]}...")
            resp = model.generate_content(prompt)
            
            # Check if response is blocked
            if hasattr(resp, 'prompt_feedback') and resp.prompt_feedback:
                if resp.prompt_feedback.block_reason:
                    logger.warning(f"Prompt blocked: {resp.prompt_feedback.block_reason}")
                    return "🚫 Sorry, I can't respond to that message due to content policies."
            
            # Check if response has text
            if resp.text:
                logger.info("Successfully got response from Gemini")
                return resp.text
            else:
                logger.warning("Empty response from Gemini")
                return "🤔 I received your message but couldn't generate a response. Try rephrasing."
                
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Gemini AI error (attempt {i+1}): {e}")
            
            if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg:
                wait = 2 ** i
                logger.info(f"⏳ Rate limit hit. Retrying in {wait} sec...")
                await asyncio.sleep(wait)
                continue
            elif "blocked" in error_msg:
                return "🚫 Sorry, I can't respond to that message due to content policies."
            elif "400" in error_msg:
                return "❌ Invalid request format. Please try again."
            elif "403" in error_msg:
                return "❌ API access denied. Please check API key."
            else:
                # For other errors, don't retry
                return f"❌ Sorry, I'm having technical issues right now. Please try again later."
    
    return "🚫 Too many requests. Please try again in a minute."

# ------------------------
# Tech news fetcher
# ------------------------
def get_latest_tech_news():
    url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&country=in&language=en&category=technology"
    try:
        logger.info("Fetching tech news...")
        resp = requests.get(url, timeout=10)
        logger.info(f"News API response status: {resp.status_code}")
        
        if resp.status_code != 200:
            return f"⚠️ Failed to fetch news. Status: {resp.status_code}"
            
        data = resp.json()
        articles = data.get("results", [])[:3]
        
        if not articles: 
            return "📰 No tech news found!"
            
        news_text = "🗞️ *Latest Tech Headlines from India:*\n\n"
        for idx, art in enumerate(articles, 1):
            title = art.get("title","No Title")
            link = art.get("link","")
            source = art.get("source_id","Unknown")
            news_text += f"{idx}. *{title}*\n   📄 Source: {source}\n   🔗 [Read More]({link})\n\n"
        news_text += "🔄 _Auto-updated every few hours_"
        
        logger.info("Successfully fetched news")
        return news_text
        
    except Exception as e:
        logger.error(f"News fetch error: {e}")
        return f"❌ Error fetching news: {e}"

# ------------------------
# Bot Handlers
# ------------------------
async def start(update, context):
    user_name = update.effective_user.first_name
    text = (
        f"👋 Hey {user_name}! Gemini AI se live connected hoon! 🤖\n\n"
        "• Ask questions\n• Get latest tech news\n• Coding help, jokes & more!\n\n"
        "Commands:\n/start - Show this\n/help - Help\n/stop - Say bye"
    )
    await update.message.reply_text(text)

async def help_command(update, context):
    help_text = (
        "🆘 *Help*\n"
        "Just type anything and I will respond using Gemini AI.\n\n"
        "For news: type `news`, `headlines`, `tech news`\n"
        "Rate limit: 1 msg per 5 sec"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stop(update, context):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"🙏 Bye {user_name}! Come back anytime.")

async def handle_message(update, context):
    user_msg = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    logger.info(f"Received message from {user_name} ({user_id}): {user_msg[:100]}...")

    # Greetings
    if user_msg.lower() in ["hi","hello","hey","start","yo"]:
        await start(update, context)
        return

    # Rate limiting
    if not is_user_allowed(user_id):
        await update.message.reply_text("😅 Wait 5 seconds before sending another message.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # News
    news_keywords = ["news","headlines","latest news","tech news","technology news"]
    if any(word in user_msg.lower() for word in news_keywords):
        logger.info("Fetching news...")
        news = get_latest_tech_news()
        await update.message.reply_text(news, parse_mode='Markdown', disable_web_page_preview=False)
        return

    # AI reply
    try:
        # Simple test prompt first
        if user_msg.lower().strip() == "test":
            await update.message.reply_text("✅ Bot is working! Send me any message for AI response.")
            return
            
        prompt = f"You are a helpful AI assistant. User {user_name} asks: {user_msg}\n\nProvide a helpful, friendly response in a conversational tone."
        logger.info("Calling Gemini API...")
        reply = await get_gemini_reply(prompt)
        
        if reply and len(reply) > 0:
            # Split long messages
            for i in range(0, len(reply), 4000):
                await update.message.reply_text(reply[i:i+4000])
                logger.info("Successfully sent reply")
        else:
            await update.message.reply_text("🤔 I received your message but couldn't generate a response.")
            
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        await update.message.reply_text(f"❌ Technical error occurred. Please try 'test' command first.")

# Error handler
async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Something went wrong. Try later.")

# ------------------------
# Flask webhook routes
# ------------------------
@app.route("/")
def home_route():
    return jsonify({"status":"success","message":"Bot running!"})

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, telegram_app.bot)

        def process():
            try:
                # Get or create event loop for this thread
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        raise RuntimeError("Loop is closed")
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run the update processing
                loop.run_until_complete(telegram_app.process_update(update))
                
            except Exception as e:
                logger.error(f"Error processing update in thread: {e}")
        
        # Start thread to process update
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

@app.route("/set_webhook")
def set_webhook():
    url = request.url_root + f"webhook/{BOT_TOKEN}"
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", data={"url": url})
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------
# Initialize Telegram App
# ------------------------
async def init_telegram_app():
    global telegram_app
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("stop", stop))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    telegram_app.add_error_handler(error_handler)
    
    # Initialize the application
    await telegram_app.initialize()
    logger.info("Telegram application initialized successfully")

# ------------------------
# Main
# ------------------------
if __name__ == "__main__":
    # Initialize telegram app in event loop
    async def setup():
        await init_telegram_app()
    
    # Run initialization
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup())
    
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)