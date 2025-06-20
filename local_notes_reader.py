# -*- coding: utf-8 -*-
import sqlite3
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class LocalNotesReader:
    def __init__(self):
        self.notes_path = os.path.expanduser("~/Library/Group Containers/group.com.apple.notes")
        self.db_path = None
        self.notes_cache = {}
        
    def find_notes_database(self) -> Optional[str]:
        """Находит файл базы данных заметок"""
        try:
            if not os.path.exists(self.notes_path):
                logger.error(f"Путь к заметкам не найден: {self.notes_path}")
                return None
                
            # Ищем файл базы данных
            for root, dirs, files in os.walk(self.notes_path):
                for file in files:
                    if file.endswith('.sqlite') or file.endswith('.db'):
                        db_path = os.path.join(root, file)
                        logger.info(f"Найдена база данных: {db_path}")
                        return db_path
                        
            logger.error("База данных заметок не найдена")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске базы данных: {e}")
            return None
    
    def get_notes_from_database(self) -> Optional[List[Dict]]:
        """Читает заметки из базы данных SQLite"""
        try:
            if not self.db_path:
                self.db_path = self.find_notes_database()
                if not self.db_path:
                    return None
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем список таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.info(f"Найдены таблицы: {tables}")
            
            notes_data = []
            
            # Пытаемся найти заметки в разных таблицах
            for table in tables:
                table_name = table[0]
                try:
                    # Пробуем получить данные из таблицы
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    logger.info(f"Таблица {table_name}: {columns}")
                    
                    # Если таблица содержит заметки
                    if any('title' in col[1].lower() or 'content' in col[1].lower() for col in columns):
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
                        rows = cursor.fetchall()
                        
                        for row in rows:
                            try:
                                # Пытаемся извлечь данные заметки
                                note = self.parse_note_row(row, columns)
                                if note:
                                    notes_data.append(note)
                            except Exception as e:
                                logger.warning(f"Ошибка при парсинге строки: {e}")
                                continue
                                
                except Exception as e:
                    logger.warning(f"Ошибка при чтении таблицы {table_name}: {e}")
                    continue
            
            conn.close()
            
            if not notes_data:
                logger.warning("Заметки не найдены в базе данных")
                return None
                
            logger.info(f"Успешно прочитано {len(notes_data)} заметок")
            return notes_data
            
        except Exception as e:
            logger.error(f"Ошибка при чтении базы данных: {e}")
            return None
    
    def parse_note_row(self, row: tuple, columns: List[tuple]) -> Optional[Dict]:
        """Парсит строку из базы данных в объект заметки"""
        try:
            note = {}
            
            for i, col in enumerate(columns):
                col_name = col[1].lower()
                value = row[i] if i < len(row) else None
                
                if 'title' in col_name and value:
                    note['title'] = str(value)
                elif 'content' in col_name and value:
                    note['content'] = str(value)
                elif 'date' in col_name or 'modified' in col_name or 'created' in col_name:
                    if value:
                        try:
                            # Пытаемся преобразовать timestamp в читаемую дату
                            if isinstance(value, (int, float)):
                                dt = datetime.fromtimestamp(value)
                                note['modified'] = dt.strftime("%Y-%m-%d %H:%M")
                            else:
                                note['modified'] = str(value)
                        except:
                            note['modified'] = str(value)
            
            # Если есть хотя бы заголовок или содержимое
            if note.get('title') or note.get('content'):
                if not note.get('title'):
                    note['title'] = f"Заметка {len(note)}"
                if not note.get('content'):
                    note['content'] = "Содержимое недоступно"
                if not note.get('modified'):
                    note['modified'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                return note
                
            return None
            
        except Exception as e:
            logger.warning(f"Ошибка при парсинге строки заметки: {e}")
            return None
    
    def get_notes_hash(self, notes_data: List[Dict]) -> str:
        """Создает хеш от содержимого заметок для отслеживания изменений"""
        content = json.dumps(notes_data, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def detect_changes(self, current_notes: List[Dict]) -> List[Dict]:
        """Определяет изменения в заметках"""
        if not self.notes_cache:
            self.notes_cache = current_notes
            logger.info("Первоначальная загрузка заметок")
            return []
        
        changes = []
        
        # Создаем словари для быстрого поиска
        current_dict = {note.get('title', f"note_{i}"): note for i, note in enumerate(current_notes)}
        cached_dict = {note.get('title', f"note_{i}"): note for i, note in enumerate(self.notes_cache)}
        
        # Проверяем новые и измененные заметки
        for title, note in current_dict.items():
            if title not in cached_dict:
                changes.append({
                    'type': 'new',
                    'title': note.get('title', 'Без названия'),
                    'content': note.get('content', ''),
                    'modified': note.get('modified', ''),
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Новая заметка: {title}")
            elif note.get('content') != cached_dict[title].get('content'):
                changes.append({
                    'type': 'modified',
                    'title': note.get('title', 'Без названия'),
                    'old_content': cached_dict[title].get('content', ''),
                    'new_content': note.get('content', ''),
                    'modified': note.get('modified', ''),
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Изменена заметка: {title}")
        
        # Проверяем удаленные заметки
        for title, note in cached_dict.items():
            if title not in current_dict:
                changes.append({
                    'type': 'deleted',
                    'title': note.get('title', 'Без названия'),
                    'content': note.get('content', ''),
                    'modified': note.get('modified', ''),
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Удалена заметка: {title}")
        
        self.notes_cache = current_notes
        return changes
    
    def check_local_notes(self) -> Optional[List[Dict]]:
        """Основной метод для проверки локальных заметок"""
        return self.get_notes_from_database() 