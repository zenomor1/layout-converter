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
        self.root.geometry("900x500")
        self.root.resizable(True, True)
        
        # Настройка grid weight для ресайза
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Режим конвертации
        self.mode = tk.StringVar(value="ru_to_en")
        
        self.create_widgets()
    
    def create_widgets(self):
        # === ВЕРХНЯЯ ПАНЕЛЬ (режим) ===
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.grid(row=0, column=0, sticky="ew")
        
        ttk.Label(top_frame, text="Режим:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        self.mode_combo = ttk.Combobox(top_frame, textvariable=self.mode, state="readonly", width=30)
        self.mode_combo['values'] = ('RU → EN (русская раскладка в английскую)', 'EN → RU (английская раскладка в русскую)')
        self.mode_combo.current(0)
        self.mode_combo.pack(side=tk.LEFT)
        
        # === ОСНОВНОЙ КОНТЕНТ ===
        content_frame = ttk.Frame(self.root, padding="10")
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        
        # --- ЛЕВОЕ ОКНО ---
        left_frame = ttk.LabelFrame(content_frame, text="Исходный текст", padding="5")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        self.left_text = tk.Text(left_frame, wrap=tk.WORD, font=('Consolas', 11))
        self.left_text.grid(row=0, column=0, sticky="nsew")
        
        scrollbar_left = ttk.Scrollbar(left_frame, command=self.left_text.yview)
        scrollbar_left.grid(row=0, column=1, sticky="ns")
        self.left_text.config(yscrollcommand=scrollbar_left.set)
        
        btn_paste = ttk.Button(left_frame, text="📋 Вставить из буфера", command=self.paste_text)
        btn_paste.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        # --- ЦЕНТР (кнопка конвертации) ---
        center_frame = ttk.Frame(content_frame)
        center_frame.grid(row=0, column=1, sticky="ns", padx=10)
        
        btn_convert = ttk.Button(center_frame, text="Конверти-\nровать\n➡", 
                                  command=self.convert, width=12)
        btn_convert.pack(expand=True, fill=tk.Y)
        
        # --- ПРАВОЕ ОКНО ---
        right_frame = ttk.LabelFrame(content_frame, text="Результат", padding="5")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        self.right_text = tk.Text(right_frame, wrap=tk.WORD, font=('Consolas', 11))
        self.right_text.grid(row=0, column=0, sticky="nsew")
        
        scrollbar_right = ttk.Scrollbar(right_frame, command=self.right_text.yview)
        scrollbar_right.grid(row=0, column=1, sticky="ns")
        self.right_text.config(yscrollcommand=scrollbar_right.set)
        
        btn_copy = ttk.Button(right_frame, text="📋 Скопировать в буфер", command=self.copy_result)
        btn_copy.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        # === СТАТУС БАР ===
        self.status_var = tk.StringVar(value="Готов к работе. Введите текст слева и нажмите 'Конвертировать'")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, sticky="ew")
    
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
                self.status_var.set("✓ Результат скопирован в буфер")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать: {e}")
    
    def convert(self):
        """Конвертировать текст из левого поля в правое"""
        source_text = self.left_text.get('1.0', tk.END)
        
        # Определяем режим по индексу выбранного элемента
        mode_idx = self.mode_combo.current()
        
        result = []
        for char in source_text:
            if mode_idx == 0:  # RU → EN
                result.append(RU_TO_EN.get(char, char))
            else:  # EN → RU
                result.append(EN_TO_RU.get(char, char))
        
        result_text = ''.join(result)
        
        # Очищаем и вставляем результат
        self.right_text.delete('1.0', tk.END)
        self.right_text.insert('1.0', result_text)
        
        # Автоматически копируем в буфер
        pyperclip.copy(result_text)
        self.status_var.set(f"✓ Конвертировано {len(source_text)} символов. Результат скопирован!")

if __name__ == "__main__":
    root = tk.Tk()
    app = LayoutConverter(root)
    root.mainloop()
