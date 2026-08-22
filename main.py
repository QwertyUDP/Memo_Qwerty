# main.py - Мемо Машинки для Android (Kivy)
# Для сборки APK используйте Buildozer
# Установка: pip install kivy

import kivy
kivy.require('2.2.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
import random

# Устанавливаем размер окна для мобильных устройств
Window.size = (360, 640)

# Эмодзи машинок (достаточно для 24 пар)
CAR_EMOJIS = [
    "🚗", "🚕", "🚙", "🚌", "🚎", "🏎️", "🚓", "🚑", "🚒", "🚐",
    "🚛", "🚜", "🏍️", "🛵", "🚲", "🚨", "🚔", "🚍", "🚘", "🚖",
    "🚠", "🚟", "🚃", "🚋"
]

# 12 уровней: количество пар на каждом
LEVEL_CONFIG = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]


class CardButton(Button):
    """Кнопка-карточка с состоянием."""
    def __init__(self, card_id, emoji, **kwargs):
        super().__init__(**kwargs)
        self.card_id = card_id
        self.emoji = emoji
        self.matched = False
        self.flipped = False
        self.text = "?"
        self.font_size = 36
        self.background_color = (0.18, 0.27, 0.36, 1)
        self.color = (1, 1, 1, 1)
        self.border = (0, 0, 0, 0)
        self.size_hint = (1, 1)
        
    def flip_card(self):
        """Переворачивает карточку."""
        if not self.matched:
            self.flipped = not self.flipped
            self.text = self.emoji if self.flipped else "?"
            self.background_color = (0.9, 0.94, 0.98, 1) if self.flipped else (0.18, 0.27, 0.36, 1)
            self.color = (0.1, 0.1, 0.1, 1) if self.flipped else (1, 1, 1, 1)
    
    def set_matched(self):
        """Отмечает карту как найденную пару."""
        self.matched = True
        self.flipped = True
        self.text = self.emoji
        self.background_color = (0.11, 0.48, 0.32, 1)
        self.color = (1, 1, 1, 1)
        self.disabled = True


