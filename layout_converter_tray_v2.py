#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конвертер раскладки с иконкой в трее и продвинутой заменой.
При нажатии Shift+Pause выделенный текст автоматически заменяется.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
import os

# Импорты
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

class TrayConverterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LayoutConverter Tray")
        self.root.geometry("500x350")
        
        # Переменные настроек
        self.save_clipboard = tk.BooleanVar(value=True)  # Сохранять историю буфера
        self.show_notification = tk.BooleanVar(value=True)  # Показывать уведомления
        self.conversion_count = 0
        self.last_clipboard = ""  # Для восстановления
        
        self.create_main_window()
        self.setup_tray_icon()
        self.setup_hotkey()
    
    def create_main_window(self):
        """Создать главное окно настроек"""
        # Заголовок
        ttk.Label(self.root, text="LayoutConverter Tray", 
                   font=('Arial', 16, 'bold')).pack(pady=10)
        
        ttk.Label(self.root, text="Конвертер раскладки с автозаменой",
                   foreground="gray").pack()
        
        # Инструкция
        frame_info = ttk.LabelFrame(self.root, text="Как использовать", padding="10")
        frame_info.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(frame_info, text="1. Выделите текст с неправильной раскладкой",
                   anchor=tk.W).pack(fill=tk.X)
        ttk.Label(frame_info, text="2. Нажмите Shift+Pause",
                   anchor=tk.W).pack(fill=tk.X)
        ttk.Label(frame_info, text="3. Текст автоматически заменится на правильный",
                   anchor=tk.W).pack(fill=tk.X)
        
        # Настройки
        frame_settings = ttk.LabelFrame(self.root, text="Настройки", padding="10")
        frame_settings.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Checkbutton(frame_settings, text="Сохранять историю буфера обмена (восстанавливать после конвертации)",
                       variable=self.save_clipboard).pack(anchor=tk.W)
        
        ttk.Checkbutton(frame_settings, text="Показывать уведомления в трее",
                       variable=self.show_notification).pack(anchor=tk.W)
        
        # Статистика
        self.stats_label = ttk.Label(self.root, text="Конвертаций: 0")
        self.stats_label.pack(pady=5)
        
        # Кнопки
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="▶ Тест (Shift+Pause)", 
                  command=self.test_conversion).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🔄 Свернуть в трей", 
                  command=self.minimize_to_tray).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="❌ Выход", 
                  command=self.exit_app).pack(side=tk.LEFT, padx=5)
        
        # Статус
        self.status_var = tk.StringVar(value="Готов. Ожидание нажатия Shift+Pause...")
        ttk.Label(self.root, textvariable=self.status_var, 
                  foreground="gray", wraplength=450).pack(pady=5)
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
    
    def setup_tray_icon(self):
        """Настроить иконку в трее (через меню)"""
        # Создаем меню для трея (через Toplevel)
        self.tray_menu = tk.Menu(self.root, tearoff=0)
        self.tray_menu.add_command(label="LayoutConverter", state=tk.DISABLED, 
                                   font=('Arial', 9, 'bold'))
        self.tray_menu.add_separator()
        self.tray_menu.add_command(label="Показать окно", command=self.show_window)
        self.tray_menu.add_command(label=f"Конвертаций: {self.conversion_count}", 
                                   state=tk.DISABLED)
        self.tray_menu.add_separator()
        self.tray_menu.add_command(label="Выход", command=self.exit_app)
        
        # При минимизации окна показываем сообщение
        self.root.bind("<Unmap>", self.on_minimize)
    
    def on_minimize(self, event=None):
        """При минимизации сворачиваем в трей"""
        if self.root.state() == 'iconic':
            self.minimize_to_tray()
    
    def minimize_to_tray(self):
        """Свернуть в трей (спрятать окно)"""
        self.root.withdraw()
        self.status_var.set("Свернуто в трей. Нажмите Shift+Pause для конвертации.")
    
    def show_window(self):
        """Показать окно"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def setup_hotkey(self):
        """Настроить глобальный hotkey"""
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.add_hotkey('shift+pause', self.auto_convert, suppress=False)
                print("✓ Hotkey Shift+Pause зарегистрирован")
            except Exception as e:
                print(f"✗ Ошибка регистрации hotkey: {e}")
                messagebox.showerror("Ошибка", f"Не удалось зарегистрировать Shift+Pause: {e}")
    
    def auto_convert(self):
        """
        Автоматическая конвертация с сохранением буфера:
        1. Сохраняем текущий буфер
        2. Копируем выделенное (Ctrl+C)
        3. Читаем и конвертируем
        4. Вставляем (Ctrl+V)
        5. Восстанавливаем буфер (если включено)
        """
        try:
            # Сохраняем текущее содержимое буфера
            old_clipboard = ""
            if self.save_clipboard.get():
                try:
                    old_clipboard = pyperclip.paste()
                except:
                    pass
            
            # Копируем выделенный текст
            keyboard.send('ctrl+c')
            time.sleep(0.15)  # Даём время на копирование
            
            # Читаем из буфера
            selected = pyperclip.paste()
            if not selected or selected == old_clipboard:
                return
            
            # Конвертируем
            converted, mode = self.convert_text(selected)
            
            # Проверяем, изменился ли текст
            if converted == selected:
                # Восстанавливаем буфер если не конвертировали
                if self.save_clipboard.get() and old_clipboard:
                    pyperclip.copy(old_clipboard)
                return
            
            # Записываем конвертированный текст
            pyperclip.copy(converted)
            time.sleep(0.05)
            
            # Вставляем
            keyboard.send('ctrl+v')
            time.sleep(0.05)
            
            # Восстанавливаем оригинальный буфер
            if self.save_clipboard.get() and old_clipboard:
                time.sleep(0.1)
                pyperclip.copy(old_clipboard)
            
            # Обновляем статистику
            self.conversion_count += 1
            self.stats_label.config(text=f"Конвертаций: {self.conversion_count}")
            
            # Показываем статус
            mode_text = "RU→EN" if mode == 'ru_to_en' else "EN→RU"
            self.status_var.set(f"✓ Конвертировано ({mode_text}): {len(selected)} символов")
            
            print(f"✓ Конвертация {self.conversion_count}: {mode_text}, {len(selected)} символов")
            
        except Exception as e:
            print(f"✗ Ошибка: {e}")
            self.status_var.set(f"Ошибка конвертации: {e}")
    
    def convert_text(self, text):
        """Конвертировать текст с автоопределением"""
        if not text:
            return text, None
        
        ru_count = sum(1 for c in text if c in RU_LOWER or c in RU_UPPER)
        en_count = sum(1 for c in text if c in EN_LOWER or c in EN_UPPER)
        mode = 'ru_to_en' if ru_count > en_count else 'en_to_ru'
        
        result = []
        for char in text:
            if mode == 'ru_to_en':
                result.append(RU_TO_EN.get(char, char))
            else:
                result.append(EN_TO_RU.get(char, char))
        
        return ''.join(result), mode
    
    def test_conversion(self):
        """Тест конвертации"""
        test_text = "rfrfz-nj f,hfrflf,hf?"  # какая-то абракадабра
        converted, mode = self.convert_text(test_text)
        mode_text = "RU→EN" if mode == 'ru_to_en' else "EN→RU"
        messagebox.showinfo("Тест", f"Исходный: {test_text}\nРезультат: {converted}\nРежим: {mode_text}")
    
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
    app = TrayConverterApp()
    app.run()
