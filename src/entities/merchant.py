import pygame
from src.entities.entity import Entity
from src.core.managers.game_manager import GameManager
from src.utils import Position, GameSettings, Direction
from src.sprites import Sprite
from typing import override

class Merchant(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        facing: Direction = Direction.DOWN,
        max_tiles: int = 2, # 這個是 enemy 的視力
    ) -> None:
        super().__init__(x, y, game_manager)
        
        self.animation = Sprite("character/nthu.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        self.animation.update_pos(self.position)
        
        self.facing = facing
        self.max_tiles = max_tiles
        self.detected = False
        self.alert_icon = Sprite("exclamation.png", (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2))
        self.los_direction = facing

    @override
    def update(self, dt: float) -> None:
        self._has_los_to_player()
        self.animation.update_pos(self.position)
        if self.detected:
            self.alert_icon.update_pos(Position(self.position.x + GameSettings.TILE_SIZE//4, self.position.y - GameSettings.TILE_SIZE//2))

    @override
    def draw(self, screen: pygame.Surface, camera):
        self.animation.draw(screen, camera)
        if self.detected:
            self.alert_icon.draw(screen, camera)

    def _get_los_rect(self) -> pygame.Rect | None:
        '''
        TODO: Create hitbox to detect line of sight of the enemies towards the player
        '''
        if self.max_tiles is None: # 理論上，視力不應該是 None
            return None
            
        tile_size = GameSettings.TILE_SIZE
        dist = self.max_tiles * tile_size # 把視力乘上格子的大小
        x, y = self.position.x, self.position.y
        
        # Rect(left, top, width, height)
        if self.los_direction == Direction.UP:
            return pygame.Rect(x, y - dist, tile_size, dist)
        elif self.los_direction == Direction.DOWN:
            return pygame.Rect(x, y + tile_size, tile_size, dist)
        elif self.los_direction == Direction.LEFT:
            return pygame.Rect(x - dist, y, dist, tile_size)
        elif self.los_direction == Direction.RIGHT:
            return pygame.Rect(x + tile_size, y, dist, tile_size)
            
        return None

    def _has_los_to_player(self) -> None:
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return
        los_rect = self._get_los_rect()
        if los_rect is None:
            self.detected = False
            return
        '''
        TODO: Implement line of sight detection
        If it's detected, set self.detected to True
        '''
        player_rect = player.animation.rect # 應該直接拿 animation 的就好吧？我又沒有要預測，幹嘛手搓出來
        
        if los_rect.colliderect(player_rect):
            self.detected = True
        else:
            self.detected = False

    def to_dict(self) -> dict:
        return {
            "x": self.position.x // GameSettings.TILE_SIZE,
            "y": self.position.y // GameSettings.TILE_SIZE,
            "facing": self.facing.value,
            "max_tiles": self.max_tiles
        }

    @classmethod
    def from_dict(cls, data: dict, game_manager: GameManager) -> "Merchant":
        return cls(
            x=data["x"] * GameSettings.TILE_SIZE,
            y=data["y"] * GameSettings.TILE_SIZE,
            game_manager=game_manager,
            facing=Direction[data.get("facing", "DOWN")],
            max_tiles=data.get("max_tiles", 2)
        )