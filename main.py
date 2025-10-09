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
from kivy.metrics import dp, sp
from kivy.utils import platform

# フォントファイルの指定
font_path = os.path.join(os.path.dirname(__file__), "font", "NotoSansJP-VariableFont_wght.ttf")
# ensure font is bundled/exists before registering on platforms like Android
if os.path.exists(font_path):
    resource_add_path(os.path.dirname(font_path))
    try:
        LabelBase.register(DEFAULT_FONT, font_path)
    except Exception as e:
        # fallback: continue without custom font
        print(f"Font registration failed: {e}")
else:
    print(f"Font file not found at {font_path}. Using default font.")


class ListViewApp(App):
    def build(self):
        base = os.path.dirname(__file__)
        products_path = os.path.join(base, 'products.json')

        # UI 基本値（dp/sp で指定）
        ui_padding = dp(12)
        row_height = dp(72)
        chk_size = dp(48)
        img_size = dp(64)
        spinner_width = dp(110)
        spinner_height = dp(40)
        label_large = sp(18)
        label_small = sp(16)
        order_btn_height = dp(56)

        # json読み込んでしまおう（存在しない場合は分かりやすく表示してクラッシュ回避）
        try:
            with open(products_path, 'r', encoding='utf-8') as f:
                json_load = json.load(f)
        except Exception as e:
            # 建設的な挙動: 空の商品リストを使い、エラーメッセージを表示してクラッシュ回避
            json_load = {'items': []}
            root = ScrollView(size_hint=(1, 1))
            container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=ui_padding, padding=(ui_padding, ui_padding, ui_padding, ui_padding))
            container.bind(minimum_height=container.setter('height'))
            container.add_widget(Label(text=f"products.json を読み込めませんでした: {e}", font_size=label_large))
            root.add_widget(container)
            return root

        root = ScrollView(size_hint=(1, 1))

        # container の padding は左, 上, 右, 下 の順で指定
        container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=ui_padding, padding=(ui_padding, ui_padding, ui_padding, ui_padding))
        container.bind(minimum_height=container.setter('height'))

        # 汎用アイテム一覧（カテゴリを廃止）
        self.item_checks = []  # list of dict {check, spinner(optional), product}
        items = json_load.get('items', [])
        for it in items:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=row_height, spacing=ui_padding)
            # CheckBox をタップしやすくする（固定サイズ）
            chk = CheckBox(size_hint=(None, None), size=(chk_size, chk_size))
            chk.product = it
            # 中央揃え
            chk_container = BoxLayout(size_hint=(None, 1), width=chk_size, padding=(0, (row_height - chk_size) / 2, 0, (row_height - chk_size) / 2))
            chk_container.add_widget(chk)
            row.add_widget(chk_container)

            img_file = it.get('image') or ''
            if img_file:
                img_path = os.path.join(base, 'assets', 'images', img_file)
                if os.path.exists(img_path):
                    img_widget = Image(source=img_path, size_hint=(None, None), size=(img_size, img_size), allow_stretch=True, keep_ratio=True)
                    # 画像を中央寄せするコンテナ
                    img_container = BoxLayout(size_hint=(None, 1), width=img_size + ui_padding, padding=(0, (row_height - img_size) / 2, 0, (row_height - img_size) / 2))
                    img_container.add_widget(img_widget)
                    row.add_widget(img_container)

            # 名前とベース価格
            text_box = BoxLayout(orientation='vertical')
            text_box.add_widget(Label(text=it.get('name', '名前不明'), font_size=label_large))
            text_box.add_widget(Label(text=f"{it.get('price')}¥", font_size=label_small))
            row.add_widget(text_box)

            spinner = None
            sizes = it.get('sizes') or []
            if sizes:
                size_names = [s.get('name') for s in sizes]
                default = size_names[1] if len(size_names) >= 2 else size_names[0]
                spinner = Spinner(text=default, values=size_names, size_hint=(None, None), size=(spinner_width, spinner_height))
                # 垂直中央揃えのためのスペースを確保
                spinner_container = BoxLayout(size_hint=(None, 1), width=spinner_width + ui_padding, padding=(0, (row_height - spinner_height) / 2, 0, (row_height - spinner_height) / 2))
                spinner_container.add_widget(spinner)
                row.add_widget(spinner_container)

            container.add_widget(row)
            self.item_checks.append({'check': chk, 'spinner': spinner, 'product': it})

        # 注文ボタン
        order_btn = Button(text='注文する', size_hint_y=None, height=order_btn_height, font_size=label_large)
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