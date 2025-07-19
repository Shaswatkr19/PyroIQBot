from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
import google.generativeai as genai
import os
import time
import asyncio
import requests

# Load env variables
BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
NEWSDATA_API_KEY = os.environ["NEWSDATA_API_KEY"]  # <--- Add this to your .env
genai.configure(api_key=GEMINI_API_KEY)

print("🚀 Starting bot...")
print("✅ GEMINI_API_KEY loaded:", repr(GEMINI_API_KEY))
print("✅ BOT_TOKEN loaded:", repr(BOT_TOKEN))

# Gemini 1.5 Pro model
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Cooldown system
user_last_active = {}

def is_user_allowed(user_id):
    now = time.time()
    if user_id not in user_last_active or now - user_last_active[user_id] > 5:
        user_last_active[user_id] = now
        return True
    return False

# Gemini text generation
async def get_gemini_reply(prompt):
    retries = 5
    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait_time = 2 ** i
                print(f"Rate limit hit. Retrying in {wait_time} sec...")
                await asyncio.sleep(wait_time)
            else:
                return f"Error from Gemini: {e}"
    return "🚫 Too many requests. Try again later."

# News fetcher
def get_latest_tech_news():
    url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&country=in&language=en&category=technology"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("results", [])[:3]
            if not articles:
                return "No news found right now. Try again later 📰"
            news_text = "🗞️ *Latest Tech Headlines from India:*\n\n"
            for idx, article in enumerate(articles, 1):
                title = article.get("title", "No Title")
                link = article.get("link", "")
                news_text += f"{idx}. [{title}]({link})\n"
            return news_text
        else:
            return f"⚠️ Failed to fetch news. Status Code: {response.status_code}"
    except Exception as e:
        return f"❌ Error while fetching news: {e}"

# /start
async def start(update, context):
    intro_text = (
        "👋 Yo! Main Gemini AI se live connected hoon 🤖 Google AI ka magic lekar! Kuch bhi puchh, har sawaal ka jawab milega 💡✨\n\n"
        "🔹Try sending anything like:\n"
        "`What is Python?`\n"
        "`Text me for a latest news`\n"
        "`Tell me a joke`\n"
        "`How to learn coding?`\n\n"
        "Type /stop when you're done. Let's go! 🚀"
    )
    await update.message.reply_text(intro_text)

# /stop
async def stop(update, context):
    goodbye_text = (
        "🙏 Thank you for chatting with me!\n"
        "Hope I helped you today 🌟\n"
        "You can come back anytime by typing /start 💬\n\n"
        "Have a great day ahead! 🌈"
    )
    await update.message.reply_text(goodbye_text)

# Message Handler
async def handle_message(update, context):
    user_msg = update.message.text
    user_id = update.effective_user.id

    if user_msg.lower() in ["hi", "hello", "hey", "start", "yo"]:
        await start(update, context)
        return

    if not is_user_allowed(user_id):
        await update.message.reply_text("😅 Thoda ruk ja bhai! 5 sec mein ek baar hi message bhejna allowed hai.")
        return

    # Check for news-related trigger
    if any(word in user_msg.lower() for word in ["news", "headlines", "latest news"]):
        news = get_latest_tech_news()
        await update.message.reply_text(news, parse_mode="Markdown", disable_web_page_preview=False)
        return

    try:
        bot_reply = await get_gemini_reply(user_msg)
        await update.message.reply_text(bot_reply)
    except Exception as e:
        await update.message.reply_text(f"Oops! System thoda tilt ho gaya 😵‍💫⚙️\nError: {e}")

# Error handler
async def error_handler(update, context):
    import logging
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    logging.error(msg="Exception while handling update:", exc_info=context.error)

# Main App
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print("🤖 Gemini Telegram Bot with News Feature Running...")
    app.run_polling()