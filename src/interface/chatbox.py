# 這麼說吧，這個檔案不是我寫的，我甚至還沒看 AI 生了什麼

import pygame as pg
from src.utils import GameSettings
from src.core import OnlineManager

class ChatBox:
    def __init__(self, online_manager: OnlineManager):
        self.online_manager = online_manager
        self.active = False
        self.text = ""
        self.chat_history = []
        
        # 嘗試使用支援中文的字體，若失敗則回退到預設
        possible_fonts = ["Microsoft JhengHei", "SimHei", "Arial", "sans-serif"]
        self.font = None
        for f in possible_fonts:
            try:
                self.font = pg.font.SysFont(f, 20)
                break
            except:
                continue
        if self.font is None:
            self.font = pg.font.Font(None, 24)

        # 介面尺寸設定
        self.box_width = 400
        self.box_height = 300
        self.input_height = 30
        self.padding = 5
        
        # 位置：左下角
        self.x = 20
        self.y = GameSettings.SCREEN_HEIGHT - self.box_height - 20
        
        self.input_rect = pg.Rect(self.x, self.y + self.box_height - self.input_height, self.box_width, self.input_height)
        self.history_bg_rect = pg.Rect(self.x, self.y, self.box_width, self.box_height - self.input_height)

    def toggle(self):
        self.active = not self.active
        if self.active:
            pg.key.start_text_input()
        else:
            pg.key.stop_text_input()
            self.text = ""

    def handle_event(self, event: pg.event.Event):
        if not self.active:
            return

        if event.type == pg.TEXTINPUT:
            self.text += event.text
            
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                if self.text.strip():
                    # 發送訊息
                    self.online_manager.send_chat(self.text)
                    self.text = ""
                    # 發送後關閉輸入模式 (或是你想保持開啟也可以，這裡依據通常習慣設定為發送後關閉)
                    self.toggle()
                else:
                    self.toggle() # 空白訊息直接關閉
                    
            elif event.key == pg.K_BACKSPACE:
                self.text = self.text[:-1]
                
            elif event.key == pg.K_ESCAPE:
                self.toggle()

    def update(self):
        # 從 OnlineManager 同步最新訊息
        self.chat_history = self.online_manager.get_recent_chat()

    def draw(self, screen: pg.Surface):
        # 1. 繪製聊天記錄背景 (半透明黑)
        s = pg.Surface((self.history_bg_rect.width, self.history_bg_rect.height))
        s.set_alpha(100)
        s.fill((0, 0, 0))
        screen.blit(s, (self.history_bg_rect.x, self.history_bg_rect.y))
        
        # 2. 繪製輸入框 (只有 active 時比較明顯)
        if self.active:
            pg.draw.rect(screen, (50, 50, 50), self.input_rect)
            pg.draw.rect(screen, (0, 255, 255), self.input_rect, 2)
        else:
            # 非 active 時只顯示淡淡的底或是完全不顯示輸入框背景
            pass

        # 3. 繪製輸入文字
        if self.active:
            txt_surf = self.font.render(self.text + "|", True, (255, 255, 255))
            screen.blit(txt_surf, (self.input_rect.x + 5, self.input_rect.y + 5))
        else:
            # 提示按 T
            if not self.active:
                hint_surf = self.font.render("[Press T to Chat]", True, (150, 150, 150))
                screen.blit(hint_surf, (self.input_rect.x + 5, self.input_rect.y + 5))

        # 4. 繪製歷史訊息 (由下往上畫)
        # 我們只畫能塞進框框的最後幾條
        line_height = 25
        max_lines = (self.history_bg_rect.height - 10) // line_height
        
        # 取最後 max_lines 條
        msgs_to_draw = self.chat_history[-max_lines:]
        
        start_y = self.history_bg_rect.bottom - line_height - 5
        
        for msg in reversed(msgs_to_draw):
            sender = msg.get("from", "?")
            text = msg.get("text", "")
            # 簡單區分顏色：自己發的跟別人發的 (如果你有存 player_id 可以判斷，這裡先統一白色)
            display_text = f"{sender}: {text}"
            
            text_surf = self.font.render(display_text, True, (255, 255, 255))
            screen.blit(text_surf, (self.history_bg_rect.x + 5, start_y))
            start_y -= line_height