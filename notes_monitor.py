import json
import hashlib
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

logger = logging.getLogger(__name__)

class NotesMonitor:
    def __init__(self, icloud_email: str = None, icloud_password: str = None):
        self.notes_cache = {}
        self.last_check = None
        self.changes_log = []
        self.icloud_email = icloud_email
        self.icloud_password = icloud_password
        self.driver = None
        
    def setup_driver(self):
        """Настраивает Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Явно указываем путь к chromedriver
            service = Service('./chromedriver/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при настройке ChromeDriver: {e}")
            return False
    
    def login_to_icloud(self) -> bool:
        """Выполняет вход в iCloud"""
        try:
            if not self.driver:
                if not self.setup_driver():
                    return False
            
            logger.info("Переходим на страницу входа в iCloud...")
            self.driver.get('https://www.icloud.com/')
            
            # Ждем загрузки страницы входа
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "account_name_text_field"))
            )
            
            # Вводим email
            email_field = self.driver.find_element(By.ID, "account_name_text_field")
            email_field.clear()
            email_field.send_keys(self.icloud_email)
            
            # Нажимаем кнопку "Далее"
            next_button = self.driver.find_element(By.ID, "sign-in")
            next_button.click()
            
            # Ждем поля для пароля
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password_text_field"))
            )
            
            # Вводим пароль
            password_field = self.driver.find_element(By.ID, "password_text_field")
            password_field.clear()
            password_field.send_keys(self.icloud_password)
            
            # Нажимаем кнопку входа
            sign_in_button = self.driver.find_element(By.ID, "sign-in")
            sign_in_button.click()
            
            # Ждем загрузки главной страницы iCloud
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "app-icon"))
            )
            
            logger.info("Успешный вход в iCloud")
            return True
            
        except TimeoutException:
            logger.error("Таймаут при входе в iCloud")
            return False
        except Exception as e:
            logger.error(f"Ошибка при входе в iCloud: {e}")
            return False
    
    def navigate_to_notes(self) -> bool:
        """Переходит к приложению Notes"""
        try:
            # Ищем иконку Notes
            notes_icon = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'app-icon') and contains(@title, 'Notes')]"))
            )
            notes_icon.click()
            
            # Ждем загрузки приложения Notes
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "notes-list"))
            )
            
            logger.info("Успешно перешли к Notes")
            return True
            
        except TimeoutException:
            logger.error("Таймаут при переходе к Notes")
            return False
        except Exception as e:
            logger.error(f"Ошибка при переходе к Notes: {e}")
            return False
    
    def get_notes_hash(self, notes_data: List[Dict]) -> str:
        """Создает хеш от содержимого заметок для отслеживания изменений"""
        content = json.dumps(notes_data, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def check_icloud_notes(self) -> Optional[List[Dict]]:
        """Проверяет заметки через iCloud веб-интерфейс"""
        try:
            if not self.icloud_email or not self.icloud_password:
                logger.error("Не указаны учетные данные iCloud")
                return None
            
            # Выполняем вход
            if not self.login_to_icloud():
                return None
            
            # Переходим к Notes
            if not self.navigate_to_notes():
                return None
            
            # Ждем загрузки списка заметок
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "notes-list"))
            )
            
            # Получаем список заметок
            notes_elements = self.driver.find_elements(By.CSS_SELECTOR, ".note-item, .note")
            notes_data = []
            
            logger.info(f"Найдено {len(notes_elements)} заметок")
            
            for i, note in enumerate(notes_elements):
                try:
                    # Пытаемся получить заголовок
                    try:
                        title_element = note.find_element(By.CSS_SELECTOR, ".note-title, .title")
                        title = title_element.text.strip()
                    except NoSuchElementException:
                        title = f"Заметка {i+1}"
                    
                    # Пытаемся получить содержимое
                    try:
                        content_element = note.find_element(By.CSS_SELECTOR, ".note-content, .content, .preview")
                        content = content_element.text.strip()
                    except NoSuchElementException:
                        content = "Содержимое недоступно"
                    
                    # Пытаемся получить дату изменения
                    try:
                        modified_element = note.find_element(By.CSS_SELECTOR, ".note-modified, .modified, .date")
                        modified = modified_element.text.strip()
                    except NoSuchElementException:
                        modified = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    notes_data.append({
                        'title': title,
                        'content': content,
                        'modified': modified,
                        'index': i
                    })
                    
                except Exception as e:
                    logger.warning(f"Ошибка при парсинге заметки {i}: {e}")
                    continue
            
            logger.info(f"Успешно получено {len(notes_data)} заметок")
            return notes_data
            
        except Exception as e:
            logger.error(f"Ошибка при проверке iCloud заметок: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def check_local_notes(self) -> Optional[List[Dict]]:
        """Проверяет локальные заметки (если доступны)"""
        try:
            notes_path = os.path.expanduser("~/Library/Group Containers/group.com.apple.notes")
            if not os.path.exists(notes_path):
                logger.info("Локальные заметки не найдены")
                return None
                
            notes_data = []
            # Здесь можно добавить логику для чтения локальных файлов заметок
            # Структура может быть сложной, так как это база данных SQLite
            
            return notes_data
            
        except Exception as e:
            logger.error(f"Ошибка при проверке локальных заметок: {e}")
            return None
    
    def detect_changes(self, current_notes: List[Dict]) -> List[Dict]:
        """Определяет изменения в заметках"""
        if not self.notes_cache:
            self.notes_cache = current_notes
            logger.info("Первоначальная загрузка заметок")
            return []
        
        changes = []
        
        # Создаем словари для быстрого поиска
        current_dict = {note['title']: note for note in current_notes}
        cached_dict = {note['title']: note for note in self.notes_cache}
        
        # Проверяем новые и измененные заметки
        for title, note in current_dict.items():
            if title not in cached_dict:
                changes.append({
                    'type': 'new',
                    'title': note['title'],
                    'content': note['content'],
                    'modified': note['modified'],
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Новая заметка: {title}")
            elif note['content'] != cached_dict[title]['content']:
                changes.append({
                    'type': 'modified',
                    'title': note['title'],
                    'old_content': cached_dict[title]['content'],
                    'new_content': note['content'],
                    'modified': note['modified'],
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Изменена заметка: {title}")
        
        # Проверяем удаленные заметки
        for title, note in cached_dict.items():
            if title not in current_dict:
                changes.append({
                    'type': 'deleted',
                    'title': note['title'],
                    'content': note['content'],
                    'modified': note['modified'],
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Удалена заметка: {title}")
        
        self.notes_cache = current_notes
        return changes 