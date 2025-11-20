"""
現在這裡掌管整個設定頁面
退出鈕、checkbox、slider 等
"""

'''
[TODO HACKATHON 5]
Try to mimic the menu_scene.py or game_scene.py to create this new scene
'''

import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button, Checkbox, Slider
from src.core.services import scene_manager, sound_manager, input_manager
from typing import override
import sys
import os

class SettingScene(Scene):
    # Background Image
    background: BackgroundSprite
    # Buttons
    back_button: Button
    #checkboxs
    trash_checkbox: Checkbox
    shutdown_button: Button # 其實我本來想直接用 OS 把電腦關機，想想還是算了
    #sliders
    volume_slider: Slider

    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("UI/raw/UI_Flat_Frame03a.png")

        # Texts
        self.font = pg.font.SysFont("Arial", 24, bold=True) # 字體
        self.txt_nothing = self.font.render("Obviously, nothing happened :D", True, (255, 255, 255))
        self.txt_bar_hint = self.font.render("Drag to shut down your computer", True, (255, 255, 255))
        self.txt_do_not_press = self.font.render("DO NOT PRESS", True, (255, 255, 255))

        # 找中央
        center_x = GameSettings.SCREEN_WIDTH // 2
        start_y = GameSettings.SCREEN_HEIGHT // 3

        # buttons
        self.back_button = Button(
            img_path = "UI/button_x.png", 
            img_hovered_path = "UI/button_x_hover.png", 
            x = GameSettings.SCREEN_WIDTH // 8 - 100, 
            y = GameSettings.SCREEN_HEIGHT * 3 // 4,
            width = 100, height = 100,
            on_click = lambda: scene_manager.change_scene("menu")
        )

        self.shutdown_button = Button(
            img_path = "UI/raw/shut_down_button.jpg", 
            img_hovered_path = "UI/raw/shut_down_button_hover.jpg", 
            x = center_x // 4, 
            y = int(start_y * 1.5),
            width = 100, height = 100,
            on_click = self.shutdown_game
        )

        # checkboxs
        self.trash_checkbox = Checkbox(
            x = center_x // 4, # 左邊 1/8
            y = start_y // 2, # 上面 1/4
            size = 64,
            img_checked = "UI/raw/UI_Flat_ButtonCheck01a.png",
            img_unchecked = "UI/raw/UI_Flat_ButtonCross01a.png",
            click_sound = "bababoy.wav", 
            initial_state = True
        )

        # sliders
        self.volume_slider = Slider(
            x = center_x // 4,
            y = start_y * 1.2,
            w = 300,
            h = 20,
            img_bar = "UI/raw/UI_Flat_BarFill01f.png",
            img_knob = "UI/raw/doge.png",
            initial_value = GameSettings.AUDIO_VOLUME
        )

    def shutdown_game(self):
        sound_manager.play_sound("drop.wav")
        # 有一說一我根本沒看懂下面的語法
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

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        pass

    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
        if input_manager.key_pressed(pg.K_SPACE):
            scene_manager.change_scene("game")
            return
        self.back_button.update(dt)

        self.trash_checkbox.update(dt)
        self.volume_slider.update(dt)
        self.shutdown_button.update(dt)

        # 音量
        current_vol = self.volume_slider.get_value()
        GameSettings.AUDIO_VOLUME = current_vol
        if sound_manager.current_bgm:
            sound_manager.current_bgm.set_volume(current_vol)

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        self.back_button.draw(screen)
        self.shutdown_button.draw(screen)

        self.trash_checkbox.draw(screen)
        self.volume_slider.draw(screen)

        # Obviously, nothing happened :D
        tcb_rect = self.trash_checkbox.rect
        txt_tcb_x = tcb_rect.right + 20
        txt_tcb_y = tcb_rect.centery - self.txt_nothing.get_height() // 2
        screen.blit(self.txt_nothing, (txt_tcb_x, txt_tcb_y))

        # Drag to shut down your computer
        sl_rect = self.volume_slider.rect_bar
        txt_sl_x = sl_rect.centerx - self.txt_bar_hint.get_width() // 2
        txt_sl_y = sl_rect.top - 40
        screen.blit(self.txt_bar_hint, (txt_sl_x, txt_sl_y))

        # DO NOT PRESS
        dnp_rect = self.shutdown_button.hitbox
        txt_dnp_x = dnp_rect.right + 20
        txt_dnp_y = dnp_rect.centery - self.txt_do_not_press.get_height() // 2
        screen.blit(self.txt_do_not_press, (txt_dnp_x, txt_dnp_y))
