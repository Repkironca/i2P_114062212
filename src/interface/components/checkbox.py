"""
設定裡面的 check_box
其實是偷 button 的 code 啦，嘻嘻
話說其實我根本不知道 override 是什麼
但不管，反正加就對了
"""

import pygame as pg

from src.interface.components import UIComponent
from src.sprites import Sprite
from src.core.services import input_manager, sound_manager
from typing import override

class Checkbox(UIComponent):

    def __init__(self, x: int, y: int, size: int, 
                 img_checked: str, img_unchecked: str,
                 click_sound: str, 
                 initial_state: bool = False
                 ):
        
        self.checked = initial_state
        self.rect = pg.Rect(x, y, size, size)
        
        self.sprite_checked = Sprite(img_checked, (size, size))
        self.sprite_unchecked = Sprite(img_unchecked, (size, size))
        self.click_sound = click_sound

    @override
    def update(self, dt: float) -> None:
        hover: bool = self.rect.collidepoint(input_manager.mouse_pos) # 滑鼠是否在框內
        pressed: bool = input_manager.mouse_pressed(1) # 聽說 1 是滑鼠左鍵
        
        if hover and pressed:
             self.checked = not self.checked
             sound_manager.play_sound(self.click_sound)
             # 誒記得晚點來加音效
             # sound_manager.play_sound("")

    @override
    def draw(self, screen: pg.Surface) -> None:
    	if (self.checked):
    		screen.blit(self.sprite_checked.image, self.rect)
    	else:
    		screen.blit(self.sprite_unchecked.image, self.rect)