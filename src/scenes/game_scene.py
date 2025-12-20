"""
負責管遊戲畫面，更新玩家與敵人
還有 camera 之類雜七雜八的東西

render: 把字體變成圖片，才可以 blit 出來
parameter 分別是 text: str, antialias: bool, color: tuple
str 放文字，antialias 是去鋸齒，設為 True 就對了別管他
color 分別是 (R, G, B)
"""

import pygame as pg
import threading
import time
import os
import sys
import random

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager, input_manager
from src.sprites import Sprite
from typing import override
from src.interface.components import Button, Checkbox, Slider
from src.entities.merchant import Merchant

class GameScene(Scene):
    # 喔我真的好討厭冒號前不空後空的規範，為什麼不是前空後不空：（
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite

    merchant_sell_buttons: list[Button] # 這個是商人的售出按鈕
    credit_icon: Sprite # 左上角那咖常駐的標示

    show_overlay: str # Can be Nothing | Setting | Bag

    # Buttons
    bag_button: Button
    setting_button: Button
    close_button: Button
    shutdown_button: Button # 關掉遊戲的那個
    save_button: Button
    load_button: Button

    # Checkboxs
    trash_checkbox: Checkbox

    # Sliders
    volume_slider: Slider
    
    # Texts
    font: pg.font.Font
    title_font: pg.font.Font
    txt_nothing: pg.Surface
    txt_bar_hint: pg.Surface
    txt_do_not_press: pg.Surface

    def __init__(self):
        super().__init__()
        # Game Manager
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager
        
        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.sprite_online = Sprite("ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        
        self.show_overlay = "Nothing" #  Can be "Nothing" | "Setting" | "Bag"

        
        # 這坨都拿來控制 Bag Button
        btn_size = 64
        bag_btn_x = GameSettings.SCREEN_WIDTH - btn_size - 20
        bag_btn_y = 20
        self.bag_button = Button(
            img_path = "UI/button_backpack.png",
            img_hovered_path =  "UI/button_backpack_hover.png", 
            x = bag_btn_x, y = bag_btn_y,
            width = btn_size , height = btn_size, 
            on_click = lambda: self.set_overlay("Bag")
        )

        # 這坨拿來控制設定 overlay 按鈕
        setting_x = bag_btn_x - btn_size - 10
        setting_y = 20
        self.setting_button = Button(
            img_path = "UI/button_setting.png",
            img_hovered_path = "UI/button_setting_hover.png",
            x = setting_x, y = 20,
            width = btn_size, height = btn_size,
            on_click = lambda: self.set_overlay("Setting")
        )
        
        # 這坨拿來控制退出 overlay 按鈕
        close_btn_x = GameSettings.SCREEN_WIDTH - 20 - btn_size - 10 
        close_btn_y = 20 + 10
        self.close_button = Button(
            img_path = "UI/button_x.png",
            img_hovered_path = "UI/button_x_hover.png",
            x = close_btn_x, y = close_btn_y,
            width = btn_size, height = btn_size,
            on_click = lambda: self.set_overlay("Nothing")
        )

        # 這坨拿來處理文字
        self.font = pg.font.SysFont("Arial", 24)
        self.title_font = pg.font.SysFont("Arial", 32, bold=True)
        self.txt_nothing = self.font.render("Obviously, nothing happened :D", True, (255, 255, 255))
        self.txt_bar_hint = self.font.render("Drag to shut down your computer", True, (255, 255, 255))
        self.txt_do_not_press = self.font.render("DO NOT PRESS", True, (255, 255, 255))

        # 這坨拿來處理 slider, checkbox, 直接從 setting scene 複製過來
        center_x = GameSettings.SCREEN_WIDTH // 2
        start_y = GameSettings.SCREEN_HEIGHT // 3

        # Checkbox
        self.trash_checkbox = Checkbox(
            x = center_x // 4, 
            y = start_y // 2,
            size = 64,
            img_checked = "UI/raw/UI_Flat_ButtonCheck01a.png",
            img_unchecked = "UI/raw/UI_Flat_ButtonCross01a.png",
            click_sound = "bababoy.wav", 
            initial_state = True
        )

        # Slider
        self.volume_slider = Slider(
            x = center_x // 4,
            y = int(start_y * 1.2),
            w = 300,
            h = 20,
            img_bar = "UI/raw/UI_Flat_BarFill01f.png",
            img_knob = "UI/raw/doge.png",
            initial_value = GameSettings.AUDIO_VOLUME
        )

        # Shutdown Button
        self.shutdown_button = Button(
            img_path = "UI/raw/shut_down_button.jpg",
            img_hovered_path = "UI/raw/shut_down_button_hover.jpg",
            x = center_x // 4, y = int(start_y * 1.5),
            width = 100, height = 100,
            on_click = self.shutdown_game
        )

        # 這坨是 Save Button
        self.save_button = Button(
            img_path="UI/button_save.png",
            img_hovered_path="UI/button_save_hover.png",
            x=center_x // 4,
            y=int(start_y * 2),
            width=100, height=100,
            on_click=self.save_game
        )

        # 這坨是 Load Button
        self.load_button = Button(
            img_path="UI/button_load.png",
            img_hovered_path="UI/button_load_hover.png",
            x=center_x // 4 + 120,
            y=int(start_y * 2),
            width=100, height=100,
            on_click=self.load_game
        )

        # 這坨是商人
        self.credit_icon = Sprite("ingame_ui/coin.png", (32, 32))
        self.merchant_sell_buttons = [] # 一大串販賣按鈕

    # 把 overlay 叫出來和關掉用的 func.
    def set_overlay(self, rep: str) -> None:
        assert (rep in ["Nothing", "Setting", "Bag", "Merchant", "Minimap"]), f"set_overlay 被丟了奇怪的東西進來：{rep}"
        self.show_overlay = rep
        if rep == "Nothing":
            sound_manager.play_sound("gugugaga_2.mp3")
        else:
            sound_manager.play_sound("gugugaga.mp3")

    # 字面上的意思，畫小地圖！
    def _draw_minimap(self, screen: pg.Surface):
        # 這好像是直接把整張圖片幹過來，十分舒服
        raw_map_surf = self.game_manager.current_map._surface
        
        max_w = GameSettings.SCREEN_WIDTH * 0.75
        max_h = GameSettings.SCREEN_HEIGHT * 0.75
        
        scale_w = max_w / raw_map_surf.get_width()
        scale_h = max_h / raw_map_surf.get_height()
        # 避免直接無情超出螢幕
        scale = min(scale_w, scale_h)
        
        new_w = int(raw_map_surf.get_width() * scale)
        new_h = int(raw_map_surf.get_height() * scale)
        minimap_surf = pg.transform.scale(raw_map_surf, (new_w, new_h))
        
        start_x = (GameSettings.SCREEN_WIDTH - new_w) // 2
        start_y = (GameSettings.SCREEN_HEIGHT - new_h) // 2
        
        title = self.title_font.render("--- Minimap ---", True, (255, 255, 0))
        screen.blit(title, (GameSettings.SCREEN_WIDTH // 2 - title.get_width() // 2, start_y - 40))
        
        pg.draw.rect(screen, (0, 0, 0, 150), (start_x - 5, start_y - 5, new_w + 10, new_h + 10))
        screen.blit(minimap_surf, (start_x, start_y))
        
        # 這邊就是座標了
        px = self.game_manager.player.position.x * scale
        py = self.game_manager.player.position.y * scale
        
        mini_px = int(px)
        mini_py = int(py)
        # 左(上)界要和 minimap 同步
        final_x = start_x + mini_px
        final_y = start_y + mini_py
    
        pg.draw.circle(screen, (255, 0, 0), (final_x, final_y), 5)

    # 計算 selling_button 們放哪裡用的
    def _init_merchant_buttons(self):
        self.merchant_sell_buttons = []
        bag = self.game_manager.bag
        
        start_x = 400
        current_y = 100 + 35
    
        if len(bag.monsters) == 0:
            current_y += 35
        else:
            current_y += len(bag.monsters) * 35
            
        current_y += 25
        current_y += 35
        
        for i, item in enumerate(bag.items):
            btn = Button(
                img_path="UI/button_shop.png",
                img_hovered_path="UI/button_shop_hover.png",
                x=start_x, 
                y=current_y - 5,
                width=60, height=30,
                on_click=lambda idx=i: self._sell_item(idx)
            )
            self.merchant_sell_buttons.append(btn)
            current_y += 35


    # 賣東西，啊因為我很懶，所以不能買東西
    def _sell_item(self, index: int):
        bag = self.game_manager.bag
        if 0 <= index < len(bag.items):
            item = bag.items[index]
            bag.credit += random.randint(1, 10)
    
            if item['count'] > 1:
                item['count'] -= 1
            else:
                bag.items.pop(index)
            
            # 誒明天早上起來換個音效啦
            sound_manager.play_sound("gugugaga.mp3")
            
            # 背包變了，按鈕就要重新生成一次
            self._init_merchant_buttons()

    # 從 setting_scene 抄來的 shutdown_button 專用 func.
    @staticmethod
    def shutdown_game() -> None:
        sound_manager.play_sound("drop.wav")
        cmd_duck = (
            'start "DATA CORRUPTION" cmd /v:on /k '
            '"color 0a & mode 1000 & cls & '
            'QUACK...!'
            'timeout /t 1 >nul & '
            'for /l %x in (0,0,0) do ('
                '(for /l %y in (1,1,15) do @echo 0x!random!  F!random!A  9C-!random!  !random!X  ERROR-!random!) & '
                'timeout /t 1 >nul'
            ')"'
        )
        os.system(cmd_duck)
        pg.quit()
        sys.exit()

    def save_game(self):
        sound_manager.play_sound("huh.wav")
        self.game_manager.save("saves/game0.json")
        print("Game Saved!") # 誒你之後有空可以移到遊戲畫面上

    def load_game(self):
        sound_manager.play_sound("huh.wav")
        new_manager = GameManager.load("saves/game0.json")
        
        if new_manager is not None: # PEP-8 說不要寫 != None
            self.game_manager = new_manager
            print("Game Loaded!")
        else:
            print("Failed to load game")

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()
        
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):
        # Check if there is assigned next scene
        self.game_manager.try_switch_map()
        
        # about overlay
        if self.show_overlay != "Nothing":
            self.close_button.update(dt)
            if self.show_overlay == "Setting":
                self.trash_checkbox.update(dt)
                self.volume_slider.update(dt)
                self.shutdown_button.update(dt)
                self.save_button.update(dt)
                self.load_button.update(dt)

                current_vol = self.volume_slider.get_value()
                GameSettings.AUDIO_VOLUME = current_vol
                if sound_manager.current_bgm:
                    sound_manager.current_bgm.set_volume(current_vol)
            elif self.show_overlay == "Merchant":
                for btn in self.merchant_sell_buttons:
                     btn.update(dt)
            elif self.show_overlay == "Minimap":
                if input_manager.key_pressed(pg.K_m):
                    self.set_overlay("Nothing")
        else:
            self.bag_button.update(dt)
            self.setting_button.update(dt)

            if input_manager.key_pressed(pg.K_m):
                self.set_overlay("Minimap")

            # 他們不像按鈕一樣有 on_click 可以用，所以只能手刻
            for merchant in self.game_manager.current_merchants:
                merchant.update(dt)
                # 偵測是否按下空白鍵開啟商店
                if merchant.detected and input_manager.key_pressed(pg.K_SPACE):
                    self._init_merchant_buttons()
                    self.set_overlay("Merchant")

        # Update player and other data
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
            
        # Update others
        self.game_manager.bag.update(dt)
        
        if self.game_manager.player is not None and self.online_manager is not None:
            _ = self.online_manager.update(
                self.game_manager.player.position.x, 
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name
            )
        
    @override
    def draw(self, screen: pg.Surface):        
        if self.game_manager.player:
            '''
            [TODO HACKATHON 3][completed]
            Implement the camera algorithm logic here
            Right now it's hard coded, you need to follow the player's positions
            you may use the below example, but the function still incorrect, you may trace the entity.py
            
            camera = self.game_manager.player.camera
            '''
            camera = self.game_manager.player.camera # This is freaking correct now
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)

        for merchant in self.game_manager.current_merchants:
            merchant.draw(screen, camera)

        self.game_manager.bag.draw(screen)
        
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)

        self._draw_credits_ui(screen)
        # Buttons
        self.bag_button.draw(screen)
        self.setting_button.draw(screen)

        if self.show_overlay != "Nothing":
            overlay_surface = pg.Surface((GameSettings.SCREEN_WIDTH-40, GameSettings.SCREEN_HEIGHT-40), pg.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 150)) # 聽說 150 是半透明
            screen.blit(overlay_surface, (20, 20))
            self.close_button.draw(screen) # 退出鈕

            # 半透明ㄉ那個
            overlay_surface = pg.Surface((GameSettings.SCREEN_WIDTH-40, GameSettings.SCREEN_HEIGHT-40), pg.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 150)) # 聽說 150 是半透明，200 太黑了不喜歡
            screen.blit(overlay_surface, (20, 20))
            
            self.close_button.draw(screen)
            if self.show_overlay == "Bag":
                self._draw_backpack(screen)
            elif self.show_overlay == "Setting":
                self._draw_setting(screen)
            elif self.show_overlay == "Merchant":
                self._draw_merchant(screen)
            elif self.show_overlay == "Minimap":
                    self._draw_minimap(screen)

    # 這個也太雜了，畫金幣
    def _draw_credits_ui(self, screen: pg.Surface):
        self.credit_icon.update_pos(Position(10, 10))
        self.credit_icon.draw(screen)
        credit_txt = self.title_font.render(f"{self.game_manager.bag.credit}", True, (255, 215, 0)) # 金色
        screen.blit(credit_txt, (50, 10))

    # 這坨太雜了我丟出來寫
    def _draw_backpack(self, screen: pg.Surface) -> None:
        title = self.title_font.render("GUGUGAGA", True, (255, 255, 0)) # 聽說這是黃色
        screen.blit(title, (60, 40))
            
        bag = self.game_manager.bag
        start_x = 60
        start_y = 100
        line_height = 35
            
        # monsters
        monster_title = self.font.render(f"--- Monsters Without Babies : Total = ({len(bag.monsters)}) ---", True, (100, 255, 100))
        screen.blit(monster_title, (start_x, start_y))
        start_y += line_height
            
        if len(bag.monsters) == 0:
            screen.blit(self.font.render("What the hell bro there's no monsters here", True, (200, 200, 200)), (start_x + 20, start_y))
            start_y += line_height
        else:
            for mon in bag.monsters:
                text = f"{mon['name']} (Level.{mon['level']}) - HP: {mon['hp']}/{mon['max_hp']}"
                surf = self.font.render(text, True, (255, 255, 255))
                screen.blit(surf, (start_x + 20, start_y))
                start_y += line_height

        # items
        start_y += 25 # 多一點間隔，因為我懶得畫間隔線
        item_title = self.font.render(f"--- Items : Total = ({len(bag.items)}) ---", True, (100, 255, 100))
        screen.blit(item_title, (start_x, start_y))
        start_y += line_height

        if len(bag.items) == 0:
            screen.blit(self.font.render("How poor are you? You're bag is emptyyyyyyyyy!", True, (200, 200, 200)), (start_x + 20, start_y))
        else:
            for it in bag.items:
                text = f"{it['name']} x {it['count']}"
                surf = self.font.render(text, True, (255, 255, 255))
                screen.blit(surf, (start_x + 20, start_y))
                start_y += line_height

    # 這坨也太雜了，不想看 draw 裡面一堆垃圾
    def _draw_setting(self, screen: pg.Surface):
        title = self.title_font.render("Setting, though it might not actually work :D", True, (0, 255, 255))
        screen.blit(title, (60, 40))

        self.trash_checkbox.draw(screen)
        self.volume_slider.draw(screen)
        self.shutdown_button.draw(screen)
        self.save_button.draw(screen)
        self.load_button.draw(screen)

        # trash_checkbox
        tcb_rect = self.trash_checkbox.rect
        screen.blit(self.txt_nothing, (tcb_rect.right + 20, tcb_rect.centery - 12))

        # volume_slider
        sl_rect = self.volume_slider.rect_bar
        screen.blit(self.txt_bar_hint, (sl_rect.centerx - self.txt_bar_hint.get_width() // 2, sl_rect.top - 40))

        # shutdown_button
        dnp_rect = self.shutdown_button.hitbox
        screen.blit(self.txt_do_not_press, (dnp_rect.right + 20, dnp_rect.centery - 12))

    # 我用了一個超髒的做法，抄背包
    def _draw_merchant(self, screen: pg.Surface):
        title = self.title_font.render("MERCHANT - SELL TRASH TO ME. Nope, not yourself plz", True, (0, 255, 255))
        screen.blit(title, (60, 40))
        
        self._draw_backpack(screen)
        for btn in self.merchant_sell_buttons:
            btn.draw(screen)
            
        pg.draw.rect(screen, (0, 0, 0), (60, 40, 300, 40)) # 塗黑原本的 GUGUGAGA
        screen.blit(title, (60, 40)) # 畫上新標題
