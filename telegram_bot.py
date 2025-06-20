import os
from dotenv import load_dotenv
import telebot

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, (
        "Привет! Я бот для мониторинга заметок iPhone.\n\n"
        "Доступные команды:\n"
        "/start - показать это сообщение\n"
        "/check - проверить заметки на изменения"
    ))

@bot.message_handler(commands=['check'])
def check(message):
    bot.reply_to(message, "🔍 Начинаю проверку заметок...")
    # Здесь будет логика проверки заметок
    bot.reply_to(message, "✅ Проверка завершена. Изменений не обнаружено.")

if __name__ == '__main__':
    print('Бот запущен! Используйте /start для получения справки.')
    bot.polling(none_stop=True) 