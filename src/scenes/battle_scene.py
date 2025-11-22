"""
字面上的意思，和百祥戰鬥的介面
"""

import pygame as pg
import random
import sys
import os
import platform

from src.scenes.scene import Scene
from src.utils import GameSettings
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, resource_manager
from src.entities.enemy_trainer import EnemyTrainer
from typing import override

class BattleLogger: # 我需要一個聊天室
    def __init__(self, x: int, y: int, w: int, h: int, font: pg.font.Font):
        self.rect = pg.Rect(x, y, w, h)
        self.font = font
        self.messages: list[str] = [] # 類似 queue，新訊息往後堆，而我 pop_front
        self.max_lines = int(h / (font.get_height() + 5)) # 訊息上限
        
    def log(self, text: str):
        self.messages.append(text)
        if len(self.messages) > self.max_lines:
            self.messages.pop(0)
            
    def draw(self, screen: pg.Surface):
        # 框框
        surf = pg.Surface((self.rect.width, self.rect.height), pg.SRCALPHA)
        surf.fill((0, 0, 0, 150))
        screen.blit(surf, self.rect)
        
        # 文字
        start_y = self.rect.top + 10
        line_height = self.font.get_height() + 5
        
        for i, msg in enumerate(self.messages): # emumerate 就是自動幫你依序裝成 tuple (index, msg)
            txt_surf = self.font.render(msg, True, (255, 255, 255))
            screen.blit(txt_surf, (self.rect.left + 10, start_y + i * line_height))

