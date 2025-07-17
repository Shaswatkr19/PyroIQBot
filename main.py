from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
import google.generativeai as genai
import os
import time
import asyncio

# Load env variables
BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

print("🚀 Starting bot...")
print("✅ GEMINI_API_KEY loaded:", repr(os.getenv("GEMINI_API_KEY")))
print("✅ BOT_TOKEN loaded:", repr(os.getenv("BOT_TOKEN")))

# Gemini 1.5 Pro model (no chat context for now)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Cooldown system to prevent spam
user_last_active = {}

def is_user_allowed(user_id):
    now = time.time()
    if user_id not in user_last_active or now - user_last_active[user_id] > 5:
        user_last_active[user_id] = now
        return True
    return False

# Get Gemini reply (with retry logic)
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

# /start command
async def start(update, context):
    intro_text = (
        "👋 Yo! Main Gemini AI se live connected hoon 🤖 Google AI ka magic lekar! Kuch bhi puchh, har sawaal ka jawab milega 💡✨\n\n"
        "🔹Try sending anything like:\n"
        "What is Python?\n"
        "Tell me a joke\n"
        "How to learn coding?\n\n"
        "Type /stop when you're done. Let's go! 🚀"
    )
    await update.message.reply_text(intro_text)

# /stop handler
async def stop(update, context):
    goodbye_text = (
        "🙏 Thank you for chatting with me!\n"
        "Hope I helped you today 🌟\n"
        "You can come back anytime by typing /start 💬\n\n"
        "Have a great day ahead! 🌈"
    )
    await update.message.reply_text(goodbye_text)

# Handle user messages
async def handle_message(update, context):
    user_msg = update.message.text
    user_id = update.effective_user.id

    if user_msg.lower() in ["hi", "hello", "hey", "start", "yo"]:
        await start(update, context)
        return

    if not is_user_allowed(user_id):
        await update.message.reply_text("😅 Thoda ruk ja bhai! 5 sec mein ek baar hi message bhejna allowed hai.")
        return

    try:
        bot_reply = await get_gemini_reply(user_msg)
        await update.message.reply_text(bot_reply)
    except Exception as e:
        await update.message.reply_text(f"Oops! System thoda tilt ho gaya 😵‍💫⚙️\nError: {e}")

# Handle errors
async def error_handler(update, context):
    import logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    logging.error(msg="Exception while handling update:", exc_info=context.error)

# Run the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print("Bot connected with Gemini 1.5 Pro and running....")
    app.run_polling()