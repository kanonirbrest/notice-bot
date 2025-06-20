# -*- coding: utf-8 -*-
import os
import requests
import io
import tempfile
from dotenv import load_dotenv
import telebot

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
VOICEMOD_API_KEY = os.getenv('VOICEMOD_API_KEY')
VOICEMOD_API_URL = os.getenv('VOICEMOD_API_URL', 'https://api.voicemod.net/v1/voice/transform')

# Список доступных эффектов Voicemod (можно расширить)
VOICEMOD_EFFECTS = [
    'magic-chords', 'alien', 'baby', 'cave', 'robot', 'man', 'woman', 'titan', 'zombie', 'police-radio',
    'megaphone', 'ghost', 'radio', 'underwater', 'vibrato', 'tremolo', 'telephone', 'muscle', 'blockbuster',
    'cathedral', 'helium', 'demon', 'chipmunk', 'deep', 'double', 'echo', 'fast', 'slow', 'reverse', 'monster'
]
DEFAULT_EFFECT = 'magic-chords'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def download_voice_file(file_id):
    try:
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
        response = requests.get(file_url)
        response.raise_for_status()
        return io.BytesIO(response.content)
    except Exception as e:
        print(f"Ошибка при скачивании файла: {e}")
        return None

def voicemod_transform(audio_bytes, effect=DEFAULT_EFFECT):
    # Разные варианты авторизации
    auth_variants = [
        {'Authorization': f'Bearer {VOICEMOD_API_KEY}'},
        {'X-API-Key': VOICEMOD_API_KEY},
        {'api-key': VOICEMOD_API_KEY},
        {'client-key': VOICEMOD_API_KEY},
        {'Authorization': f'Client {VOICEMOD_API_KEY}'},
        {'Authorization': f'ApiKey {VOICEMOD_API_KEY}'},
        {'Authorization': VOICEMOD_API_KEY},
    ]
    
    files = {
        'audio': ('voice.ogg', audio_bytes, 'audio/ogg'),
        'voice': ('voice.ogg', audio_bytes, 'audio/ogg'),
        'file': ('voice.ogg', audio_bytes, 'audio/ogg')
    }
    
    data_variants = [
        {'effect': effect},
        {'voice_effect': effect},
        {'filter': effect},
        {'voice_filter': effect}
    ]
    
    api_urls = [
        'https://api.voicemod.net/v1/voice/transform',
        'https://api.voicemod.net/v2/voice/transform',
        'https://api.voicemod.net/voice/transform',
        'https://api.voicemod.net/transform',
        'https://api.voicemod.net/v1/transform'
    ]
    
    for url in api_urls:
        for auth in auth_variants:
            for data in data_variants:
                for file_key, file_data in files.items():
                    try:
                        headers = auth.copy()
                        headers['Content-Type'] = 'multipart/form-data'
                        
                        current_files = {file_key: file_data}
                        
                        print(f"Пробуем: {url} | Auth: {list(auth.keys())[0]} | Data: {data} | File: {file_key}")
                        response = requests.post(url, headers=headers, files=current_files, data=data, timeout=60)
                        print(f"Статус: {response.status_code}")
                        
                        if response.status_code == 200:
                            print("✅ Успех!")
                            return response.content
                        elif response.status_code == 401:
                            print(f"❌ 401 для {list(auth.keys())[0]}")
                            continue
                        else:
                            print(f"❌ {response.status_code}: {response.text[:100]}")
                            
                    except Exception as e:
                        print(f"❌ Ошибка: {e}")
                        continue
    
    print("❌ Все варианты не сработали")
    return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, (
        "🎤 Привет! Я бот для изменения голоса через Voicemod API.\n\n"
        "Отправь голосовое сообщение — я пришлю версию с эффектом!\n\n"
        "/effects — список эффектов\n"
        "/help — справка"
    ))

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, (
        "🎤 Как использовать бота:\n\n"
        "1. Отправь голосовое сообщение\n"
        "2. По умолчанию применяется эффект 'magic-chords'\n"
        "3. Чтобы выбрать другой эффект, напиши его название в подписи к голосовому сообщению или после /effect <название>\n\n"
        "/effects — список эффектов"
    ))

@bot.message_handler(commands=['effects'])
def effects_command(message):
    bot.reply_to(message, (
        "🎛️ Доступные эффекты Voicemod:\n\n" + ', '.join(VOICEMOD_EFFECTS) +
        "\n\nПример: отправь голосовое с подписью 'robot' или напиши /effect robot перед голосовым."
    ))

# Храним выбранный эффект для каждого пользователя (простая реализация)
user_effect = {}

@bot.message_handler(commands=['effect'])
def set_effect(message):
    effect = message.text.split(maxsplit=1)[-1].strip().lower()
    if effect in VOICEMOD_EFFECTS:
        user_effect[message.from_user.id] = effect
        bot.reply_to(message, f"✅ Эффект для ваших голосовых: {effect}")
    else:
        bot.reply_to(message, f"❌ Эффект '{effect}' не найден. Используйте /effects для списка.")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        # Определяем эффект: из подписи или из user_effect, иначе дефолт
        effect = DEFAULT_EFFECT
        if message.caption and message.caption.lower() in VOICEMOD_EFFECTS:
            effect = message.caption.lower()
        elif message.from_user.id in user_effect:
            effect = user_effect[message.from_user.id]
        
        processing_msg = bot.reply_to(message, f"🎛️ Обрабатываю голос с эффектом: {effect}...")
        voice_file = download_voice_file(message.voice.file_id)
        if not voice_file:
            bot.edit_message_text("❌ Не удалось скачать голосовое сообщение", chat_id=processing_msg.chat.id, message_id=processing_msg.message_id)
            return
        result_audio = voicemod_transform(voice_file, effect)
        if result_audio:
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_file.write(result_audio)
                temp_file_path = temp_file.name
            with open(temp_file_path, 'rb') as audio_file:
                bot.send_voice(message.chat.id, audio_file, caption=f"🎤 Ваш голос с эффектом: {effect}")
            os.unlink(temp_file_path)
            bot.edit_message_text("✅ Готово!", chat_id=processing_msg.chat.id, message_id=processing_msg.message_id)
        else:
            bot.edit_message_text("❌ Не удалось обработать аудио через Voicemod API", chat_id=processing_msg.chat.id, message_id=processing_msg.message_id)
    except Exception as e:
        print(f"Ошибка при обработке голосового: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при обработке аудио")

if __name__ == '__main__':
    print('🎤 Бот Voicemod запущен!')
    print('Используйте /start для справки.')
    bot.polling(none_stop=True) 