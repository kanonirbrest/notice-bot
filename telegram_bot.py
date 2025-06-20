# -*- coding: utf-8 -*-
import os
import requests
import io
import tempfile
from dotenv import load_dotenv
import telebot

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"

# Список доступных голосов ElevenLabs (можно расширить)
ELEVENLABS_VOICES = {
    'male': 'pNInz6obpgDQGcFmaJgB',  # Adam - мужской
    'female': 'EXAVITQu4vr4xnSDxMaL',  # Bella - женский
    'child': 'VR6AewLTigWG4xSOukaG',  # Josh - детский
    'elderly': 'pNInz6obpgDQGcFmaJgB',  # Adam - пожилой
    'robot': 'VR6AewLTigWG4xSOukaG',  # Josh - робот
    'deep': 'pNInz6obpgDQGcFmaJgB',  # Adam - глубокий
    'high': 'EXAVITQu4vr4xnSDxMaL',  # Bella - высокий
    'fast': 'VR6AewLTigWG4xSOukaG',  # Josh - быстрый
    'slow': 'pNInz6obpgDQGcFmaJgB',  # Adam - медленный
}
DEFAULT_VOICE = 'male'

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

def speech_to_text(audio_bytes):
    """Конвертирует аудио в текст через ElevenLabs Speech-to-Text"""
    try:
        headers = {
            'xi-api-key': ELEVENLABS_API_KEY
        }
        
        files = {
            'audio': ('voice.ogg', audio_bytes, 'audio/ogg')
        }
        
        response = requests.post(
            f"{ELEVENLABS_API_URL}/speech-to-text",
            headers=headers,
            files=files,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get('text', '')
        else:
            print(f"Ошибка STT: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Ошибка при конвертации в текст: {e}")
        return None

def text_to_speech(text, voice_id=DEFAULT_VOICE):
    """Конвертирует текст в речь через ElevenLabs"""
    try:
        headers = {
            'xi-api-key': ELEVENLABS_API_KEY,
            'Content-Type': 'application/json'
        }
        
        data = {
            'text': text,
            'model_id': 'eleven_multilingual_v2',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.5
            }
        }
        
        response = requests.post(
            f"{ELEVENLABS_API_URL}/text-to-speech/{ELEVENLABS_VOICES.get(voice_id, ELEVENLABS_VOICES[DEFAULT_VOICE])}",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.content
        else:
            print(f"Ошибка TTS: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Ошибка при конвертации в речь: {e}")
        return None

def elevenlabs_transform(audio_bytes, voice_type=DEFAULT_VOICE):
    """Обрабатывает аудио через ElevenLabs: STT -> TTS с новым голосом"""
    try:
        # Шаг 1: Конвертируем аудио в текст
        print("🎤 Конвертирую аудио в текст...")
        text = speech_to_text(audio_bytes)
        
        if not text:
            print("❌ Не удалось распознать речь")
            return None
        
        print(f"📝 Распознанный текст: {text}")
        
        # Шаг 2: Конвертируем текст обратно в речь с новым голосом
        print(f"🎭 Конвертирую в речь с голосом: {voice_type}")
        audio_result = text_to_speech(text, voice_type)
        
        if audio_result:
            print("✅ Успешно обработано через ElevenLabs!")
            return audio_result
        else:
            print("❌ Не удалось сгенерировать речь")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка при обработке через ElevenLabs: {e}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, (
        "🎭 Привет! Я бот для изменения голоса через ElevenLabs.\n\n"
        "Отправь голосовое сообщение — я изменю его на другой голос!\n\n"
        "/voices — список голосов\n"
        "/help — справка"
    ))

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, (
        "🎭 Как использовать бота:\n\n"
        "1. Отправь голосовое сообщение\n"
        "2. По умолчанию применяется мужской голос\n"
        "3. Чтобы выбрать другой голос, напиши его название в подписи к голосовому сообщению или используй /voice <тип>\n\n"
        "/voices — список доступных голосов"
    ))

@bot.message_handler(commands=['voices'])
def voices_command(message):
    voices_list = "\n".join([f"• {voice} - {desc}" for voice, desc in {
        'male': 'Мужской голос',
        'female': 'Женский голос', 
        'child': 'Детский голос',
        'elderly': 'Пожилой голос',
        'robot': 'Робот',
        'deep': 'Глубокий голос',
        'high': 'Высокий голос',
        'fast': 'Быстрая речь',
        'slow': 'Медленная речь'
    }.items()])
    
    bot.reply_to(message, (
        f"🎭 Доступные голоса ElevenLabs:\n\n{voices_list}\n\n"
        "Пример: отправь голосовое с подписью 'female' или напиши /voice female"
    ))

# Храним выбранный голос для каждого пользователя
user_voice = {}

@bot.message_handler(commands=['voice'])
def set_voice(message):
    voice_type = message.text.split(maxsplit=1)[-1].strip().lower()
    if voice_type in ELEVENLABS_VOICES:
        user_voice[message.from_user.id] = voice_type
        bot.reply_to(message, f"✅ Голос для ваших сообщений: {voice_type}")
    else:
        bot.reply_to(message, f"❌ Голос '{voice_type}' не найден. Используйте /voices для списка.")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        # Определяем голос: из подписи или из user_voice, иначе дефолт
        voice_type = DEFAULT_VOICE
        if message.caption and message.caption.lower() in ELEVENLABS_VOICES:
            voice_type = message.caption.lower()
        elif message.from_user.id in user_voice:
            voice_type = user_voice[message.from_user.id]
        
        processing_msg = bot.reply_to(message, f"🎭 Обрабатываю голос с эффектом: {voice_type}...")
        voice_file = download_voice_file(message.voice.file_id)
        
        if not voice_file:
            bot.edit_message_text("❌ Не удалось скачать голосовое сообщение", 
                                chat_id=processing_msg.chat.id, 
                                message_id=processing_msg.message_id)
            return
        
        result_audio = elevenlabs_transform(voice_file, voice_type)
        
        if result_audio:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(result_audio)
                temp_file_path = temp_file.name
            
            with open(temp_file_path, 'rb') as audio_file:
                bot.send_voice(message.chat.id, audio_file, 
                             caption=f"🎭 Ваш голос с эффектом: {voice_type}")
            
            os.unlink(temp_file_path)
            bot.edit_message_text("✅ Готово!", 
                                chat_id=processing_msg.chat.id, 
                                message_id=processing_msg.message_id)
        else:
            bot.edit_message_text("❌ Не удалось обработать аудио через ElevenLabs", 
                                chat_id=processing_msg.chat.id, 
                                message_id=processing_msg.message_id)
            
    except Exception as e:
        print(f"Ошибка при обработке голосового: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при обработке аудио")

if __name__ == '__main__':
    print('🎭 Бот ElevenLabs запущен!')
    print('Используйте /start для справки.')
    bot.polling(none_stop=True) 