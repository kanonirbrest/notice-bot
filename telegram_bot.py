import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from config import TELEGRAM_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Бот работает.")

def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не настроен")
        return
    
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    
    logger.info("Минимальный бот запущен! Используйте /start.")
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main() 