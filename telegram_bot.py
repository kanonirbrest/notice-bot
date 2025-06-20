# -*- coding: utf-8 -*-
import os
import requests
import io
import tempfile
from dotenv import load_dotenv
import telebot
from pydub import AudioSegment
from pydub.effects import speedup, normalize
import numpy as np

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

def apply_audio_effect(audio_file, effect_type="echo"):
    """Применяет звуковой эффект к аудиофайлу"""
    try:
        # Загружаем аудио
        audio = AudioSegment.from_file(audio_file)
        
        if effect_type == "echo":
            # Эффект эхо
            delay_ms = 200
            decay = 0.5
            echo = audio - (decay * 20)  # Уменьшаем громкость
            combined = audio.overlay(echo, position=delay_ms)
            
        elif effect_type == "reverb":
            # Простой реверб
            reverb = audio - 10  # Уменьшаем громкость
            combined = audio.overlay(reverb, position=100)
            combined = combined.overlay(reverb, position=200)
            
        elif effect_type == "speedup":
            # Ускорение
            combined = speedup(audio, playback_speed=1.5)
            
        elif effect_type == "slowdown":
            # Замедление
            combined = speedup(audio, playback_speed=0.7)
            
        elif effect_type == "pitch_up":
            # Повышение тона
            combined = audio._spawn(audio.raw_data, overrides={'frame_rate': int(audio.frame_rate * 1.2)})
            combined = combined.set_frame_rate(audio.frame_rate)
            
        elif effect_type == "pitch_down":
            # Понижение тона
            combined = audio._spawn(audio.raw_data, overrides={'frame_rate': int(audio.frame_rate * 0.8)})
            combined = combined.set_frame_rate(audio.frame_rate)
            
        elif effect_type == "normalize":
            # Нормализация громкости
            combined = normalize(audio)
            
        else:
            # По умолчанию - эхо
            delay_ms = 200
            decay = 0.5
            echo = audio - (decay * 20)
            combined = audio.overlay(echo, position=delay_ms)
        
        return combined
        
    except Exception as e:
        print(f"Ошибка при применении эффекта: {e}")
        return None

def download_voice_file(file_id):
    """Скачивает голосовое сообщение"""
    try:
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
        
        response = requests.get(file_url)
        response.raise_for_status()
        
        return io.BytesIO(response.content)
        
    except Exception as e:
        print(f"Ошибка при скачивании файла: {e}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, (
        "🎵 Привет! Я бот для поиска рифм и обработки аудио.\n\n"
        "Доступные функции:\n"
        "• Напиши слово → найду рифмы\n"
        "• Отправь голосовое сообщение → применю эффект\n\n"
        "Команды:\n"
        "/start - показать это сообщение\n"
        "/help - справка по использованию\n"
        "/effects - список доступных эффектов"
    ))

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, (
        "🎵 Как использовать бота:\n\n"
        "**Поиск рифм:**\n"
        "1. Просто напиши любое слово\n"
        "2. Бот найдет к нему рифмы\n\n"
        "**Обработка аудио:**\n"
        "1. Отправь голосовое сообщение\n"
        "2. Выбери эффект из списка\n"
        "3. Получи обработанное аудио\n\n"
        "Используй /effects для списка доступных эффектов!"
    ))

@bot.message_handler(commands=['effects'])
def effects_command(message):
    bot.reply_to(message, (
        "🎛️ Доступные звуковые эффекты:\n\n"
        "• **echo** - эхо\n"
        "• **reverb** - реверберация\n"
        "• **speedup** - ускорение\n"
        "• **slowdown** - замедление\n"
        "• **pitch_up** - повышение тона\n"
        "• **pitch_down** - понижение тона\n"
        "• **normalize** - нормализация громкости\n\n"
        "Отправь голосовое сообщение, затем выбери эффект!"
    ))

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    """Обрабатывает голосовые сообщения"""
    try:
        # Отправляем сообщение о начале обработки
        processing_msg = bot.reply_to(message, "🎵 Обрабатываю голосовое сообщение...")
        
        # Скачиваем файл
        voice_file = download_voice_file(message.voice.file_id)
        if not voice_file:
            bot.edit_message_text("❌ Не удалось скачать голосовое сообщение", 
                                chat_id=processing_msg.chat.id, 
                                message_id=processing_msg.message_id)
            return
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            temp_file.write(voice_file.getvalue())
            temp_file_path = temp_file.name
        
        # Применяем эффект (по умолчанию эхо)
        processed_audio = apply_audio_effect(temp_file_path, "echo")
        
        if processed_audio:
            # Сохраняем обработанное аудио
            output_path = temp_file_path.replace('.ogg', '_processed.ogg')
            processed_audio.export(output_path, format='ogg')
            
            # Отправляем обработанное аудио
            with open(output_path, 'rb') as audio_file:
                bot.send_voice(message.chat.id, audio_file, 
                             caption="🎛️ Обработанное аудио с эффектом эхо")
            
            # Удаляем временные файлы
            os.unlink(temp_file_path)
            os.unlink(output_path)
            
            bot.edit_message_text("✅ Аудио обработано! Отправлено с эффектом эхо.", 
                                chat_id=processing_msg.chat.id, 
                                message_id=processing_msg.message_id)
        else:
            bot.edit_message_text("❌ Не удалось применить эффект к аудио", 
                                chat_id=processing_msg.chat.id, 
                                message_id=processing_msg.message_id)
            
    except Exception as e:
        print(f"Ошибка при обработке голосового сообщения: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при обработке аудио")

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
    print('🎵 Бот для поиска рифм и обработки аудио запущен!')
    print('Используйте /start для получения справки.')
    bot.polling(none_stop=True) 