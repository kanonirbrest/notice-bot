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
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    import sys
    
    # Простой способ запуска без конфликтов event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        try:
            loop.close()
        except:
            pass 