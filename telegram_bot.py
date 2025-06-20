# -*- coding: utf-8 -*-
import os
import requests
from dotenv import load_dotenv
import telebot

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def get_rhymes(word):
    """Получает рифмы к слову через RhymeBrain API"""
    try:
        # Используем бесплатный RhymeBrain API
        url = f"https://rhymebrain.com/talk"
        params = {
            'function': 'getRhymes',
            'word': word,
            'lang': 'ru'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        rhymes = response.json()
        
        # Фильтруем и сортируем рифмы по качеству
        filtered_rhymes = []
        for rhyme in rhymes:
            if rhyme.get('score', 0) > 0:  # Только рифмы с положительным скором
                filtered_rhymes.append({
                    'word': rhyme.get('word', ''),
                    'score': rhyme.get('score', 0),
                    'freq': rhyme.get('freq', 0)
                })
        
        # Сортируем по скору (качеству рифмы)
        filtered_rhymes.sort(key=lambda x: x['score'], reverse=True)
        
        return filtered_rhymes
        
    except Exception as e:
        print(f"Ошибка при получении рифм: {e}")
        # Fallback на Datamuse API
        try:
            url = f"https://api.datamuse.com/words"
            params = {
                'rel_rhy': word,
                'max': 10,
                'lang': 'ru'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            rhymes = response.json()
            return rhymes
        except:
            return []

def format_rhymes(rhymes, original_word):
    """Форматирует список рифм для вывода"""
    if not rhymes:
        return f"😔 К сожалению, рифмы к слову '{original_word}' не найдены.\n\nПопробуйте другое слово!"
    
    result = f"🎵 Рифмы к слову '{original_word}':\n\n"
    
    for i, rhyme in enumerate(rhymes[:10], 1):
        word = rhyme.get('word', '')
        score = rhyme.get('score', 0)
        
        # Добавляем эмодзи в зависимости от качества рифмы
        if score > 1000:
            emoji = "⭐"
        elif score > 500:
            emoji = "✨"
        else:
            emoji = "💫"
        
        result += f"{i}. {emoji} {word}\n"
    
    result += f"\nНайдено рифм: {len(rhymes)}"
    return result

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, (
        "🎵 Привет! Я бот для поиска рифм.\n\n"
        "Просто напиши любое слово, и я найду к нему рифмы!\n\n"
        "Доступные команды:\n"
        "/start - показать это сообщение\n"
        "/help - справка по использованию\n\n"
        "Пример: напиши 'дом' и получишь рифмы!"
    ))

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, (
        "🎵 Как использовать бота:\n\n"
        "1. Просто напиши любое слово\n"
        "2. Бот найдет к нему рифмы\n"
        "3. Рифмы отсортированы по качеству\n\n"
        "Примеры слов для тестирования:\n"
        "• дом\n"
        "• любовь\n"
        "• солнце\n"
        "• песня\n\n"
        "Бот работает с русскими словами!"
    ))

@bot.message_handler(func=lambda message: True)
def handle_word(message):
    word = message.text.strip().lower()
    
    # Проверяем, что это не команда
    if word.startswith('/'):
        return
    
    # Проверяем, что это слово (не пустая строка и не слишком длинное)
    if not word or len(word) > 50:
        bot.reply_to(message, "Пожалуйста, введите слово (не более 50 символов).")
        return
    
    # Отправляем сообщение о поиске
    search_msg = bot.reply_to(message, f"🔍 Ищу рифмы к слову '{word}'...")
    
    # Получаем рифмы
    rhymes = get_rhymes(word)
    
    # Форматируем результат
    result = format_rhymes(rhymes, word)
    
    # Отправляем результат
    bot.edit_message_text(
        result,
        chat_id=search_msg.chat.id,
        message_id=search_msg.message_id
    )

if __name__ == '__main__':
    print('🎵 Бот для поиска рифм запущен!')
    print('Используйте /start для получения справки.')
    bot.polling(none_stop=True) 