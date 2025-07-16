from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from openai import OpenAI
from telegram import Update
import os


BOT_TOKEN = os.environ["BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

print("🚀 Starting bot...")
print("✅ OPENAI_API_KEY loaded:", repr(os.getenv("OPENAI_API_KEY")))
print("✅ BOT_TOKEN loaded:", repr(os.getenv("BOT_TOKEN")))
#create openai client
client = OpenAI(api_key=OPENAI_API_KEY)
print("✅ Loaded key:", repr("OPENAI_API_KEY"))

#/Start command
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

#Handle normal text messages
async def handle_message(update, context):
    user_msg = update.message.text

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

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[{"role": "user", "content": user_msg}],
        )

        bot_reply = response.choices[0].message.content
        await update.message.reply_text(bot_reply)

    except Exception as e:
        await update.message.reply_text(f"Oops! System thoda tilt ho gaya 😵‍💫⚙️\nError ka scene hai: {e}")    

if __name__ == "__main__":
#Setup bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("Stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error Handler (for Telegram errors like Conflict etc.)
    async def error_handler(update, context):
        import logging
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
        )
        logging.error(msg="Exception while handling update:", exc_info=context.error)

    app.add_error_handler(error_handler)

    print("Bot connected with OpenAI and running....")
    app.run_polling()