#!/usr/bin/env python3
"""
Скрипт для автоматической установки ChromeDriver
"""

import os
import sys
import platform
import urllib.request
import zipfile
import tarfile
import subprocess
import shutil
import json

def get_chrome_version():
    """Получает версию Chrome"""
    try:
        if platform.system() == "Darwin":  # macOS
            # Путь к Chrome на macOS
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(chrome_path):
                result = subprocess.run([chrome_path, "--version"], 
                                      capture_output=True, text=True)
                version = result.stdout.strip().split()[-1]
                return version.split('.')[0]  # Возвращаем major version
    except Exception as e:
        print(f"Ошибка при получении версии Chrome: {e}")
    
    return "120"  # Версия по умолчанию

def get_latest_chromedriver_version():
    """Получает последнюю версию ChromeDriver"""
    try:
        url = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone.json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            # Получаем последнюю стабильную версию
            latest_version = data.get("milestones", {}).get("stable", {}).get("version", "120.0.6099.109")
            return latest_version.split('.')[0]  # Возвращаем major version
    except Exception as e:
        print(f"Ошибка при получении последней версии ChromeDriver: {e}")
        return "120"

def download_chromedriver(version):
    """Скачивает ChromeDriver"""
    system = platform.system()
    machine = platform.machine()
    
    if system == "Darwin":  # macOS
        if machine == "arm64":
            arch = "mac-arm64"
        else:
            arch = "mac-x64"
    elif system == "Linux":
        arch = "linux64"
    elif system == "Windows":
        arch = "win32"
    else:
        print(f"Неподдерживаемая система: {system}")
        return False
    
    # Используем новый URL для ChromeDriver
    url = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{version}.0.6099.109/{arch}/chromedriver-{arch}.zip"
    
    try:
        print(f"Скачиваю ChromeDriver версии {version} для {arch}...")
        urllib.request.urlretrieve(url, "chromedriver.zip")
        
        print("Распаковываю ChromeDriver...")
        with zipfile.ZipFile("chromedriver.zip", 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Переименовываем файл если нужно
        extracted_files = [f for f in os.listdir('.') if f.startswith('chromedriver')]
        if extracted_files:
            if extracted_files[0] != 'chromedriver':
                os.rename(extracted_files[0], 'chromedriver')
        
        # Делаем файл исполняемым
        os.chmod("chromedriver", 0o755)
        
        # Удаляем zip файл
        os.remove("chromedriver.zip")
        
        print("ChromeDriver успешно установлен!")
        return True
        
    except Exception as e:
        print(f"Ошибка при скачивании ChromeDriver: {e}")
        return False

def main():
    print("Установка ChromeDriver для мониторинга заметок iCloud...")
    
    # Получаем версию Chrome
    chrome_version = get_chrome_version()
    print(f"Обнаружена версия Chrome: {chrome_version}")
    
    # Получаем последнюю версию ChromeDriver
    chromedriver_version = get_latest_chromedriver_version()
    print(f"Используем ChromeDriver версии: {chromedriver_version}")
    
    # Скачиваем ChromeDriver
    if download_chromedriver(chromedriver_version):
        print("\n✅ ChromeDriver готов к использованию!")
        print("Теперь вы можете запустить бота командой: python3 telegram_bot.py")
    else:
        print("\n❌ Не удалось установить ChromeDriver")
        print("Попробуйте установить его вручную:")
        print("1. Перейдите на https://chromedriver.chromium.org/")
        print("2. Скачайте версию, соответствующую вашему Chrome")
        print("3. Распакуйте в папку проекта")

if __name__ == "__main__":
    main() 