import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# iCloud настройки (для будущего использования)
ICLOUD_EMAIL = os.getenv('ICLOUD_EMAIL')
ICLOUD_PASSWORD = os.getenv('ICLOUD_PASSWORD') 