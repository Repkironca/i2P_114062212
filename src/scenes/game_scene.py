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

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager
from src.sprites import Sprite
from typing import override
from src.interface.components import Button

class GameScene(Scene):
    # 喔我真的好討厭冒號前不空後空的規範，為什麼不是前空後不空：（
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
    overlay_button: Button
    show_overlay: bool

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
        
        """
        這坨都拿來控制 button
        """
        self.show_overlay = False
        btn_size = 64
        btn_x = GameSettings.SCREEN_WIDTH - btn_size - 20
        btn_y = 20
        self.overlay_button = Button(
            "UI/button_backpack.png",
            "UI/button_backpack_hover.png",
            btn_x, btn_y,
            btn_size, btn_size,
            self.switch_overlay
        )

        """
        這坨拿來控制退出 overlay button
        """
        close_btn_x = GameSettings.SCREEN_WIDTH - 20 - btn_size - 10 
        close_btn_y = 20 + 10
        self.close_overlay_button = Button(
            "UI/button_x.png",
            "UI/button_x_hover.png",
            close_btn_x, close_btn_y,
            btn_size, btn_size,
            self.switch_overlay
        )

        """
        這坨拿來處理字體
        """
        self.font = pg.font.SysFont("Arial", 24)
        self.title_font = pg.font.SysFont("Arial", 32, bold=True)

    def switch_overlay(self) -> None:
        if (self.show_overlay):
            sound_manager.play_sound("gugugaga_2.mp3")
        else:
            sound_manager.play_sound("gugugaga.mp3")
        self.show_overlay = not self.show_overlay # 隱藏掉
        


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
        
        # update button
        if self.show_overlay:
            self.close_overlay_button.update(dt)
        else:
            self.overlay_button.update(dt)

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

        self.game_manager.bag.draw(screen)
        
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)

        self.overlay_button.draw(screen)
        if self.show_overlay:
            overlay_surface = pg.Surface((GameSettings.SCREEN_WIDTH-40, GameSettings.SCREEN_HEIGHT-40), pg.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 150)) # 聽說 150 是半透明
            screen.blit(overlay_surface, (20, 20))
            self.close_overlay_button.draw(screen) # 退出鈕

            """
            下面這坨來畫背包內容
            """
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
            
            if not bag.monsters:
                screen.blit(self.font.render("What the hell bro there's no monsters here", True, (200, 200, 200)), (start_x + 20, start_y))
                start_y += line_height
            else:
                for mon in bag.monsters:
                    text = f"{mon['name']} (Level.{mon['level']}) - HP: {mon['hp']}/{mon['max_hp']}"
                    surf = self.font.render(text, True, (255, 255, 255))
                    screen.blit(surf, (start_x + 20, start_y))
                    start_y += line_height

            # itmes
            start_y += 25 # 多一點間隔，因為我懶得畫間隔線
            item_title = self.font.render(f"--- Items : Total = ({len(bag.items)}) ---", True, (100, 255, 100))
            screen.blit(item_title, (start_x, start_y))
            start_y += line_height

            if not bag.items:
                screen.blit(self.font.render("How poor are you? You're bag is emptyyyyyyyyy!", True, (200, 200, 200)), (start_x + 20, start_y))
            else:
                for it in bag.items:
                    text = f"{it['name']} x {it['count']}"
                    surf = self.font.render(text, True, (255, 255, 255))
                    screen.blit(surf, (start_x + 20, start_y))
                    start_y += line_height