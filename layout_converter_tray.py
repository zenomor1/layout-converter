#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конвертер раскладки в системном трее с автозаменой текста.
При нажатии Shift+Pause выделенный текст автоматически заменяется.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
import os

# Попытка импорта необходимых модулей
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    print("Error: pyperclip not available")
    sys.exit(1)

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Error: keyboard module not available")
    sys.exit(1)

# Словари раскладок
RU_LOWER = "йцукенгшщзхъфывапролджэячсмитьбю.ё"
RU_UPPER = "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ.Ё"
EN_LOWER = "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
EN_UPPER = "QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?~"

RU_TO_EN = {}
EN_TO_RU = {}

for ru, en in zip(RU_LOWER, EN_LOWER):
    RU_TO_EN[ru] = en
    EN_TO_RU[en] = ru

for ru, en in zip(RU_UPPER, EN_UPPER):
    RU_TO_EN[ru] = en
    EN_TO_RU[en] = ru

def detect_layout(text):
    """Автоопределение раскладки"""
    ru_count = sum(1 for c in text if c in RU_LOWER or c in RU_UPPER)
    en_count = sum(1 for c in text if c in EN_LOWER or c in EN_UPPER)
    return 'ru_to_en' if ru_count > en_count else 'en_to_ru'

def convert_text(text):
    """Конвертировать текст с автоопределением"""
    if not text:
        return text
    
    mode = detect_layout(text)
    result = []
    
    for char in text:
        if mode == 'ru_to_en':
            result.append(RU_TO_EN.get(char, char))
        else:
            result.append(EN_TO_RU.get(char, char))
    
    return ''.join(result), mode

class TrayConverter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LayoutConverter Tray")
        self.root.geometry("400x200")
        
        # Сразу прячем окно
        self.root.withdraw()
        
        self.create_menu()
        self.setup_hotkey()
        
        # Статус
        self.conversion_count = 0
        
        print("Конвертер запущен в фоновом режиме")
        print("Hotkey: Shift+Pause")
        print("Нажмите Shift+Pause для автозамены выделенного текста")
    
    def create_menu(self):
        """Создать контекстное меню по правому клику в трее"""
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Показать статистику", command=self.show_stats)
        self.menu.add_separator()
        self.menu.add_command(label="Выйти", command=self.exit_app)
        
        # Обработка клика по иконке (симуляция через окно)
        self.root.bind("<Button-3>", self.show_menu)
    
    def show_menu(self, event=None):
        """Показать меню"""
        self.menu.post(self.root.winfo_x(), self.root.winfo_y())
    
    def show_stats(self):
        """Показать окно со статистикой"""
        self.root.deiconify()
        
        # Очищаем окно
        for widget in self.root.winfo_children():
            widget.destroy()
        
        ttk.Label(self.root, text="LayoutConverter Tray", 
                   font=('Arial', 14, 'bold')).pack(pady=10)
        
        ttk.Label(self.root, text=f"Конвертаций: {self.conversion_count}",
                   font=('Arial', 11)).pack(pady=5)
        
        ttk.Label(self.root, text="Hotkey: Shift+Pause", 
                   foreground="gray").pack(pady=5)
        
        ttk.Button(self.root, text="Скрыть", 
                  command=self.hide_window).pack(pady=10)
        
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
    
    def hide_window(self):
        """Скрыть окно в трей"""
        self.root.withdraw()
    
    def setup_hotkey(self):
        """Настроить глобальный hotkey"""
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.add_hotkey('shift+pause', self.auto_convert, suppress=False)
                print("Hotkey Shift+Pause зарегистрирован")
            except Exception as e:
                print(f"Ошибка регистрации hotkey: {e}")
    
    def auto_convert(self):
        """
        Автоматическая конвертация:
        1. Копируем выделенный текст (Ctrl+C)
        2. Читаем из буфера
        3. Конвертируем
        4. Записываем в буфер
        5. Вставляем (Ctrl+V)
        """
        try:
            # Эмулируем Ctrl+C
            keyboard.send('ctrl+c')
            time.sleep(0.1)  # Даём время на копирование
            
            # Читаем из буфера
            original = pyperclip.paste()
            if not original:
                return
            
            # Конвертируем
            converted, mode = convert_text(original)
            
            # Проверяем, изменился ли текст
            if converted == original:
                return
            
            # Записываем в буфер
            pyperclip.copy(converted)
            time.sleep(0.05)
            
            # Эмулируем Ctrl+V
            keyboard.send('ctrl+v')
            
            # Счётчик
            self.conversion_count += 1
            
            print(f"Конвертировано: {mode} ({len(original)} символов)")
            
        except Exception as e:
            print(f"Ошибка конвертации: {e}")
    
    def exit_app(self):
        """Выход из приложения"""
        if KEYBOARD_AVAILABLE:
            keyboard.unhook_all()
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Запустить главный цикл"""
        self.root.mainloop()

if __name__ == "__main__":
    app = TrayConverter()
    app.run()
