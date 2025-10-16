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
from kivy.uix.anchorlayout import AnchorLayout

# フォントファイルの指定
font_path = os.path.join(os.path.dirname(__file__), "font", "NotoSansJP-VariableFont_wght.ttf")
if os.path.exists(font_path):
    resource_add_path(os.path.dirname(font_path))
    try:
        LabelBase.register(DEFAULT_FONT, font_path)
    except Exception as e:
        print(f"Font registration failed: {e}")
else:
    print(f"Font file not found at {font_path}. Using default font.")


class ListViewApp(App):
    def build(self):
        base = os.path.dirname(__file__)
        products_path = os.path.join(base, 'products.json')

      
        ui_padding = dp(14) 
        row_height = dp(320)  
        card_radius = dp(8)  
        img_size = dp(80)  
        label_color = (0.3, 0.3, 0.3, 1)  
        Window.clearcolor = (0.95, 0.95, 0.95, 1)

        # 商品カード　べーす
        class CardLayout(ButtonBehavior, BoxLayout):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.bind(pos=self._update_rect, size=self._update_rect)
                with self.canvas.before:
                    Color(0.98, 0.98, 0.98, 1)
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

        scroll_view = ScrollView(size_hint=(1, 1))
        container = BoxLayout(orientation='vertical', 
                    size_hint_y=None, 
                    spacing=dp(16),
                    padding=ui_padding)
        container.bind(minimum_height=container.setter('height'))

        self.item_checks = []
        items = json_load.get('items', [])

        # (m: メイン, s: サイド, d: ドリンク)
        mains = [it for it in items if str(it.get('id', '')).startswith('m')]
        sides = [it for it in items if str(it.get('id', '')).startswith('s')]
        drinks = [it for it in items if str(it.get('id', '')).startswith('d')]


        def add_section(title, items_list):
            if not items_list:
                return
            title_lbl = Label(text=title, font_size=sp(20), size_hint_y=None, height=dp(40), color=(0.15,0.15,0.15,1), halign='left', valign='middle')
            title_lbl.bind(size=lambda s, *_: setattr(s, 'text_size', (s.width, s.height)))
            container.add_widget(title_lbl)
            for it in items_list:
                card = CardLayout(orientation='vertical',
                                  size_hint_y=None,
                                  height=row_height,
                                  padding=(dp(12), dp(12), dp(20), dp(12)))
                card.valign = 'middle'

                name_label = Label(text=it.get('name', '名前不明'), font_size=sp(18), color=label_color,
                                   size_hint_y=None, height=dp(36), halign='center', valign='middle')
                name_label.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
                card.add_widget(name_label)

                if 'image' in it:
                    img_container = AnchorLayout(size_hint=(1, None), height=img_size + dp(24), anchor_x='center', anchor_y='center')
                    img = Image(source=os.path.join(base, 'assets', 'images', it['image']), size_hint=(None, None), size=(img_size, img_size), allow_stretch=True, keep_ratio=True)
                    img_container.add_widget(img)
                    card.add_widget(img_container)

                state = {'product': it, 'qty': 0}
                sizes = it.get('sizes')

                if sizes:
                    state['qty_by_size'] = {s.get('name'): 0 for s in sizes}
                    control_width = dp(220)
                    ctrl_spacing = dp(12)
                    controls_row = BoxLayout(orientation='horizontal', size_hint=(None, None), height=dp(96), spacing=ctrl_spacing)
                    controls_row.width = len(sizes) * (control_width + ctrl_spacing) + dp(40)

                    for size in sizes:
                        size_name = size.get('name')
                        ctrl_wrap = AnchorLayout(size_hint=(None, None), size=(control_width, dp(96)), anchor_x='center', anchor_y='center')
                        vbox = BoxLayout(orientation='vertical', size_hint=(None, None), size=(control_width, dp(96)), spacing=dp(6))
                        size_lbl = Label(text=size_name, size_hint=(None, None), size=(control_width, dp(28)), font_size=sp(14), color=label_color, halign='center', valign='middle')
                        size_lbl.bind(size=lambda s, *_: setattr(s, 'text_size', (s.width, s.height)))
                        controls = self.make_qty_controls_for_size(state, size_name)
                        ctrl_anchor = AnchorLayout(size_hint=(1, None), height=dp(56), anchor_x='center', anchor_y='center')
                        ctrl_anchor.add_widget(controls)
                        vbox.add_widget(size_lbl)
                        vbox.add_widget(ctrl_anchor)
                        ctrl_wrap.add_widget(vbox)
                        controls_row.add_widget(ctrl_wrap)

                    controls_row.add_widget(Label(size_hint_x=None, width=dp(40)))

                    controls_scroll = ScrollView(size_hint=(1, None), height=dp(120), do_scroll_x=True, do_scroll_y=False)
                    controls_scroll.scroll_timeout = 240
                    controls_scroll.scroll_distance = 24
                    controls_scroll.add_widget(controls_row)

                    sizes_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(120), spacing=dp(8), padding=(dp(4), 0, dp(4), 0))
                    sizes_row.add_widget(controls_scroll)
                    card.add_widget(sizes_row)
                else:
                    price_label = Label(text=f"¥{it.get('price', 0)}", font_size=sp(16), color=label_color, size_hint_y=None, height=dp(28), halign='center')
                    price_label.bind(size=lambda s, *_: setattr(s, 'text_size', (s.width, s.height)))
                    card.add_widget(price_label)
                    controls = self.make_qty_controls(state)
                    ctrl_anchor = AnchorLayout(size_hint=(1, None), height=dp(64), anchor_x='center')
                    ctrl_anchor.add_widget(controls)
                    card.add_widget(ctrl_anchor)

                container.add_widget(card)
                self.item_checks.append(state)

        add_section('メイン', mains)
        add_section('サイド', sides)
        add_section('ドリンク', drinks)

        # 注文ボタン
        order_btn = Button(
            text='注文する',
            size_hint=(1, None),
            height=dp(56),
            font_size=sp(18),
            background_color=(0.2, 0.7, 0.3, 1),
            background_normal='',
        )
        order_btn.bind(on_release=self.on_order)

        scroll_view.add_widget(container)
        root_layout = BoxLayout(orientation='vertical')
        root_layout.add_widget(scroll_view)

        # フッターにこてい
        footer = BoxLayout(size_hint_y=None, height=dp(80), padding=(dp(8), dp(8), dp(8), dp(8)))
        btn_anchor = AnchorLayout(size_hint=(1, 1), anchor_x='center', anchor_y='center')
        btn_anchor.add_widget(order_btn)
        footer.add_widget(btn_anchor)
        root_layout.add_widget(footer)

        return root_layout

    def make_qty_controls(self, state):
        label_color = (0.3, 0.3, 0.3, 1)
        controls = BoxLayout(orientation='horizontal', size_hint=(None, None), width=dp(180), height=dp(48), spacing=dp(8))

        btn_minus = Button(text='-', size_hint=(None, None), size=(dp(56), dp(48)))
        qty_label = Label(text='0', size_hint=(None, None), size=(dp(64), dp(48)), color=label_color)
        btn_plus = Button(text='+', size_hint=(None, None), size=(dp(56), dp(48)))

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
        controls = BoxLayout(orientation='horizontal', size_hint=(None, None), width=dp(220), height=dp(48), spacing=dp(8))

        btn_minus = Button(text='-', size_hint=(None, None), size=(dp(56), dp(48)), background_color=(0.9, 0.9, 0.9, 1))
        qty_label = Label(text='0', size_hint=(None, None), size=(dp(64), dp(48)), color=label_color)
        btn_plus = Button(text='+', size_hint=(None, None), size=(dp(56), dp(48)), background_color=(0.9, 0.9, 0.9, 1))

        def update_qty(change):
            state['qty_by_size'][size_name] = max(0, state['qty_by_size'].get(size_name, 0) + change)
            qty_label.text = str(state['qty_by_size'][size_name])

        btn_minus.bind(on_release=lambda _: update_qty(-1))
        btn_plus.bind(on_release=lambda _: update_qty(1))

        controls.add_widget(Label(size_hint_x=None, width=dp(6)))
        controls.add_widget(btn_minus)
        controls.add_widget(qty_label)
        controls.add_widget(btn_plus)
        controls.add_widget(Label(size_hint_x=None, width=dp(6)))

        return controls

    def on_order(self, instance):
        lines = []
        total = 0
        for st in self.item_checks:
            p = st['product']
            if 'qty_by_size' in st:  
                for size, qty in st['qty_by_size'].items():
                    if qty > 0:
                        size_price = next((s.get('price') for s in p.get('sizes', [])
                                         if s.get('name') == size), None)
                        price = size_price if size_price is not None else p.get('price', 0)
                        lines.append(f"{p.get('name')} ({size}) x{qty} - ¥{price * qty}")
                        total += price * qty
            else: 
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