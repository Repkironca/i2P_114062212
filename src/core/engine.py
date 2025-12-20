import pygame as pg
import sys

from src.utils import GameSettings, Logger
from .services import scene_manager, input_manager

from src.scenes.menu_scene import MenuScene
from src.scenes.game_scene import GameScene
from src.scenes.setting_scene import SettingScene

class Engine:

    screen: pg.Surface              # Screen Display of the Game
    clock: pg.time.Clock            # Clock for FPS control
    running: bool                   # Running state of the game

    def __init__(self):
        Logger.info("Initializing Engine")

        pg.init()

        self.screen = pg.display.set_mode((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True

        pg.display.set_caption(GameSettings.TITLE)

        scene_manager.register_scene("menu", MenuScene())
        scene_manager.register_scene("game", GameScene())
        '''
        [TODO HACKATHON 5]
        Register the setting scene here
        '''
        scene_manager.register_scene("setting_menu", SettingScene())
        scene_manager.change_scene("menu")

    def run(self):
        Logger.info("Running the Game Loop ...")

        while self.running:
            dt = self.clock.tick(GameSettings.FPS) / 1000.0

            # 每一幀開始時，重置 InputManager 的單次點擊狀態
            input_manager.reset()
            events = pg.event.get()
            
            for event in events:
                # 處理視窗關閉
                if event.type == pg.QUIT:
                    self.running = False
                
                # 分發事件給 Input Manager
                input_manager.handle_events(event)

                # 分發事件給目前的 Scene (讓 ChatBox 接收文字輸入)
                if scene_manager._current_scene:
                    if hasattr(scene_manager._current_scene, "handle_event"):
                        scene_manager._current_scene.handle_event(event)

            self.update(dt)
            self.render()

        pg.quit()
        sys.exit()

    def update(self, dt: float):
        scene_manager.update(dt)

    def render(self):
        self.screen.fill((0, 0, 0))     # Make sure the display is cleared
        scene_manager.draw(self.screen) # Draw the current scene
        pg.display.flip()               # Render the display