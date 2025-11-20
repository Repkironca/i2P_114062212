"""
用在 setting 的那根滑桿
我直接把上面的旋鈕跟拉桿本身合併
不管，因為我很懶惰，嘻嘻嘻
"""

import pygame as pg
from src.interface.components import UIComponent
from src.sprites import Sprite
from src.core.services import input_manager
from src.utils import GameSettings
from typing import override

class Slider(UIComponent):
    def __init__(self, x: int, y: int, w: int, h: int, 
                 img_bar: str, img_knob: str, 
                 initial_value: float = 0.5):
        
        self.value: float = max(0.0, min(1.0, initial_value)) # 範圍從 0 到 1
        self.rect_bar = pg.Rect(x, y, w, h)
        
        self.sprite_bar = Sprite(img_bar, (w, h))
        
        knob_size = int(h * 2.5) # 我設成高度的 2 倍
        self.sprite_knob = Sprite(img_knob, (knob_size, knob_size))
        self.knob_width = knob_size
    
        self.dragging: bool = False # 正在被拖曳

    @override
    def update(self, dt: float) -> None:
        mouse_pos = input_manager.mouse_pos
        mouse_down = input_manager.mouse_down(1) 
        mouse_pressed = input_manager.mouse_pressed(1) 
        mouse_released = input_manager.mouse_released(1)

        # 旋鈕
        center_x = self.rect_bar.x + (self.rect_bar.width * self.value) # value 就是幾趴的拉桿
        knob_x = center_x - (self.knob_width // 2) # 扣掉一半寬度，這個是靠左的座標
        knob_y_center = self.rect_bar.centery
        knob_rect = pg.Rect(knob_x, knob_y_center - self.knob_width // 2, 
                            self.knob_width, self.knob_width)

        # 檢查是否進入拖曳模式
        if knob_rect.collidepoint(mouse_pos) and mouse_pressed:
            self.dragging = True
        
        # 2. 正在拖曳
        if self.dragging:
            if mouse_released: # 這個寫在外面會爛掉
                self.dragging = False
            else:
                relative_x = mouse_pos[0] - self.rect_bar.x
                max_delta = self.rect_bar.width
                if max_delta > 0:
                    self.value = (relative_x) / max_delta # 我的位置在幾分之幾
                    self.value = max(0.0, min(1.0, self.value))

    @override
    def draw(self, screen: pg.Surface) -> None:
        # 條
        screen.blit(self.sprite_bar.image, self.rect_bar)
        
        # 拉桿
        center_x = self.rect_bar.x + (self.rect_bar.width * self.value)
        knob_x = center_x - (self.knob_width // 2)
        knob_y = self.rect_bar.centery - self.knob_width // 2
        
        screen.blit(self.sprite_knob.image, (knob_x, knob_y))
        
    def get_value(self) -> float:
        return self.value