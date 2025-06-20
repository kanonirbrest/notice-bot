# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
import telebot
from local_notes_reader import LocalNotesReader

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
    bot.reply_to(message, "🔍 Начинаю проверку локальных заметок...")
    reader = LocalNotesReader()
    notes = reader.check_local_notes()
    if notes is None:
        bot.reply_to(message, "❌ Не удалось получить заметки. Убедитесь, что запускаете на Mac и заметки синхронизированы.")
        return
    changes = reader.detect_changes(notes)
    if not changes:
        bot.reply_to(message, "✅ Проверка завершена. Изменений не обнаружено.")
    else:
        for change in changes:
            if change['type'] == 'new':
                bot.reply_to(message, f"🆕 Новая заметка: {change['title']}\n{change['content']}")
            elif change['type'] == 'modified':
                bot.reply_to(message, f"✏️ Изменена заметка: {change['title']}\nБыло: {change['old_content']}\nСтало: {change['new_content']}")
            elif change['type'] == 'deleted':
                bot.reply_to(message, f"🗑️ Удалена заметка: {change['title']}\n{change['content']}")

if __name__ == '__main__':
    print('Бот запущен! Используйте /start для получения справки.')
    bot.polling(none_stop=True) 