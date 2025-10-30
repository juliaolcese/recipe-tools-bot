import logging
import asyncio
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv
from agent import Agent

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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, 
            action='typing'
        )
        agent = context.bot_data['agent']
        
        try:
            response_text = await asyncio.to_thread(agent.invoke, update.message.text)
            
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text)

        except Exception as e:
            logging.error(f"Unexpected error in handle_message: {e}", exc_info=True)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, an error occurred.")

if __name__ == '__main__':

    application = ApplicationBuilder().token(API_TOKEN).build()
    application.bot_data['agent'] = Agent()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(message_handler)
    
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()