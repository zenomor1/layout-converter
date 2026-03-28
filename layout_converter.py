#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Конвертер раскладки клавиатуры (рус/англ)"""

import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip

# Словари раскладок
RU_LOWER = "йцукенгшщзхъфывапролджэячсмитьбю.ё"
RU_UPPER = "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ.Ё"
EN_LOWER = "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
EN_UPPER = "QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?~"

# Создаем словари для конвертации
RU_TO_EN = {}
EN_TO_RU = {}

for ru, en in zip(RU_LOWER, EN_LOWER):
    RU_TO_EN[ru] = en
    EN_TO_RU[en] = ru

for ru, en in zip(RU_UPPER, EN_UPPER):
    RU_TO_EN[ru] = en
    EN_TO_RU[en] = ru

class LayoutConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер раскладки")
        self.root.geometry("700x400")
        self.root.resizable(True, True)
        
        # Режим конвертации
        self.mode = tk.StringVar(value="ru_to_en")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Верхняя панель с выбором режима
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Режим:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        self.mode_combo = ttk.Combobox(top_frame, textvariable=self.mode, state="readonly", width=40)
        self.mode_combo['values'] = ('ru_to_en', 'en_to_ru')
        self.mode_combo.set('ru_to_en')
        self.mode_combo.pack(side=tk.LEFT)
        
        # Основной фрейм для текстовых полей
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левое поле
        left_frame = ttk.LabelFrame(main_frame, text="Исходный текст", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Текстовое поле слева
        self.left_text = tk.Text(left_frame, wrap=tk.WORD, font=('Consolas', 11))
        self.left_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_left = ttk.Scrollbar(left_frame, command=self.left_text.yview)
        scrollbar_left.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_text.config(yscrollcommand=scrollbar_left.set)
        
        # Кнопка Вставить под левым полем
        btn_paste = ttk.Button(left_frame, text="📋 Вставить", command=self.paste_text)
        btn_paste.pack(fill=tk.X, pady=(5, 0))
        
        # Центральная панель с кнопкой
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        btn_convert = ttk.Button(center_frame, text="➡\nКонверти-\nровать\n➡", 
                                  command=self.convert, width=12)
        btn_convert.pack(expand=True, fill=tk.Y)
        
        # Правое поле
        right_frame = ttk.LabelFrame(main_frame, text="Результат", padding="5")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Текстовое поле справа
        self.right_text = tk.Text(right_frame, wrap=tk.WORD, font=('Consolas', 11))
        self.right_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_right = ttk.Scrollbar(right_frame, command=self.right_text.yview)
        scrollbar_right.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_text.config(yscrollcommand=scrollbar_right.set)
        
        # Кнопка Скопировать под правым полем
        btn_copy = ttk.Button(right_frame, text="📋 Скопировать", command=self.copy_result)
        btn_copy.pack(fill=tk.X, pady=(5, 0))
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def paste_text(self):
        """Вставить текст из буфера обмена в левое поле"""
        try:
            text = pyperclip.paste()
            self.left_text.delete('1.0', tk.END)
            self.left_text.insert('1.0', text)
            self.status_var.set("Текст вставлен из буфера")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось вставить текст: {e}")
    
    def copy_result(self):
        """Копировать результат в буфер обмена"""
        try:
            text = self.right_text.get('1.0', tk.END).strip()
            if text:
                pyperclip.copy(text)
                self.status_var.set("Результат скопирован в буфер")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать: {e}")
    
    def convert(self):
        """Конвертировать текст из левого поля в правое"""
        source_text = self.left_text.get('1.0', tk.END)
        mode = self.mode.get()
        
        result = []
        for char in source_text:
            if mode == 'ru_to_en':
                result.append(RU_TO_EN.get(char, char))
            else:
                result.append(EN_TO_RU.get(char, char))
        
        result_text = ''.join(result)
        
        # Очищаем и вставляем результат
        self.right_text.delete('1.0', tk.END)
        self.right_text.insert('1.0', result_text)
        
        # Автоматически копируем в буфер
        pyperclip.copy(result_text)
        self.status_var.set(f"Конвертировано: {len(source_text)} символов. Результат скопирован!")

if __name__ == "__main__":
    root = tk.Tk()
    app = LayoutConverter(root)
    root.mainloop()