class BattleScene(Scene):
    def __init__(self, enemy: EnemyTrainer):
        super().__init__()
        self.enemy = enemy
        raw_img = resource_manager.get_image("character/phchou.jpg") # 這是周百祥
        self.enemy_img = pg.transform.scale(raw_img, (403, 269)) # 原始尺寸

        self.player_max_hp = 100
        self.player_hp = 100
        
        self.enemy_max_hp = random.randint(50, 150) # 血量取 50 到 150 隨便一個數字
        self.enemy_hp = self.enemy_max_hp
        self.is_battle_over = False
        
        self.font = pg.font.SysFont("Arial", 22, bold=True)
        
        # 聊天室
        log_w = 800
        log_h = 300
        log_x = (GameSettings.SCREEN_WIDTH - log_w) // 6
        log_y = 150
        self.logger = BattleLogger(log_x, log_y, log_w, log_h, self.font)
        
        # self.logger.log(f"Encountered {self.enemy.classification.name}!")
        self.logger.log(f"Encountered P.H.Chou!")
        self.logger.log("Battle Start!")

        btn_y = GameSettings.SCREEN_HEIGHT - 120
        btn_size = 80
        total_w = (btn_size * 5) + (30 * 4) # 五個按鈕 + 四個間距
        start_x = (GameSettings.SCREEN_WIDTH - total_w) // 2
        
        # 1. Attack
        self.attack_button = Button(
            img_path = "UI/attack_button.png",
            img_hovered_path = None,
            x = start_x, y = btn_y,
            width = btn_size, height = btn_size,
            on_click = self.attack
        )
        
        # 2. Russian Roulette
        self.roulette_button = Button(
            img_path = "UI/roulette_button.png",
            img_hovered_path = None,
            x = start_x + (btn_size + 30), y = btn_y,
            width = btn_size, height = btn_size,
            on_click = self.roulette
        )
        
        # 3. Daydream
        self.daydream_button = Button(
            img_path = "UI/daydream_button.png",
            img_hovered_path = None,
            x = start_x + (btn_size + 30) * 2, y = btn_y,
            width = btn_size, height = btn_size,
            on_click = self.daydream
        )
        
        # 4. Item
        self.item_button = Button(
            img_path = "UI/button_backpack.png",
            img_hovered_path = "UI/button_backpack_hover.png",
            x = start_x + (btn_size + 30) * 3, y = btn_y,
            width = btn_size, height = btn_size,
            on_click = self.use_item
        )
        
        # 5. Run
        self.run_button = Button(
            img_path = "UI/run_button.png",
            img_hovered_path = None,
            x = start_x + (btn_size + 30) * 4, y = btn_y,
            width = btn_size, height = btn_size,
            on_click = self.run
        )
        
        self.buttons = [
            (self.attack_button, "Attack"),
            (self.roulette_button, "Russian Roulette"),
            (self.daydream_button, "Daydream"),
            (self.item_button, "Item"),
            (self.run_button, "Run")
        ]

    def attack(self):
        if self.is_battle_over: return
        
        dmg = random.randint(15, 30)
        self.enemy_hp -= dmg
        self.logger.log(f"You attacked! Dealt {dmg} damage.")
        sound_manager.play_sound("bonk.mp3")
        
        if self.check_battle_end(): return
        else: self.enemy_turn()

    def roulette(self):
        if self.is_battle_over: return
        
        self.logger.log("Spinning the cylinder...")
        chance = random.random()
        sound_manager.play_sound("gunshot.wav")
        dmg = 80
        if chance < 0.6:
            self.enemy_hp -= dmg
            self.logger.log(f"BANG! You shot the enemy and dealt {dmg} damage. Lucky you.")
        else:
            self.player_hp -= dmg
            self.logger.log(f"BANG! You shot yourself and dealt {dmg} damage. Hehehe.")
        
        if self.check_battle_end(): return
        else: self.enemy_turn()

    def daydream(self):
        if self.is_battle_over: return
        
        sound_manager.play_sound("daydream.wav")
        self.logger.log("You daydreamed... Nothing happened")
        if self.check_battle_end(): return
        else: self.enemy_turn()

    def use_item(self):
        if self.is_battle_over: return
        self.logger.log("Great Proposal! While I haven't actually done it yet :D")

    def run(self):
        self._mocking_coward()

    def _mocking_coward(self):
        msg = "Don't worry coward! I've helped you to exit the game! You ran away successfully!"
        sys_name = platform.system() # 聽說這個可以檢查使用者的電腦環境

        # 然後說真的，我根本不會 bash 語法
        if sys_name == "Windows":
            cmd = f'start "COWARD" cmd /k "color 0c & echo {msg} & pause"'
            os.system(cmd)
        elif sys_name == "Linux":
            try:
                os.system(f'xterm -hold -e "echo {msg}"')
            except:
                print(msg)
        elif sys_name == "Darwin":
            script = f'tell application "Terminal" to do script "echo {msg}"'
            os.system(f"osascript -e '{script}'")

        pg.quit()
        sys.exit()

    def enemy_turn(self):
        enemy_dmg = random.randint(10, 25)
        self.player_hp -= enemy_dmg
        chance = random.random()
        if chance < 0.333:
            self.logger.log(f"Aeeey we'll have a pop quiz! Took {enemy_dmg} damage.")
        elif chance < 0.666:
            self.logger.log(f"Mary had a little lamb! Recieved {enemy_dmg} damage.")
        else:
            self.logger.log(f"Ch.16 is functions while ch.12 is recursion! Recieved {enemy_dmg} damage.")
        self.check_battle_end()

    def check_battle_end(self) -> bool:
        if self.enemy_hp <= 0:
            self.enemy_hp = 0 # 不太想讓它顯示負數
            self.is_battle_over = True
            self.logger.log("--------------------------------")
            self.logger.log("YOU WON! Press SPACE to return.")
            return True
            
        if self.player_hp <= 0:
            self.player_hp = 0 # 不太想讓它顯示負數
            self.is_battle_over = True
            self.logger.log("--------------------------------")
            self.logger.log("YOU DIED! Press SPACE to return.")
            return True
            
        return False

    @override
    def update(self, dt: float):
        if self.is_battle_over:
            if pg.key.get_pressed()[pg.K_SPACE]:
                scene_manager.change_scene("game")
            return

        for btn, _ in self.buttons: # 後面只是一個完全不重要的提示字
            btn.update(dt)

    @override
    def draw(self, screen: pg.Surface):
        screen.fill((20, 160, 190))
        self.logger.draw(screen)

        
        # enemy
        img_rect = self.enemy_img.get_rect(center=(GameSettings.SCREEN_WIDTH * 7 // 8, 100))
        screen.blit(self.enemy_img, img_rect)
        enemy_hp_text = f"Enemy HP: {self.enemy_hp}/{self.enemy_max_hp}"
        enemy_hp_surf = self.font.render(enemy_hp_text, True, (255, 50, 50))
        screen.blit(enemy_hp_surf, (img_rect.centerx - enemy_hp_surf.get_width() // 2, img_rect.bottom + 10))
        
        # 自己的血量
        player_hp_text = f"Player HP: {self.player_hp}/{self.player_max_hp}"
        player_hp_surf = self.font.render(player_hp_text, True, (255, 255, 255))
        screen.blit(player_hp_surf, (30, GameSettings.SCREEN_HEIGHT - 100))

        # Buttons
        for btn, button_name in self.buttons:
            btn.draw(screen) 
            text_list = button_name.split()
            counter = len(text_list)
            for it in text_list:
                lbl_surf = self.font.render(it, True, (200, 200, 200))
                start_x = btn.hitbox.centerx - lbl_surf.get_width() // 2
                start_y = btn.hitbox.top - 25*counter
                screen.blit(lbl_surf, (start_x, start_y))
                counter -= 1

            