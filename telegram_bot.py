import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TELEGRAM_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот работает.")

async def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не настроен")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    logger.info("Минимальный бот запущен! Используйте /start.")
    
    # Запускаем бота без автоматического закрытия event loop
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Держим бота запущенным
    try:
        await app.updater.idle()
    except KeyboardInterrupt:
        pass
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    import asyncio
    
    # Запускаем без asyncio.run для избежания конфликтов
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}") 