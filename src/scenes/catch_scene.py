"""
aka 猜 Shiro 在哪個 bed 上
"""

import pygame as pg
import random
from src.scenes.scene import Scene
from src.utils import GameSettings
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, resource_manager
from src.core import GameManager
from typing import override

class CatchScene(Scene):
    def __init__(self, game_manager: GameManager):
        super().__init__()
        self.game_manager = game_manager
        self.result_text = "" # 最後會是成功或失敗
        self.is_finished = False
        
        self.real = random.sample([1, 2, 3, 4, 5, 6], 2) # 決定誰是真袋子
        
        raw_img = resource_manager.get_image("shiro.png")
        self.top_image = pg.transform.scale(raw_img, (292, 215))
        
        self.font = pg.font.SysFont("Arial", 24, bold=True)
        # self.result_font = pg.font.SysFont("Arial", 32, bold=True)
        ins_text_1 = "I don't have any pictures of Domo, so here is my cat. His name is Shiro"
        ins_text_2 = "He sleep on my book to prevent me from studying, what a nice cat"
        ins_text_3 = "You want to find the perfect bed for Shiro, so that he will not sleep on my book again"
        ins_text_4 = "While you don't know which one does shiro like"
        ins_text_5 = "So take a guess :D"
        self.instruction_text = [ins_text_1, ins_text_2, ins_text_3, ins_text_4, ins_text_5]
        
        # perfect_beds
        self.perfect_bed_buttons: list[Button] = []
        
        # 這坨是原圖尺寸
        btn_w = 186
        btn_h = 61
        spacing = 30
        
        total_width = (3 * btn_w) + (2 * spacing)
        start_x = (GameSettings.SCREEN_WIDTH - total_width) // 2
        start_y = 500 # 實測，說明文字會在 450 左右
        
        for i in range(6):
            # 3 行 2 列
            row = i // 3
            col = i % 3
            
            x = start_x + col * (btn_w + spacing)
            y = start_y + row * (btn_h + spacing)
            
            btn = Button(
                img_path = "perfect_bed.png", 
                img_hovered_path = None,
                x = x, y = y,
                width = btn_w, height = btn_h,
                on_click = lambda idx=i+1: self.on_bag_click(idx)
            )
            self.perfect_bed_buttons.append(btn)

    # 偵測有沒有被點擊之類的
    def on_bag_click(self, index: int):
        if self.is_finished: return        
        sound_manager.play_sound("bababoy.wav")

        # 猜對
        if index in self.real:
            self.result_text = "Aha! Shiro likes this bed so much! All Accepted"
            
            new_monster = {
                "name": "Shiro",
                "hp": 10000,
                "max_hp": 10000,
                "level": 999,
                "sprite_path": "shiro.png"
            }
            self.game_manager.bag.monsters.append(new_monster)
        
        # 猜錯 
        else:
          self.result_text   = "Oops, it seems like Shiro isn't satisfy with this bed. Not Accepted (0/6)"
            
        self.is_finished = True

    @override
    def update(self, dt: float):
        if self.is_finished:
            if pg.key.get_pressed()[pg.K_SPACE]:
                scene_manager.change_scene("game")
            return

        for it in self.perfect_bed_buttons:
            it.update(dt)

    @override
    def draw(self, screen: pg.Surface):
        screen.fill((30, 100, 50))
        
        # 上面的大 Shiro
        img_rect = self.top_image.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, 160))
        screen.blit(self.top_image, img_rect)
        
        # 說明文字
        start_x = GameSettings.SCREEN_WIDTH // 2
        start_y = 290
        padding = 35
        for text in self.instruction_text:
            text_surf = self.font.render(text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(start_x, start_y))
            screen.blit(text_surf, text_rect)
            start_y += padding
        
        # 按鈕
        for button in self.perfect_bed_buttons:
            button.draw(screen)
        
        if self.is_finished:
            final_text = f"{self.result_text} | Press SPACE to return"
            result_surf = self.font.render(final_text, True, (255, 255, 255))
            result_rect = result_surf.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT - 30))
            screen.blit(result_surf, result_rect)