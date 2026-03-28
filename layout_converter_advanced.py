#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Продвинутый конвертер раскладки с глобальными hotkey и автоопределением.
Запускается в фоне (system tray), реагирует на Shift+Pause.
"""

import tkinter as tk
from tkinter import ttk
import pyperclip
import threading
import time
import sys
import os

# Попытка импорта keyboard - если нет, работаем без hotkey
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Warning: keyboard module not available, hotkeys disabled")

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
    """Автоопределение раскладки текста"""
    ru_count = sum(1 for c in text if c in RU_LOWER or c in RU_UPPER)
    en_count = sum(1 for c in text if c in EN_LOWER or c in EN_UPPER)
    
    if ru_count > en_count:
        return 'ru_to_en'  # Вводили как русские буквы, но надо в английские
    else:
        return 'en_to_ru'  # Вводили как английские, но надо в русские

def convert_text(text, mode=None):
    """Конвертировать текст"""
    if not text:
        return text
    
    if mode is None:
        mode = detect_layout(text)
    
    result = []
    for char in text:
        if mode == 'ru_to_en':
            result.append(RU_TO_EN.get(char, char))
        else:
            result.append(EN_TO_RU.get(char, char))
    
    return ''.join(result)

def process_clipboard():
    """
    Главная функция: берёт текст из буфера, конвертирует, кладёт обратно.
    Возвращает (original, converted, mode)
    """
    try:
        original = pyperclip.paste()
        if not original:
            return None, None, None
        
        mode = detect_layout(original)
        converted = convert_text(original, mode)
        
        # Копируем результат в буфер
        pyperclip.copy(converted)
        
        return original, converted, mode
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

class AdvancedLayoutConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер раскладки PRO")
        self.root.geometry("900x500")
        self.root.resizable(True, True)
        
        # Настройка grid
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.last_original = ""
        self.last_converted = ""
        
        self.create_widgets()
        self.setup_hotkeys()
        self.start_clipboard_monitor()
    
    def create_widgets(self):
        # === ВЕРХНЯЯ ПАНЕЛЬ ===
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.grid(row=0, column=0, sticky="ew")
        
        # Статус hotkey
        self.status_var = tk.StringVar(value="⌨️ Hotkey: Shift+Pause" if KEYBOARD_AVAILABLE else "⚠️ Hotkey не доступен")
        ttk.Label(top_frame, textvariable=self.status_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(top_frame, text="▶ Конвертировать сейчас", command=self.manual_convert).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(top_frame, text="🔄 Авто (буфер → конверт → буфер)", command=self.quick_convert).pack(side=tk.RIGHT)
        
        # Инструкция
        ttk.Label(top_frame, text="Выделите текст → Ctrl+C → Shift+Pause → Ctrl+V", 
                  foreground="gray").pack(side=tk.LEFT, padx=(20, 0))
        
        # === ОСНОВНОЙ КОНТЕНТ ===
        content_frame = ttk.Frame(self.root, padding="10")
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        
        # --- ЛЕВОЕ ОКНО (исходный) ---
        left_frame = ttk.LabelFrame(content_frame, text="Исходный текст (из буфера)", padding="5")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        self.left_text = tk.Text(left_frame, wrap=tk.WORD, font=('Consolas', 11))
        self.left_text.grid(row=0, column=0, sticky="nsew")
        
        scrollbar_left = ttk.Scrollbar(left_frame, command=self.left_text.yview)
        scrollbar_left.grid(row=0, column=1, sticky="ns")
        self.left_text.config(yscrollcommand=scrollbar_left.set)
        
        ttk.Button(left_frame, text="📋 Вставить из буфера", command=self.paste_to_left).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        # --- ЦЕНТР (кнопка) ---
        center_frame = ttk.Frame(content_frame)
        center_frame.grid(row=0, column=1, sticky="ns", padx=10)
        
        self.mode_label = ttk.Label(center_frame, text="Авто\nопределение", 
                                     font=('Arial', 9), justify='center')
        self.mode_label.pack(pady=(10, 5))
        
        btn_convert = ttk.Button(center_frame, text="➡\nКонверти-\nровать\n➡", 
                                  command=self.convert_manual, width=12)
        btn_convert.pack(expand=True, fill=tk.Y)
        
        # --- ПРАВОЕ ОКНО (результат) ---
        right_frame = ttk.LabelFrame(content_frame, text="Результат (скопирован в буфер)", padding="5")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        self.right_text = tk.Text(right_frame, wrap=tk.WORD, font=('Consolas', 11))
        self.right_text.grid(row=0, column=0, sticky="nsew")
        
        scrollbar_right = ttk.Scrollbar(right_frame, command=self.right_text.yview)
        scrollbar_right.grid(row=0, column=1, sticky="ns")
        self.right_text.config(yscrollcommand=scrollbar_right.set)
        
        ttk.Button(right_frame, text="📋 Скопировать", command=self.copy_right).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        # === СТАТУС БАР ===
        self.info_var = tk.StringVar(value="Готов. Используйте Shift+Pause для конвертации буфера")
        status_bar = ttk.Label(self.root, textvariable=self.info_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, sticky="ew", pady=(5, 0))
    
    def setup_hotkeys(self):
        """Настройка глобальных hotkey"""
        if KEYBOARD_AVAILABLE:
            try:
                # Shift+Pause - конвертировать буфер
                keyboard.add_hotkey('shift+pause', self.hotkey_convert)
                print("Hotkey Shift+Pause registered")
            except Exception as e:
                print(f"Failed to register hotkey: {e}")
    
    def hotkey_convert(self):
        """Обработчик hotkey Shift+Pause"""
        print("Hotkey pressed!")
        self.quick_convert()
    
    def quick_convert(self):
        """Быстрая конвертация: буфер → конверт → буфер"""
        original, converted, mode = process_clipboard()
        
        if original is not None:
            self.last_original = original
            self.last_converted = converted
            
            # Обновляем окна
            self.left_text.delete('1.0', tk.END)
            self.left_text.insert('1.0', original)
            
            self.right_text.delete('1.0', tk.END)
            self.right_text.insert('1.0', converted)
            
            # Обновляем статус
            mode_text = "RU → EN" if mode == 'ru_to_en' else "EN → RU"
            self.mode_label.config(text=f"Режим:\n{mode_text}")
            self.info_var.set(f"✓ Конвертировано ({mode_text}). Результат в буфере обмена!")
            
            # Мигание окна
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after(500, lambda: self.root.attributes('-topmost', False))
    
    def manual_convert(self):
        """Конвертировать по кнопке"""
        self.quick_convert()
    
    def convert_manual(self):
        """Конвертировать текст из левого окна"""
        text = self.left_text.get('1.0', tk.END)
        mode = detect_layout(text)
        converted = convert_text(text, mode)
        
        self.right_text.delete('1.0', tk.END)
        self.right_text.insert('1.0', converted)
        pyperclip.copy(converted)
        
        mode_text = "RU → EN" if mode == 'ru_to_en' else "EN → RU"
        self.mode_label.config(text=f"Режим:\n{mode_text}")
        self.info_var.set(f"✓ Конвертировано ({mode_text}). Скопировано в буфер!")
    
    def paste_to_left(self):
        """Вставить в левое окно"""
        try:
            text = pyperclip.paste()
            self.left_text.delete('1.0', tk.END)
            self.left_text.insert('1.0', text)
        except Exception as e:
            pass
    
    def copy_right(self):
        """Копировать правое окно"""
        text = self.right_text.get('1.0', tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.info_var.set("✓ Скопировано в буфер")
    
    def start_clipboard_monitor(self):
        """Мониторинг изменений буфера (опционально)"""
        # Можно добавить автообнаружение изменений
        pass
    
    def on_closing(self):
        """При закрытии окна"""
        if KEYBOARD_AVAILABLE:
            keyboard.unhook_all()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedLayoutConverter(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
