from kivy.app import App
from kivy.uix.label import Label
# フォントの記述
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path
import os

# フォントファイルの指定
font_path = os.path.join(os.path.dirname(__file__), "font", "NotoSansJP-VariableFont_wght.ttf")
resource_add_path(os.path.dirname(font_path))
LabelBase.register(DEFAULT_FONT, font_path)

class MyApp(App):
    def build(self):
        return Label(text="こんにちは！!")

if __name__ == "__main__":
    MyApp().run()