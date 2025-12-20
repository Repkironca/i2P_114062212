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
        
        for i, msg in enumerate(self.messages):
            txt_surf = self.font.render(msg, True, (255, 255, 255))
            screen.blit(txt_surf, (self.rect.left + 10, start_y + i * line_height))

class BattleScene(Scene):
    def __init__(self, enemy: EnemyTrainer):
        super().__init__()

        self.game_manager = enemy.game_manager

        self.enemy = enemy
        self.enemy_type = random.choice(["P.H. Chou", "tp6ru4z", "Bill Louis"])
        self.is_evolved = False

        img_path = None
        if self.enemy_type == "P.H. Chou":
            img_path = "character/phchou.jpg" 
        elif self.enemy_type == "tp6ru4z":
            img_path = "character/tp6ru4z.png"
        elif self.enemy_type == "Bill Louis":
            img_path = "character/Bill_Louis.png"

        raw_img = resource_manager.get_image(img_path) 
        if self.enemy_type == "P.H. Chou":
            self.enemy_img = pg.transform.scale(raw_img, (403, 269))
        elif self.enemy_type == "tp6ru4z":
            self.enemy_img = pg.transform.scale(raw_img, (269, 269))
        elif self.enemy_type == "Bill Louis":
            self.enemy_img = pg.transform.scale(raw_img, (350, 269))


        self.player_max_hp = 100
        self.player_hp = 100
        
        self.enemy_max_hp = random.randint(50, 150) # 血量取 50 到 150 隨便一個數字
        self.enemy_hp = self.enemy_max_hp
        self.is_battle_over = False
        
        self.font = pg.font.SysFont("Arial", 22, bold=True)
        
        # 聊天室
        log_w = 850 # 你知盪這個數字我改多久才抓到最佳解嗎 ==
        log_h = 300
        log_x = (GameSettings.SCREEN_WIDTH - log_w) // 6
        log_y = 150
        self.logger = BattleLogger(log_x, log_y, log_w, log_h, self.font)
        
        self.logger.log(f"Encountered {self.enemy_type}!")
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
        
        # Evolute Him 按鈕
        self.evolute_button = Button(
            img_path = "UI/raw/UI_Flat_Button01a_3.png",
            img_hovered_path = None,
            x = 10, y = 10, # 左上角
            width = 150, height = 50,
            on_click = self.action_evolute
        )

        self.buttons = [
            (self.attack_button, "Attack"),
            (self.roulette_button, "Russian Roulette"),
            (self.daydream_button, "Daydream"),
            (self.item_button, "Item"),
            (self.run_button, "Run"),
        ]

        # 這個是進階攻擊選單
        self.show_attack_menu = False
        
        # 按鈕位置設定，置中顯示在畫面上方
        atk_w = 350
        atk_h = 50
        atk_start_y = GameSettings.SCREEN_HEIGHT // 2 - 150
        atk_cx = (GameSettings.SCREEN_WIDTH - atk_w) // 2
        
        self.btn_survey = Button(
            img_path = "UI/raw/UI_Flat_Button01a_3.png",
            img_hovered_path = None,
            x = atk_cx, y = atk_start_y,
            width = atk_w, height = atk_h,
            on_click = lambda: self.specific_attack("Course Evaluation Survey")
        )

        self.btn_lake = Button(
            img_path = "UI/raw/UI_Flat_Button01a_3.png",
            img_hovered_path = None,
            x = atk_cx, y = atk_start_y + 60,
            width = atk_w, height = atk_h,
            on_click = lambda: self.specific_attack("Throw Him Into Lake Success")
        )

        self.btn_cheat = Button(
            img_path = "UI/raw/UI_Flat_Button01a_3.png",
            img_hovered_path = None,
            x = atk_cx, y = atk_start_y + 120,
            width = atk_w, height = atk_h,
            on_click = lambda: self.specific_attack("Ask for CheatGPT in Midterm Exam")
        )
        
        self.attack_menu_buttons = [
            (self.btn_survey, "Course Evaluation Survey"),
            (self.btn_lake, "Throw Him Into Lake Success"),
            (self.btn_cheat, "Ask for CheatGPT in Midterm Exam")
        ]

        # 背包
        self.show_bag_menu = False
        self.bag_item_buttons = [] # 只有可以使用的物品會出現這個按鈕
        
        # 記錄一些奇怪的 Buff
        self.strength_buff = False # 下次攻擊 * 2.5
        self.defense_buff = False  # 下次受傷 * 0.25

    # 進化
    def action_evolute(self):
        if self.is_battle_over: return
        if self.is_evolved:
            self.logger.log(f"{self.enemy_type} is already evolved!")
            return

        self.is_evolved = True
        self.enemy_hp *= 2
        self.enemy_max_hp *= 2
        
        img_path = None
        if self.enemy_type == "P.H. Chou":
            img_path = "character/big_phchou.jpg"
        elif self.enemy_type == "tp6ru4z":
            img_path = "character/big_tp6ru4z.png"
        elif self.enemy_type == "Bill Louis":
            img_path = "character/big_Bill_Louis.png"
            
        raw_img = resource_manager.get_image(img_path)
        if self.enemy_type == "P.H. Chou":
            self.enemy_img = pg.transform.scale(raw_img, (348, 269))
        elif self.enemy_type == "tp6ru4z":
            self.enemy_img = pg.transform.scale(raw_img, (201, 269))
        elif self.enemy_type == "Bill Louis":
            self.enemy_img = pg.transform.scale(raw_img, (269, 269))

        self.logger.log(f"{self.enemy_type} has EVOLVED! Stats doubled!")
        sound_manager.play_sound("gugugaga_2.mp3")

    def attack(self):
        if self.is_battle_over: return
        self.show_attack_menu = True
        self.show_bag_menu = False

    def specific_attack(self, attack_name: str):
        if self.is_battle_over: return
        self.show_attack_menu = False
        
        base_dmg = random.randint(15, 30)
        multiplier = 1.0
        if self.strength_buff:
            multiplier = 2.5
            self.strength_buff = False
        
        if self.enemy_type == "P.H. Chou":
            if attack_name == "Course Evaluation Survey": multiplier = 1.5
            elif attack_name == "Ask for CheatGPT in Midterm Exam": multiplier = 0.5
            
        elif self.enemy_type == "tp6ru4z":
            if attack_name == "Throw Him Into Lake Success": multiplier = 1.5
            elif attack_name == "Course Evaluation Survey": multiplier = 0.5
            
        elif self.enemy_type == "Bill Louis":
            if attack_name == "Ask for CheatGPT in Midterm Exam": multiplier = 1.5
            elif attack_name == "Throw Him Into Lake Success": multiplier = 0.5
            
        final_dmg = int(base_dmg * multiplier)
        extra_dmg = final_dmg - base_dmg # 少取一次整數免得壞掉，嘻嘻嘻嘻嘻
        
        self.enemy_hp -= final_dmg
        if self.enemy_type == "P.H. Chou":
            if attack_name == "Course Evaluation Survey":
                self.logger.log(f"You gave a negative feedback in course evalution survey!")
                self.logger.log(f"P.H. Chou is crowded! dealt {base_dmg} + {extra_dmg} damages!")
            elif attack_name == "Throw Him Into Lake Success":
                self.logger.log("You throw him into Lake Success!")
                self.logger.log(f"He just swim in the pool happily. Dealt {base_dmg} + {extra_dmg} damages!")            
            else:
                self.logger.log("You choose to ask for CheatGPT in Midterm Exam!")
                self.logger.log(f"P.H. Chou didn't notice it since he didn't come to lab. dealt {base_dmg} + {extra_dmg} damages!")               
        elif self.enemy_type == "tp6ru4z":
            if attack_name == "Throw Him Into Lake Success":
                self.logger.log("You throw the academic excellence award owner into Lake Success!")
                self.logger.log(f"Ewww, the water doesn't smell good. Dealt {base_dmg} + {extra_dmg} damages!")
            elif attack_name == "Course Evaluation Survey":
                self.logger.log("You gave a negative feedback in course evalution survey!")
                self.logger.log(f"While he's neither a professor nor a TA. Dealt {base_dmg} + {extra_dmg} damages!")              
            else:
                self.logger.log("You choose to ask for CheatGPT in Midterm Exam")
                self.logger.log(f"He always got 10/10 on every lab, so it's impossible for you to beat him. Dealt {base_dmg} + {extra_dmg} damages!")
        elif self.enemy_type == "Bill Louis":
            if attack_name == "Ask for CheatGPT in Midterm Exam":
                self.logger.log("You choose to ask for CheatGPT in Midterm Exam")
                self.logger.log(f"This is a real headache for him. Dealt {base_dmg} + {extra_dmg} damages!")
            elif attack_name == "Throw Him Into Lake Success":
                self.logger.log("You throw him into Lake Success!")
                self.logger.log(f"It seems that he doesn't care about it. Dealt {base_dmg} + {extra_dmg} damages!")                
            else:
                self.logger.log("You gave a negative feedback in course evalution survey!")
                self.logger.log(f"While obviously he's not the one to be blamed. Dealt {base_dmg} + {extra_dmg} damages!") 

        sound_manager.play_sound("bonk.mp3")
        
        if self.check_battle_end(): return
        else: self.enemy_turn()

    def roulette(self):
        if self.is_battle_over: return
        self.show_attack_menu = False
        
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
        self.show_attack_menu = False
        
        sound_manager.play_sound("daydream.wav")
        self.logger.log("You daydreamed... Nothing happened")
        if self.check_battle_end(): return
        else: self.enemy_turn()

    def use_item(self):
        if self.is_battle_over: return
        self.show_attack_menu = False
        self.show_bag_menu = not self.show_bag_menu
        self._init_bag_buttons()

    # 初始化能使用的 Items 的按鈕
    def _init_bag_buttons(self):
        self.bag_item_buttons = []
        bag = self.game_manager.bag
        start_x = (GameSettings.SCREEN_WIDTH // 2) - 150
        start_y = 150
        line_height = 50
        
        if not bag.items:
            return

        for i, item in enumerate(bag.items):
            item_name = item['name']
            if item_name in ["Heal potion", "Strength Potion", "Defense Potion"]:
                btn = Button(
                    img_path="UI/raw/UI_Flat_Button01a_3.png",
                    img_hovered_path=None,
                    x=start_x + 300,
                    y=start_y + i * line_height - 10,
                    width=80, height=40,
                    on_click=lambda idx=i, name=item_name: self._use_bag_item(idx, name)
                )
                self.bag_item_buttons.append((btn, "Use"))
            
    # 使用背包物品
    def _use_bag_item(self, index: int, name: str):
        bag = self.game_manager.bag
        if index >= len(bag.items): return
        
        item = bag.items[index]
        
        if name == "Heal potion":
            recover = 50
            self.player_hp = min(self.player_max_hp, self.player_hp + recover)
            self.logger.log(f"Used Heal potion. Recovered {recover} HP!")
            
        elif name == "Strength Potion":
            self.strength_buff = True
            self.logger.log("Used Strength Potion! Next attack damage x2.5!")
            
        elif name == "Defense Potion":
            self.defense_buff = True
            self.logger.log("Used Defense Potion! Next damage taken x0.25!")

        # 還有剩的話就 -1，沒剩的話整個踢出去，等等 update 就不見了
        if item['count'] > 1:
            item['count'] -= 1
        else:
            bag.items.pop(index)
            
        sound_manager.play_sound("eating.wav")
        self.show_bag_menu = False
        self.enemy_turn()

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
        enemy_dmg = 0
        dialogue = "..."
        
        if self.enemy_type == "P.H. Chou":
            chance = random.random()
            if chance < 0.333:
                enemy_dmg = random.randint(10, 25)
                dialogue = "Aeeey we'll have a pop quiz"
            elif chance < 0.666:
                enemy_dmg = random.randint(10, 25)
                dialogue = "Mary had a little lamb!"
            else:
                enemy_dmg = random.randint(10, 25)
                dialogue = "Ch.16 is functions while ch.12 is recursion"

        elif self.enemy_type == "tp6ru4z":
            chance = random.random()
            if chance < 0.333:
                enemy_dmg = random.randint(99999, 100000)
                dialogue = "\"I'm about to fail i2P\", emotional damage"
            else:
                enemy_dmg = random.randint(10, 25)
                dialogue = "Kabi Kabi" # [填空]

        elif self.enemy_type == "Bill Louis":
            chance = random.random()
            if chance < 0.2:
                enemy_dmg = random.randint(30, 50)
                dialogue = "He gave you 0 points on checkpoint.3"
            elif chance < 0.6:
                enemy_dmg = 0
                dialogue = "Oops, he forget the English of he's skill name"
            else:
                enemy_dmg = random.randint(10, 25)
                dialogue = "He designed a lab problem that no one knows the answer"

        multiplier = 1.0
        if self.defense_buff:
            multiplier = 0.25
            self.defense_buff = False

        self.player_hp -= int(enemy_dmg * multiplier)
        self.logger.log(f"{dialogue}! took {enemy_dmg}*{multiplier}={int(enemy_dmg * multiplier)} damage from {self.enemy_type}")
        
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

        # 如果選單打開，更新選單按鈕
        if self.show_attack_menu:
            for btn, _ in self.attack_menu_buttons:
                btn.update(dt)

        # 或是更新背包裡面的按鈕
        elif self.show_bag_menu:
            for btn, _ in self.bag_item_buttons:
                btn.update(dt)
        else:
            # 否則更新原本的按鈕
            for btn, _ in self.buttons: # 後面只是一個完全不重要的提示字
                btn.update(dt)

            # 靠北我剛剛這裡多加一個 tab 花了十分鐘 debug
            self.evolute_button.update(dt)

    @override
    def draw(self, screen: pg.Surface):
        screen.fill((20, 160, 190))
        self.logger.draw(screen)

        
        # enemy
        img_rect = self.enemy_img.get_rect(center=(GameSettings.SCREEN_WIDTH * 7 // 8, 140))
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

        # Evolute Him 按鈕
        self.evolute_button.draw(screen)
        evo_text = self.font.render("Evolute Him", True, (0, 0, 0)) # 用黑色字
        screen.blit(evo_text, (self.evolute_button.hitbox.centerx - evo_text.get_width()//2, self.evolute_button.hitbox.centery - evo_text.get_height()//2))

        # 攻擊選單 Overlay
        if self.show_attack_menu:
            s = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
            s.fill((0, 0, 0, 150))
            screen.blit(s, (0, 0))
            
            for btn, button_name in self.attack_menu_buttons:
                btn.draw(screen)
                lbl_surf = self.font.render(button_name, True, (0, 0, 0))
                screen.blit(lbl_surf, (btn.hitbox.centerx - lbl_surf.get_width()//2, btn.hitbox.centery - lbl_surf.get_height()//2))

        # 背包選單 Overlay
        if self.show_bag_menu:
            s = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
            s.fill((0, 0, 0, 150))
            screen.blit(s, (0, 0))
            
            title = self.font.render("--- Items in Bag ---", True, (255, 255, 0))
            screen.blit(title, (GameSettings.SCREEN_WIDTH // 2 - 100, 100))
            
            bag = self.game_manager.bag
            start_x = (GameSettings.SCREEN_WIDTH // 2) - 150
            start_y = 150
            line_height = 50
            
            if not bag.items:
                empty = self.font.render("How poor are you? Your Bag is EMPTY!!!", True, (200, 200, 200))
                screen.blit(empty, (start_x, start_y))
            else:
                for i, item in enumerate(bag.items):
                    text = f"{item['name']} x {item['count']}"
                    txt_surf = self.font.render(text, True, (255, 255, 255))
                    screen.blit(txt_surf, (start_x, start_y + i * line_height))
            
            # 畫 Use 按鈕
            for btn, label in self.bag_item_buttons:
                btn.draw(screen)
                l_surf = self.font.render(label, True, (0, 0, 0))
                screen.blit(l_surf, (btn.hitbox.centerx - l_surf.get_width()//2, btn.hitbox.centery - l_surf.get_height()//2))