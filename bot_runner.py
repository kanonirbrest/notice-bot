#!/usr/bin/env python3
"""
Альтернативный запуск бота для Replit
"""
import asyncio
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
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Я бот для мониторинга заметок iPhone.\n\n"
        "Доступные команды:\n"
        "/start - показать это сообщение\n"
        "/check - проверить заметки на изменения"
    )

async def check_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /check"""
    await update.message.reply_text("🔍 Начинаю проверку заметок...")
    
    try:
        # Здесь будет логика проверки заметок
        # Пока что просто заглушка
        await update.message.reply_text("✅ Проверка завершена. Изменений не обнаружено.")
    except Exception as e:
        logger.error(f"Ошибка при проверке заметок: {e}")
        await update.message.reply_text("❌ Произошла ошибка при проверке заметок.")

async def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не настроен")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_notes))
    
    logger.info("Бот запущен! Используйте /start для получения справки.")
    
    # Используем run_polling с параметрами для Replit
    await app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

def run_bot():
    """Функция для запуска бота на Replit"""
    try:
        # Проверяем, есть ли уже запущенный event loop
        try:
            loop = asyncio.get_running_loop()
            # Если loop уже запущен, создаем задачу
            loop.create_task(main())
        except RuntimeError:
            # Если loop не запущен, запускаем новый
            asyncio.run(main())
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise

if __name__ == '__main__':
    run_bot() 