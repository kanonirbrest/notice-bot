# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
import telebot
from config import ICLOUD_EMAIL, ICLOUD_PASSWORD
from selenium_notes_monitor import SeleniumNotesMonitor

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
    bot.reply_to(message, "🔍 Начинаю проверку заметок через iCloud...")
    monitor = SeleniumNotesMonitor(icloud_email=ICLOUD_EMAIL, icloud_password=ICLOUD_PASSWORD)
    notes = monitor.check_icloud_notes()
    if notes is None:
        bot.reply_to(message, "❌ Не удалось получить заметки. Проверьте логин/пароль или 2FA.")
        return
    changes = monitor.detect_changes(notes)
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