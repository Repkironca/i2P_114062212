from __future__ import annotations
import pygame as pg

from src.sprites import Sprite
from src.core.services import input_manager
from src.utils import Logger
from typing import Callable, override
from .component import UIComponent

class Button(UIComponent):
    img_button: Sprite
    img_button_default: Sprite
    img_button_hover: Sprite
    hitbox: pg.Rect
    on_click: Callable[[], None] | None

    def __init__(
        self,
        img_path: str, img_hovered_path: str | None,
        x: int, y: int, width: int, height: int,
        on_click: Callable[[], None] | None = None
    ):
        self.img_button_default = Sprite(img_path, (width, height))
        self.hitbox = pg.Rect(x, y, width, height)
        '''
        [TODO HACKATHON 1][complete]
        Initialize the properties
        
        self.img_button_hover = ...
        self.img_button = ...       --> This is a reference for which image to render
        self.on_click = ...
        '''

        if img_hovered_path is not None: # 有正常路徑
            self.img_button_hover = Sprite(img_hovered_path, (width, height))
        else: # 我美術資源不足啦啦啦
            self.img_button_hover = Sprite(img_path, (width, height))
            factor = 1.1
            new_w = int(width * factor)
            new_h = int(height * factor)
            
            # 聽說這樣可以放大
            self.img_button_hover.image = pg.transform.scale(self.img_button_default.image, (new_w, new_h))
            self.img_button_hover.rect = self.img_button_hover.image.get_rect()

        self.img_button = self.img_button_default # Then why spliting it into two steps
        self.on_click = on_click


    @override
    def update(self, dt: float) -> None:
        '''
        [TODO HACKATHON 1]
        Check if the mouse cursor is colliding with the button, 
        1. If collide, draw the hover image
        2. If collide & clicked, call the on_click function
        
        if self.hitbox.collidepoint(input_manager.mouse_pos):
            ...
            if input_manager.mouse_pressed(1) and self.on_click is not None:
                ...
        else:
            ...
        '''
        if self.hitbox.collidepoint(input_manager.mouse_pos):
            self.img_button = self.img_button_hover # hovering
            if input_manager.mouse_pressed(1) and self.on_click is not None:
                self.on_click() # hovering + clicking # IT IS A FUNCTION, see line 14
        else:
            self.img_button = self.img_button_default
    
    @override
    def draw(self, screen: pg.Surface) -> None:
        '''
        [TODO HACKATHON 1]
        You might want to change this too
        It was "_ = screen.blit(self.img_button_image, self.hitbox)"
        '''
        # 中心對齊中心，因為我的 hover 可能是手搓的
        current_img = self.img_button.image
        img_rect = current_img.get_rect()
        img_rect.center = self.hitbox.center
        
        screen.blit(current_img, img_rect)


def main():
    import sys
    import os
    
    pg.init()

    WIDTH, HEIGHT = 800, 800
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption("Button Test")
    clock = pg.time.Clock()
    
    bg_color = (0, 0, 0)
    def on_button_click():
        nonlocal bg_color
        if bg_color == (0, 0, 0):
            bg_color = (255, 255, 255)
        else:
            bg_color = (0, 0, 0)
        
    button = Button(
        img_path="UI/button_play.png",
        img_hovered_path="UI/button_play_hover.png",
        x=WIDTH // 2 - 50,
        y=HEIGHT // 2 - 50,
        width=100,
        height=100,
        on_click=on_button_click
    )
    
    running = True
    dt = 0
    
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            input_manager.handle_events(event)
        
        dt = clock.tick(60) / 1000.0
        button.update(dt)
        
        input_manager.reset()
        
        _ = screen.fill(bg_color)
        
        button.draw(screen)
        
        pg.display.flip()
    
    pg.quit()


if __name__ == "__main__":
    main()
