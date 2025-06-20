import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# iCloud настройки
ICLOUD_EMAIL = os.getenv('ICLOUD_EMAIL')
ICLOUD_PASSWORD = os.getenv('ICLOUD_PASSWORD')

# Настройки мониторинга
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))  # 5 минут по умолчанию

# Путь к локальным заметкам (если используется)
LOCAL_NOTES_PATH = os.getenv('LOCAL_NOTES_PATH', '~/Library/Group Containers/group.com.apple.notes') 