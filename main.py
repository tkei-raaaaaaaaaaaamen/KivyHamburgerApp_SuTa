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
from kivy.core.window import Window

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
        ui_padding = dp(10)
        row_height = dp(64)
        chk_size = dp(40)
        img_size = dp(56)
        spinner_width = dp(96)
        spinner_compact_width = dp(64)
        spinner_height = dp(34)
        label_large = sp(16)
        label_small = sp(14)
        order_btn_height = dp(44)
        label_color = (0, 0, 0, 1)

        # 背景色を明るく設定（デフォルトの黒っぽさを改善）
        try:
            Window.clearcolor = (0.65, 0.65, 0.65, 1)
        except Exception:
            pass

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

            # 左の余白スペースを削除して項目を左寄せする（以前は spacer を置いていた）

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
            name_label = Label(text=it.get('name', '名前不明'), font_size=label_large, color=label_color)
            # 価格ラベルはスピナーの選択に応じて動的に更新する
            # 初期表示はベース価格。ドリンクの場合は後で変更する。
            initial_price = it.get('price', 0)
            price_label = Label(text=f"{initial_price}¥", font_size=label_small, color=label_color)
            text_box.add_widget(name_label)
            text_box.add_widget(price_label)
            row.add_widget(text_box)

            spinner = None
            sizes = it.get('sizes') or []

            # helper: 数量ステッパーを作る（state は {'product','qty','spinner'} の dict）
            def make_qty_controls(state):
                q_size = dp(28)
                # 初期 qty は state['qty']（0）
                qty_label = Label(text=str(state.get('qty', 0)), size_hint=(None, None), size=(q_size, q_size), font_size=label_small, halign='center', valign='middle', color=label_color)
                # ensure text is centered
                qty_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
                btn_minus = Button(text='-', size_hint=(None, None), size=(q_size, q_size))
                btn_plus = Button(text='+', size_hint=(None, None), size=(q_size, q_size))

                def dec(_):
                    if state.get('qty', 0) > 0:
                        state['qty'] = max(0, state.get('qty', 0) - 1)
                        qty_label.text = str(state['qty'])

                def inc(_):
                    state['qty'] = state.get('qty', 0) + 1
                    qty_label.text = str(state['qty'])

                btn_minus.bind(on_release=dec)
                btn_plus.bind(on_release=inc)

                qty_container = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=q_size * 3 + ui_padding, padding=(0, (row_height - q_size) / 2, 0, (row_height - q_size) / 2))
                qty_container.add_widget(btn_minus)
                qty_container.add_widget(qty_label)
                qty_container.add_widget(btn_plus)
                return qty_container

            # stateオブジェクトを作る（チェックボックス廃止に伴い qty=0 をデフォルトに）
            state = {'product': it, 'qty': 0, 'spinner': None}

            if sizes:
                size_names = [s.get('name') for s in sizes]
                default = size_names[1] if len(size_names) >= 2 else size_names[0]
                # ドリンクなどはコンパクトに表示：スピナーと個数を横並びにして重なりを防止
                spinner = Spinner(text=default, values=size_names, size_hint=(None, None), size=(spinner_compact_width, spinner_height), font_size=label_small, color=label_color)
                state['spinner'] = spinner
                qty_controls = make_qty_controls(state)
                # 横並びコンテナ。高さを固定して中身を AnchorLayout で中央揃えする
                total_width = spinner_compact_width + (dp(28) * 3 + ui_padding)
                spinner_container = BoxLayout(orientation='horizontal', size_hint=(None, None), height=row_height, width=total_width, spacing=ui_padding)
                # spinner を縦中央に配置するための AnchorLayout
                from kivy.uix.anchorlayout import AnchorLayout
                spinner_anchor = AnchorLayout(size_hint=(None, None), size=(spinner_compact_width, row_height), anchor_x='center', anchor_y='center')
                spinner_anchor.add_widget(spinner)
                qty_anchor = AnchorLayout(size_hint=(None, None), size=(dp(28) * 3 + ui_padding, row_height), anchor_x='center', anchor_y='center')
                qty_anchor.add_widget(qty_controls)
                spinner_container.add_widget(spinner_anchor)
                spinner_container.add_widget(qty_anchor)
                row.add_widget(spinner_container)
                # スピナーの選択が変わったら価格ラベルを更新
                def _update_price_label(inst, value, price_lbl=price_label, prod=it):
                    # value はサイズ名。サイズに対応する価格を探す
                    size_price = next((s.get('price') for s in prod.get('sizes', []) if s.get('name') == value), None)
                    new_price = size_price if size_price is not None else prod.get('price', 0)
                    price_lbl.text = f"{new_price}¥"

                spinner.bind(text=_update_price_label)
                # 初期反映（spinner の初期値に基づき価格表示を更新）
                _update_price_label(spinner, spinner.text)
            else:
                # サイズ選択がないアイテムは右端に数量コントロールを置く
                qty_controls = make_qty_controls(state)
                # 非ドリンクでも数量コントロールは縦中央に揃える
                from kivy.uix.anchorlayout import AnchorLayout
                qty_anchor = AnchorLayout(size_hint=(None, None), size=(dp(28) * 3 + ui_padding, row_height), anchor_x='center', anchor_y='center')
                qty_anchor.add_widget(qty_controls)
                row.add_widget(qty_anchor)

            container.add_widget(row)
            # self.item_checks は state dict のリストにする
            self.item_checks.append(state)

        # 注文ボタン
        order_btn = Button(text='注文する', size_hint_y=None, height=order_btn_height, font_size=label_large)
        order_btn.bind(on_release=self.on_order)
        container.add_widget(order_btn)

        root.add_widget(container)
        return root

    def on_order(self, instance):
        lines = []
        total = 0
        # 選択は qty > 0 のアイテム
        selected = [st for st in self.item_checks if st.get('qty', 0) > 0]
        if not selected:
            lines.append('選択された商品がありません')
        else:
            for st in selected:
                p = st['product']
                qty = int(st.get('qty', 0))
                if st.get('spinner'):
                    sz_name = st['spinner'].text
                    size_price = next((s.get('price') for s in p.get('sizes', []) if s.get('name') == sz_name), None)
                    price = size_price if size_price is not None else p.get('price', 0)
                    lines.append(f"{p.get('name')} ({sz_name}) x{qty} - ¥{price * qty}")
                else:
                    price = p.get('price', 0)
                    lines.append(f"{p.get('name')} x{qty} - ¥{price * qty}")
                total += int(price) * int(qty)

        lines.append(f"\n合計: ¥{total}")
        popup = Popup(title='ご注文の確認', content=Label(text='\n'.join(lines), color=(1,1,1,1), font_size=sp(16)), size_hint=(0.8, 0.6), background='atlas://data/images/defaulttheme/button')
        popup.open()

if __name__ == '__main__':
    ListViewApp().run()