class MemoGame(BoxLayout):
    """Основной класс игры."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # Переменные игры
        self.current_level = 0
        self.cards = []
        self.first_card = None
        self.second_card = None
        self.moves = 0
        self.matched_pairs = 0
        self.total_pairs = 0
        self.is_waiting = False
        self.game_complete = False
        
        # Создаем интерфейс
        self.build_ui()
        
        # Запускаем первый уровень
        self.start_level()
    
    def build_ui(self):
        """Создает пользовательский интерфейс."""
        # Верхняя панель
        self.top_panel = BoxLayout(
            size_hint=(1, 0.12),
            spacing=10,
            padding=5
        )
        
        self.level_label = Label(
            text="Уровень 1",
            font_size=18,
            color=(0.9, 0.9, 0.9, 1),
            size_hint=(0.3, 1)
        )
        
        self.moves_label = Label(
            text="Ходы: 0",
            font_size=18,
            color=(0.9, 0.9, 0.9, 1),
            size_hint=(0.25, 1)
        )
        
        self.pairs_label = Label(
            text="Пары: 0/0",
            font_size=18,
            color=(0.9, 0.9, 0.9, 1),
            size_hint=(0.25, 1)
        )
        
        self.top_panel.add_widget(self.level_label)
        self.top_panel.add_widget(self.moves_label)
        self.top_panel.add_widget(self.pairs_label)
        self.add_widget(self.top_panel)
        
        # Сетка для карточек
        self.grid = GridLayout(
            cols=4,
            spacing=8,
            padding=5,
            size_hint=(1, 0.7)
        )
        self.add_widget(self.grid)
        
        # Информационное сообщение
        self.message_label = Label(
            text="🚗 Найди пары машинок!",
            font_size=20,
            color=(0.9, 0.9, 0.9, 1),
            size_hint=(1, 0.08),
            halign='center',
            valign='middle'
        )
        self.message_label.bind(size=self.message_label.setter('text_size'))
        self.add_widget(self.message_label)
        
        # Нижняя панель с кнопками
        self.bottom_panel = BoxLayout(
            size_hint=(1, 0.1),
            spacing=10,
            padding=5
        )
        
        self.reset_btn = Button(
            text="🔄 Новая",
            font_size=16,
            background_color=(0.2, 0.35, 0.5, 1),
            color=(1, 1, 1, 1)
        )
        self.reset_btn.bind(on_press=self.reset_level)
        
        self.next_btn = Button(
            text="➡ След.",
            font_size=16,
            background_color=(0.2, 0.35, 0.5, 1),
            color=(1, 1, 1, 1),
            disabled=True
        )
        self.next_btn.bind(on_press=self.next_level)
        
        self.bottom_panel.add_widget(self.reset_btn)
        self.bottom_panel.add_widget(self.next_btn)
        self.add_widget(self.bottom_panel)
    
    def start_level(self):
        """Начинает новый уровень."""
        # Очищаем сетку
        self.grid.clear_widgets()
        
        # Сбрасываем состояние
        self.first_card = None
        self.second_card = None
        self.is_waiting = False
        self.game_complete = False
        
        # Получаем количество пар для текущего уровня
        pairs = LEVEL_CONFIG[self.current_level]
        self.total_pairs = pairs
        self.moves = 0
        self.matched_pairs = 0
        
        # Создаем колоду карт
        used_emojis = CAR_EMOJIS[:pairs]
        card_data = []
        for emoji in used_emojis:
            card_data.append(emoji)
            card_data.append(emoji)
        random.shuffle(card_data)
        
        # Создаем кнопки-карточки
        self.cards = []
        cols = 4 if pairs * 2 <= 16 else 6
        self.grid.cols = cols
        
        for i, emoji in enumerate(card_data):
            card = CardButton(i, emoji)
            card.bind(on_press=self.on_card_press)
            self.grid.add_widget(card)
            self.cards.append(card)
        
        # Обновляем информацию
        self.update_info()
        self.message_label.text = "🚗 Найди пары машинок!"
        self.next_btn.disabled = True
    
    def on_card_press(self, instance):
        """Обработка нажатия на карточку."""
        if self.is_waiting or self.game_complete:
            return
        
        if instance.matched or instance.flipped:
            return
        
        # Переворачиваем карту
        instance.flip_card()
        
        if self.first_card is None:
            self.first_card = instance
        else:
            self.second_card = instance
            self.moves += 1
            self.update_info()
            self.check_match()
    
    def check_match(self):
        """Проверяет совпадение двух открытых карт."""
        if self.first_card.emoji == self.second_card.emoji:
            # Совпадение!
            self.first_card.set_matched()
            self.second_card.set_matched()
            self.matched_pairs += 1
            self.update_info()
            
            self.first_card = None
            self.second_card = None
            
            # Проверяем победу
            if self.matched_pairs == self.total_pairs:
                self.game_complete = True
                if self.current_level == len(LEVEL_CONFIG) - 1:
                    self.message_label.text = "🏆 ПОБЕДА! Все уровни пройдены! 🏆"
                    self.next_btn.disabled = True
                else:
                    self.message_label.text = "🎉 Уровень пройден! 🎉"
                    self.next_btn.disabled = False
        else:
            # Не совпало - переворачиваем обратно через секунду
            self.is_waiting = True
            self.message_label.text = "❌ Не совпало!"
            Clock.schedule_once(self.flip_back, 0.8)
    
    def flip_back(self, dt):
        """Переворачивает обратно несовпавшие карты."""
        if self.first_card and self.second_card:
            self.first_card.flip_card()
            self.second_card.flip_card()
        
        self.first_card = None
        self.second_card = None
        self.is_waiting = False
        
        if not self.game_complete:
            self.message_label.text = "🚗 Найди пары машинок!"
    
    def update_info(self):
        """Обновляет информацию на панели."""
        self.level_label.text = f"Уровень {self.current_level + 1}"
        self.moves_label.text = f"Ходы: {self.moves}"
        self.pairs_label.text = f"Пары: {self.matched_pairs}/{self.total_pairs}"
    
    def reset_level(self, instance=None):
        """Перезапускает текущий уровень."""
        self.start_level()
        self.next_btn.disabled = True
    
    def next_level(self, instance=None):
        """Переходит на следующий уровень."""
        if self.current_level < len(LEVEL_CONFIG) - 1:
            self.current_level += 1
            self.start_level()
            self.next_btn.disabled = True


class MemoCarsApp(App):
    """Главное приложение."""
    def build(self):
        self.title = 'Мемо Машинки'
        return MemoGame()


if __name__ == '__main__':
    MemoCarsApp().run()
