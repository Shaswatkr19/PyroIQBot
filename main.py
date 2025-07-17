from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from openai import OpenAI
from telegram import Update
import os
import time
import asyncio

BOT_TOKEN = os.environ["BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

print("🚀 Starting bot...")
print("✅ OPENAI_API_KEY loaded:", repr(os.getenv("OPENAI_API_KEY")))
print("✅ BOT_TOKEN loaded:", repr(os.getenv("BOT_TOKEN")))

# Create OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
print("✅ Loaded key:", repr("OPENAI_API_KEY"))

# Cooldown system to prevent spam
user_last_active = {}

def is_user_allowed(user_id):
    now = time.time()
    if user_id not in user_last_active or now - user_last_active[user_id] > 5:  # 5 seconds cooldown
        user_last_active[user_id] = now
        return True
    return False

# Retry-enabled function to get ChatGPT reply
async def get_chatgpt_reply(prompt):
    retries = 5
    for i in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", 
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e):
                wait_time = 2 ** i  # exponential backoff: 1, 2, 4, 8...
                print(f"Rate limit hit. Retrying in {wait_time} sec...")
                await asyncio.sleep(wait_time)
            else:
                return f"Error from OpenAI: {e}"
    return "🚫 Too many requests. Try again later."

# /start command
async def start(update, context):
    intro_text = (
        "👋 Yo! Main ChatGPT se live connected hoon 💬 tech ka jaadu mere paas hai! Kuch bhi puchh, har sawaal ka jawab milega 😎🔥🤖\n\n"
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

# Handle text messages
async def handle_message(update, context):
    user_msg = update.message.text
    user_id = update.effective_user.id

    # 👋 Auto greet if first message is casual
    if user_msg.lower() in ["hi", "hello", "hey", "start", "yo"]:
        intro_text = (
            "👋 Yo! Main ChatGPT se live connected hoon 💬 tech ka jaadu mere paas hai! Kuch bhi puchh, har sawaal ka jawab milega 😎🔥🤖\n\n"
            "🔹 Try sending anything like:\n"
            "What is Python?\n"
            "Tell me a joke\n"
            "How to learn coding?\n\n"
            "Type /stop when you're done. Let's go! 🚀"
        )
        await update.message.reply_text(intro_text)
        return

    # ⏱️ Cooldown check
    if not is_user_allowed(user_id):
        await update.message.reply_text("😅 Thoda ruk ja bhai! 5 sec mein ek baar hi message bhejna allowed hai.")
        return

    # 🔁 Get reply from OpenAI
    try:
        bot_reply = await get_chatgpt_reply(user_msg)
        await update.message.reply_text(bot_reply)
    except Exception as e:
        await update.message.reply_text(f"Oops! System thoda tilt ho gaya 😵‍💫⚙️\nError: {e}")    

# 🛠️ Error handler for Telegram-related issues
async def error_handler(update, context):
    import logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    logging.error(msg="Exception while handling update:", exc_info=context.error)

# 🔁 MAIN: Run the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print("Bot connected with OpenAI and running....")
    app.run_polling()