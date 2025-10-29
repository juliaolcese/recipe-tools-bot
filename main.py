import logging
import asyncio
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv
from geminiAPI import GeminiAPI

load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Bot started!")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that.")

async def get_ingredients_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['llm_api']
    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide a recipe link.")
        return
    recipe_link = context.args[0]
    
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action='typing'
    )
    
    try:
        ingredients = await asyncio.to_thread(api.get_ingredients, recipe_link)

        if not ingredients:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Couldn't find ingredients for that link.")
            return

        response_text = "Ingredients:\n" + "\n".join([f"- {ing.quantity} {ing.name}" for ing in ingredients])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text)

    except Exception as e:
        logging.error(f"Unexpected error in get_ingredients: {e}", exc_info=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="An unexpected error occurred.") 


if __name__ == '__main__':

    application = ApplicationBuilder().token(API_TOKEN).build()
    application.bot_data['llm_api'] = GeminiAPI()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    
    get_ingredients_handler = CommandHandler('get_ingredients', get_ingredients_command)
    application.add_handler(get_ingredients_handler)

    unknown_handler = MessageHandler(filters.COMMAND | filters.TEXT, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()