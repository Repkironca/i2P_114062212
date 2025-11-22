"""
這邊會告訴你誰是草叢、誰是傳送門
誰是障礙物、誰是敵人之類的
"""

import pygame as pg
import pytmx

from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport

class Map:
    # Map Properties
    path_name: str
    tmxdata: pytmx.TiledMap
    # Position Argument
    spawn: Position
    teleporters: list[Teleport]
    # Rendering Properties
    _surface: pg.Surface
    _collision_map: list[pg.Rect]
    _bush_map: list[pg.Rect] # 放草叢ㄉ

    def __init__(self, path: str, tp: list[Teleport], spawn: Position):
        self.path_name = path
        self.tmxdata = load_tmx(path)
        self.spawn = spawn
        self.teleporters = tp

        pixel_w = self.tmxdata.width * GameSettings.TILE_SIZE
        pixel_h = self.tmxdata.height * GameSettings.TILE_SIZE

        # Prebake the map
        self._surface = pg.Surface((pixel_w, pixel_h), pg.SRCALPHA)
        self._render_all_layers(self._surface)
        # Prebake the collision map
        self._collision_map = self._create_collision_map()
        self._bush_map = self._create_bush_map()

    # 這咖拿來檢查腳下的是不是草叢
    def check_bush(self, rect: pg.Rect) -> bool:
        for it in self._bush_map:
            if rect.colliderect(it):
                return True
        return False

    def update(self, dt: float):
        return

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        screen.blit(self._surface, camera.transform_position(Position(0, 0)))
        
        # Draw the hitboxes collision map
        if GameSettings.DRAW_HITBOXES:
            for rect in self._collision_map:
                pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(rect), 1)
        
    def check_collision(self, rect: pg.Rect) -> bool:
        '''
        [TODO HACKATHON 4][complete]
        Return True if collide if rect param collide with self._collision_map
        Hint: use API colliderect and iterate each rectangle to check
        '''
        for temp in self._collision_map:
            if rect.colliderect(temp):
                return True
        return False
        
    def check_teleport(self, pos: Position) -> Teleport | None:
        '''[TODO HACKATHON 6] [complete]
        Teleportation: Player can enter a building by walking into certain tiles defined inside saves/*.json, and the map will be changed
        Hint: Maybe there is an way to switch the map using something from src/core/managers/game_manager.py called switch_... 
        '''
        px = int(pos.x // GameSettings.TILE_SIZE)
        py = int(pos.y // GameSettings.TILE_SIZE)
        for duck in self.teleporters:
            duck_x = int(duck.pos.x // GameSettings.TILE_SIZE)
            duck_y = int(duck.pos.y // GameSettings.TILE_SIZE)
            if (duck_x == px and duck_y == py):
                return duck

        return None

    def _render_all_layers(self, target: pg.Surface) -> None:
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                self._render_tile_layer(target, layer)
            # elif isinstance(layer, pytmx.TiledImageLayer) and layer.image:
            #     target.blit(layer.image, (layer.x or 0, layer.y or 0))
 
    def _render_tile_layer(self, target: pg.Surface, layer: pytmx.TiledTileLayer) -> None:
        for x, y, gid in layer:
            if gid == 0:
                continue
            image = self.tmxdata.get_tile_image_by_gid(gid)
            if image is None:
                continue

            image = pg.transform.scale(image, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
            target.blit(image, (x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE))
    
    def _create_collision_map(self) -> list[pg.Rect]:
        ret = []
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and ("collision" in layer.name.lower() or "house" in layer.name.lower()):
                for x, y, gid in layer:
                    if gid != 0:
                        '''
                        [TODO HACKATHON 4][complete]
                        rects.append(pg.Rect(...))
                        Append the collision rectangle to the rects[] array
                        Remember scale the rectangle with the TILE_SIZE from settings
                        '''
                        if gid != 0:
                            # Rect 吃像素座標
                            # Rect(left, top, width, height) 前兩個是起點，後兩個是大小
                            ret.append(pg.Rect(x * GameSettings.TILE_SIZE, 
                                                 y * GameSettings.TILE_SIZE, 
                                                 GameSettings.TILE_SIZE, 
                                                 GameSettings.TILE_SIZE))
        return ret

    # 依樣畫葫蘆時間
    def _create_bush_map(self) -> list[pg.Rect]:
        ret = []
        for layer in self.tmxdata.visible_layers:
            # 只要圖層名稱裡面有 bush 就算草叢，我才不管
            if isinstance(layer, pytmx.TiledTileLayer) and ("bush" in layer.name.lower()):
                for x, y, gid in layer:
                    if gid != 0:
                        ret.append(pg.Rect(x * GameSettings.TILE_SIZE, 
                                           y * GameSettings.TILE_SIZE, 
                                           GameSettings.TILE_SIZE, 
                                           GameSettings.TILE_SIZE))
        return ret

    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        tp = [Teleport.from_dict(t) for t in data["teleport"]]
        pos = Position(data["player"]["x"] * GameSettings.TILE_SIZE, data["player"]["y"] * GameSettings.TILE_SIZE)
        return cls(data["path"], tp, pos)

    def to_dict(self):
        return {
            "path": self.path_name,
            "teleport": [t.to_dict() for t in self.teleporters],
            "player": {
                "x": self.spawn.x // GameSettings.TILE_SIZE,
                "y": self.spawn.y // GameSettings.TILE_SIZE,
            }
        }
