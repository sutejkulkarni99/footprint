from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.scrollview import ScrollView
import time

# Amphibian Color Palette
BACKGROUND = (0.11, 0.13, 0.16, 1)  # Dark slate
PRIMARY = (0.35, 0.71, 0.67, 1)     # Aquatic green
SECONDARY = (0.47, 0.53, 0.6, 1)    # Stone gray
ACCENT = (0.91, 0.3, 0.24, 1)       # Coral red  # Added comment symbol
TEXT_WHITE = (1, 1, 1, 1)

class ModernButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = TEXT_WHITE
        self.font_size = 24
        self.bold = True
        self.size_hint = (1, None)
        self.height = 60
        self.bind(pos=self.update_rect, size=self.update_rect)
        with self.canvas.before:
            Color(rgba=PRIMARY)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[15])

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class StopwatchApp(App):
    def build(self):
        self.elapsed_time = 0
        self.running = False
        self.laps = []
        self.clock_event = None  # To track the clock event

        # Main layout
        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=15)

        # Timer display
        self.timer_label = Label(
            text="00:00:00.000",
            font_size=64,
            color=TEXT_WHITE,
            bold=True,
            size_hint=(1, 0.4)
        )

        # Button container
        button_layout = BoxLayout(orientation="vertical", size_hint=(1, 0.4), spacing=10)
        
        # Buttons
        self.start_button = ModernButton(text="Start")
        self.start_button.rect.rgba = PRIMARY
        self.stop_button = ModernButton(text="Stop")
        self.stop_button.rect.rgba = ACCENT
        self.lap_button = ModernButton(text="Lap")
        self.lap_button.rect.rgba = SECONDARY
        self.reset_button = ModernButton(text="Reset")
        self.reset_button.rect.rgba = SECONDARY

        # Bind buttons
        self.start_button.bind(on_press=self.start_stopwatch)
        self.stop_button.bind(on_press=self.stop_stopwatch)
        self.lap_button.bind(on_press=self.record_lap)
        self.reset_button.bind(on_press=self.reset_stopwatch)

        # Lap history
        self.scroll_view = ScrollView(size_hint=(1, 0.4))
        self.lap_container = BoxLayout(orientation="vertical", size_hint_y=None)
        self.lap_container.bind(minimum_height=self.lap_container.setter('height'))
        self.scroll_view.add_widget(self.lap_container)

        # Assemble UI
        button_layout.add_widget(self.start_button)
        button_layout.add_widget(self.stop_button)
        button_layout.add_widget(self.lap_button)
        button_layout.add_widget(self.reset_button)
        
        main_layout.add_widget(self.timer_label)
        main_layout.add_widget(self.scroll_view)
        main_layout.add_widget(button_layout)

        Window.clearcolor = BACKGROUND
        return main_layout

    def start_stopwatch(self, instance):
        if not self.running:
            self.running = True
            self.start_time = time.time() - self.elapsed_time
            self.clock_event = Clock.schedule_interval(self.update, 0.01)

    def stop_stopwatch(self, instance):
        if self.running:
            self.running = False
            Clock.unschedule(self.clock_event)

    def reset_stopwatch(self, instance):
        self.running = False
        self.elapsed_time = 0
        self.timer_label.text = "00:00:00.000"
        self.laps = []
        self.lap_container.clear_widgets()
        if self.clock_event:
            Clock.unschedule(self.clock_event)

    def record_lap(self, instance):
        if self.running:
            lap_time = self.timer_label.text
            self.laps.append(lap_time)
            lap_label = Label(
                text=f"Lap {len(self.laps)}: {lap_time}",
                color=TEXT_WHITE,
                font_size=20,
                size_hint_y=None,
                height=40
            )
            self.lap_container.add_widget(lap_label)

    def update(self, dt):
        self.elapsed_time = time.time() - self.start_time
        hours, remainder = divmod(self.elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        self.timer_label.text = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}.{milliseconds:03}"

    def on_stop(self):
        # Force stop the clock when closing
        if self.clock_event:
            Clock.unschedule(self.clock_event)

if __name__ == "__main__":
    StopwatchApp().run()