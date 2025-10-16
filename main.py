from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path
import os
import json
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout

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

        # UI基本値の更新
        ui_padding = dp(12)  # パディングを少し大きく
        row_height = dp(120)  # 行の高さを増やして余裕を持たせる
        card_radius = dp(8)  # カードの角丸の半径
        img_size = dp(80)  # 画像サイズを大きく
        label_color = (0.3, 0.3, 0.3, 1)  # ラベルの色を濃いグレーに

        # 背景色をより明るく設定
        Window.clearcolor = (0.95, 0.95, 0.95, 1)

        # 商品カードのベースクラス
        class CardLayout(ButtonBehavior, BoxLayout):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.bind(pos=self._update_rect, size=self._update_rect)
                with self.canvas.before:
                    Color(0.98, 0.98, 0.98, 1)  # カードの背景色
                    self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[card_radius])

            def _update_rect(self, instance, value):
                self.rect.pos = instance.pos
                self.rect.size = instance.size

        try:
            with open(products_path, 'r', encoding='utf-8') as f:
                json_load = json.load(f)
        except Exception as e:
            json_load = {'items': []}
            root = ScrollView(size_hint=(1, 1))
            container = BoxLayout(orientation='vertical', 
                                size_hint_y=None, 
                                spacing=ui_padding)
            container.bind(minimum_height=container.setter('height'))
            container.add_widget(Label(text=f"products.json を読み込めませんでした: {e}", 
                                     font_size=sp(16)))
            root.add_widget(container)
            return root

        root = ScrollView(size_hint=(1, 1))
        container = BoxLayout(orientation='vertical', 
                            size_hint_y=None, 
                            spacing=dp(16),
                            padding=ui_padding)
        container.bind(minimum_height=container.setter('height'))

        self.item_checks = []
        items = json_load.get('items', [])
        
        for it in items:
            # カード形式のレイアウト
            card = CardLayout(orientation='vertical', 
                            size_hint_y=None,
                            height=row_height,
                            padding=dp(12))

            # 商品情報の行
            row = BoxLayout(orientation='horizontal', 
                          spacing=ui_padding,
                          size_hint_y=None,
                          height=dp(80))

            # 画像の配置改善
            if 'image' in it:
                img_container = BoxLayout(size_hint=(None, 1), 
                                       width=img_size + ui_padding)
                img = Image(source=os.path.join(base, 'assets', 'images', it['image']),
                          size_hint=(None, None),
                          size=(img_size, img_size))
                img_container.add_widget(img)
                row.add_widget(img_container)

            # 商品情報コンテナ
            info_container = BoxLayout(orientation='vertical',
                                    padding=(0, dp(4)))
            name_label = Label(text=it.get('name', '名前不明'),
                             font_size=sp(18),
                             color=label_color,
                             size_hint_y=None,
                             height=dp(30),
                             halign='left')
            name_label.bind(size=lambda s,w: setattr(s, 'text_size', w))
            
            price_label = Label(text=f"¥{it.get('price', 0)}" if it.get('price') is not None else "",
                   font_size=sp(16),
                   color=label_color)
            
            info_container.add_widget(name_label)
            info_container.add_widget(price_label)
            row.add_widget(info_container)

            card.add_widget(row)

            # サイズ選択UI
            state = {'product': it, 'qty': 0}
            sizes = it.get('sizes')
            
            if sizes:
                state['qty_by_size'] = {s.get('name'): 0 for s in sizes}
                sizes_container = BoxLayout(orientation='horizontal',
                                         spacing=dp(36),
                                         size_hint_y=None,
                                         height=dp(40))
                
                for size in sizes:
                    size_name = size.get('name')
                    size_box = BoxLayout(orientation='vertical',
                    spacing=dp(8),
                    size_hint_x=None,
                    width=dp(180),  # 120から180に増やす
                    padding=(dp(8), dp(4)))  # 左右のパディングも少し増やす

                    
                    size_label = Label(text=f"{size_name}\n¥{size.get('price')}",
                                     color=label_color,
                                     font_size=sp(14),
                                     size_hint_y=None,
                                     height=dp(40))
                    
                    controls = self.make_qty_controls_for_size(state, size_name)
                    size_box.add_widget(size_label)
                    size_box.add_widget(controls)
                    sizes_container.add_widget(size_box)
                
                card.add_widget(sizes_container)
            else:
                controls = self.make_qty_controls(state)
                card.add_widget(controls)

            container.add_widget(card)
            self.item_checks.append(state)

        # 注文ボタンのスタイル改善
        order_btn = Button(
            text='注文する',
            size_hint_y=None,
            height=dp(56),
            font_size=sp(18),
            background_color=(0.2, 0.7, 0.3, 1),
            background_normal='',
        )
        order_btn.bind(on_release=self.on_order)
        
        # ボタンを下部に固定
        button_container = FloatLayout(size_hint_y=None, height=dp(80))
        button_container.add_widget(order_btn)
        container.add_widget(button_container)

        root.add_widget(container)
        return root

    def make_qty_controls(self, state):
        label_color = (0.3, 0.3, 0.3, 1)
        # 数量コントロール作成用のヘルパーメソッド
        controls = BoxLayout(orientation='horizontal',
                           size_hint=(None, None),
                           width=dp(120),
                           height=dp(40))
        
        btn_minus = Button(text='-',
                          size_hint=(None, None),
                          size=(dp(40), dp(40)))
        qty_label = Label(text='0',
                         size_hint=(None, None),
                         size=(dp(40), dp(40)),
                         color=label_color)
        btn_plus = Button(text='+',
                         size_hint=(None, None),
                         size=(dp(40), dp(40)))
        
        def update_qty(change):
            state['qty'] = max(0, state.get('qty', 0) + change)
            qty_label.text = str(state['qty'])
        
        btn_minus.bind(on_release=lambda _: update_qty(-1))
        btn_plus.bind(on_release=lambda _: update_qty(1))
        
        controls.add_widget(btn_minus)
        controls.add_widget(qty_label)
        controls.add_widget(btn_plus)
        
        return controls

    def make_qty_controls_for_size(self, state, size_name):
        label_color = (0.3, 0.3, 0.3, 1)
        # コントロールの全体幅を調整
        controls = BoxLayout(orientation='horizontal',
                    size_hint=(None, None),
                    width=dp(160),  # 10から160に増やす
                    height=dp(40),
                    spacing=dp(15))  # ボタン間の間隔を10から15に増やす
    
    # ボタンのスタイルを改善
        btn_minus = Button(text='-',
                      size_hint=(None, None),
                      size=(dp(40), dp(40)),
                      background_color=(0.9, 0.9, 0.9, 1))  # 薄いグレー
    
        qty_label = Label(text='0',
                     size_hint=(None, None),
                     size=(dp(40), dp(40)),
                     color=label_color)
    
        btn_plus = Button(text='+',
                     size_hint=(None, None),
                     size=(dp(40), dp(40)),
                     background_color=(0.9, 0.9, 0.9, 1))  # 薄いグレー
        
        def update_qty(change):
            state['qty_by_size'][size_name] = max(0, state['qty_by_size'].get(size_name, 0) + change)
            qty_label.text = str(state['qty_by_size'][size_name])
        
        btn_minus.bind(on_release=lambda _: update_qty(-1))
        btn_plus.bind(on_release=lambda _: update_qty(1))
        
        controls.add_widget(Label(size_hint_x=None, width=dp(5)))  # 左側の余白
        controls.add_widget(btn_minus)
        
        controls.add_widget(qty_label)
        
        controls.add_widget(btn_plus)
        controls.add_widget(Label(size_hint_x=None, width=dp(5)))  # 右側の余白
    
        return controls

    def on_order(self, instance):
        lines = []
        total = 0
        for st in self.item_checks:
            p = st['product']
            if 'qty_by_size' in st:  # サイズ別商品の場合
                for size, qty in st['qty_by_size'].items():
                    if qty > 0:
                        size_price = next((s.get('price') for s in p.get('sizes', [])
                                         if s.get('name') == size), None)
                        price = size_price if size_price is not None else p.get('price', 0)
                        lines.append(f"{p.get('name')} ({size}) x{qty} - ¥{price * qty}")
                        total += price * qty
            else:  # 通常商品の場合
                qty = st.get('qty', 0)
                if qty > 0:
                    price = p.get('price', 0)
                    lines.append(f"{p.get('name')} x{qty} - ¥{price * qty}")
                    total += price * qty

        if not lines:
            lines.append('選択された商品がありません')
        
        lines.append(f"\n合計: ¥{total}")
        popup = Popup(title='ご注文の確認',
                     content=Label(text='\n'.join(lines),
                                 color=(1,1,1,1),
                                 font_size=sp(16)),
                     size_hint=(0.8, 0.6),
                     background='atlas://data/images/defaulttheme/button')
        popup.open()

if __name__ == '__main__':
    ListViewApp().run()