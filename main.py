from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path
import os
import json
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.popup import Popup

# フォントファイルの指定
font_path = os.path.join(os.path.dirname(__file__), "font", "NotoSansJP-VariableFont_wght.ttf")
resource_add_path(os.path.dirname(font_path))
LabelBase.register(DEFAULT_FONT, font_path)


class ListViewApp(App):
    def build(self):
        base = os.path.dirname(__file__)
        products_path = os.path.join(base, 'products.json')

        # json読み込んでしまおう
        with open(products_path, 'r', encoding='utf-8') as f:
            json_load = json.load(f)

        root = ScrollView(size_hint=(1, 1))

        container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=8)
        container.bind(minimum_height=container.setter('height'))

        # 汎用アイテム一覧（カテゴリを廃止）
        self.item_checks = []  # list of dict {check, spinner(optional), product}
        items = json_load.get('items', [])
        for it in items:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=64, spacing=8)
            chk = CheckBox(size_hint=(None, 1), width=40)
            chk.product = it
            row.add_widget(chk)

            img_file = it.get('image') or ''
            if img_file:
                img_path = os.path.join(base, 'assets', 'images', img_file)
                if os.path.exists(img_path):
                    img_widget = Image(source=img_path, size_hint=(None, 1), width=64, allow_stretch=True, keep_ratio=True)
                    row.add_widget(img_widget)

            # 名前とベース価格
            text_box = BoxLayout(orientation='vertical')
            text_box.add_widget(Label(text=it.get('name', '名前不明')))
            text_box.add_widget(Label(text=f"{it.get('price')}¥"))
            row.add_widget(text_box)

            spinner = None
            sizes = it.get('sizes') or []
            if sizes:
                size_names = [s.get('name') for s in sizes]
                default = size_names[1] if len(size_names) >= 2 else size_names[0]
                spinner = Spinner(text=default, values=size_names, size_hint=(None, 1), width=80)
                row.add_widget(spinner)

            container.add_widget(row)
            self.item_checks.append({'check': chk, 'spinner': spinner, 'product': it})

        # 注文ボタン
        order_btn = Button(text='注文する', size_hint_y=None, height=48)
        order_btn.bind(on_release=self.on_order)
        container.add_widget(order_btn)

        root.add_widget(container)
        return root

    def on_order(self, instance):
        lines = []
        total = 0

        selected = [w for w in self.item_checks if w['check'].active]
        if not selected:
            lines.append('選択された商品がありません')
        else:
            for w in selected:
                p = w['product']
                if w['spinner']:
                    sz_name = w['spinner'].text
                    # find size price
                    size_price = next((s.get('price') for s in p.get('sizes', []) if s.get('name') == sz_name), None)
                    price = size_price if size_price is not None else p.get('price', 0)
                    lines.append(f"{p.get('name')} ({sz_name}) - {price}¥")
                else:
                    price = p.get('price', 0)
                    lines.append(f"{p.get('name')} - {price}¥")
                total += int(price)

        lines.append(f"\n合計: {total}¥")
        popup = Popup(title='ご注文の確認', content=Label(text='\n'.join(lines)), size_hint=(0.8, 0.6))
        popup.open()

if __name__ == '__main__':
    ListViewApp().run()