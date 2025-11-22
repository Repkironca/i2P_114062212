"""
管好你自己。
喔，草叢判定跟碰撞判定也在這裡
"""
from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager, scene_manager
from src.utils import Position, PositionCamera, GameSettings, Logger
from src.core import GameManager
import math
from typing import override

class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)

    @override
    def update(self, dt: float) -> None:
        dis = Position(0, 0) # utils\definition，反正裡面裝一個 x 和 y，都是 float，有 copy() 和 distance_to()
        '''
        [TODO HACKATHON 2][complete]
        Calculate the distance change, and then normalize the distance
        '''

        """
        dt 是一個時間校正因子，用來解決各電腦的幀率不同
        即＂我每一幀之間隔多少秒＂
        dis.x 和 dis.y 就是位移
        校正？我管他的，就是給我除根號二，傻逼才用單位向量
        """
        """
        snap to grid 的概念就是，如果我的角色已經撞牆且卡在裡面
        我要強制把他校正到一個正確的地方
        check_collision() 是一個吃碰撞箱的函數，被寫在 game_manager 裡
        self.game_manager 來自 Entity 的 __init__
        順帶一提，這和 TODO-2 完全可以合併，但我才不管，略略略
        """

        enemy_list = self.game_manager.current_enemy_trainers # 被存在這鬼地方
        player_rect = self.animation.rect # 好長，我懶得打

        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= self.speed
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += self.speed
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= self.speed
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += self.speed
        
        if dis.x != 0 and dis.y != 0:
            dis.x /= (2**0.5)
            dis.y /= (2**0.5)

        # self.position.x += dis.x*dt
        new_x = self.position.x+ dis.x*dt
        new_y = self.position.y

        rect = pg.Rect(new_x, new_y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        collide_x = self.game_manager.check_collision(rect) # 撞牆


        if collide_x:
            # new_x = self.
            
            # else: 
            new_x = self._snap_to_grid(new_x) # 別動了，順便強制貼齊
            

        # self.position.y += dis.y*dt
        new_y = self.position.y+ dis.y*dt
        rect = pg.Rect(new_x, new_y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        collide_y = self.game_manager.check_collision(rect) # 撞牆

        if collide_y :
            # self.position.y -= dis.y * 
            # if (self._snap_to_grid(self.position.y) == self.position.y):
            #     new_y = self.position.y
            
            # else: 
            new_y = self._snap_to_grid(new_y) # 別動了，順便強制貼齊
            
            
        self.position.x = new_x
        self.position.y = new_y
        '''
        [TODO HACKATHON 4]
        Check if there is collision, if so try to make the movement smooth
        Hint #1 : use entity.py _snap_to_grid function or create a similar function
        Hint #2 : Beware of glitchy teleportation, you must do
                    1. Update X
                    2. If collide, snap to grid
                    3. Update Y
                    4. If collide, snap to grid
                  instead of update both x, y, then snap to grid
        
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= ...
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += ...
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= ...
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += ...
        
        self.position = ...
        '''



        # Check teleportation
        tp = self.game_manager.current_map.check_teleport(self.position)
        if tp:
            dest = tp.destination
            self.game_manager.switch_map(dest)
        
        # 草叢
        if input_manager.key_pressed(pg.K_SPACE):
            player_rect = self.animation.rect
            if self.game_manager.current_map.check_bush(player_rect):
                # 在上面 import 會壞掉，是因為循環嗎？之後再研究
                from src.scenes.catch_scene import CatchScene
                catch_scene = CatchScene(self.game_manager)
                scene_manager.register_scene("catch", catch_scene)
                scene_manager.change_scene("catch")

        super().update(dt)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)

