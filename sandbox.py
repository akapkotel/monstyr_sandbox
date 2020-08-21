#!/usr/bin/env python

import arcade
import random

from typing import List, Optional

from lords_manager import LordsManager
from functions import *
from classes import *
from enums import *


get_sprites_at_point = arcade.get_sprites_at_point


SCREEN_WIDTH, SCREEN_HEIGHT = get_screen_size()
SCREEN_TITLE = 'Monastyr Sandbox'
FULL_SCREEN = False
LOADING = 'loading view'
SANDBOX = 'sandbox view'


class Application(arcade.Window):
    """ Main window"""

    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.views = {LOADING: LoadingScreen(), SANDBOX: Sandbox()}
        self.show_view(self.views[LOADING])


class Sandbox(arcade.View):

    def __init__(self):
        super().__init__()

        self.lords = LordsManager()

        self.ui_elements = arcade.SpriteList(is_static=False)
        self.terrain = arcade.SpriteList(is_static=True)
        self.locations = arcade.SpriteList(is_static=True)

        # --- cursor-related ---
        self.cursor = (0, 0, 0, 0)
        self.cursor_pointed: Optional[CursorInteractive] = None
        self.cursor_dragged: Optional[CursorInteractive] = None

        self.testing_ideas()  # TODO: discard this before release

        # to draw and update everything with one instruction in on_draw() and on_update() methods:
        self.drawn = [attr for attr in self.__dict__.values() if hasattr(attr, 'draw')]
        self.updated = [attr for attr in self.__dict__.values() if hasattr(attr, 'draw')]

    def testing_ideas(self):
        for i in range(1, 3):
            for j in range(1, 3):
                function = self.window.close
                button = Button(i * 400, j * 400, 150, 50, arcade.color.WHITE)
                self.ui_elements.append(button)

    def on_show_view(self):
        self.window.set_mouse_visible(True)
        self.window.background_color = arcade.color.WINE

    def on_draw(self):
        """ Draw everything """
        self.window.clear()
        for obj in self.drawn:
            obj.draw()

    def on_update(self, dt):
        """ Update everything """
        for obj in self.updated:
            obj.update()
        self.update_cursor()

    def update_cursor(self):
        x, y, *_ = self.cursor
        pointed = self.get_pointed_sprite(x, y)
        self.update_mouse_pointed(pointed)

    def update_mouse_pointed(self, pointed: Optional[CursorInteractive]):
        try:
            pointed.on_mouse_enter()
        except AttributeError:
            if self.cursor_pointed is not pointed:
                self.cursor_pointed.on_mouse_exit()
        finally:
            self.cursor_pointed = pointed

    def get_pointed_sprite(self, x, y) -> Optional[CursorInteractive]:
        if (pointed_sprite := self.cursor_dragged) is None:
            if not (pointed_sprite := self.cursor_points(self.ui_elements, x, y)):
                if not (pointed_sprite := self.cursor_points(self.locations, x, y)):
                    if not (pointed_sprite := self.cursor_points(self.terrain, x, y)):
                        return
        return pointed_sprite if pointed_sprite.active else None

    @staticmethod
    def cursor_points(sprites: arcade.SpriteList, x, y) -> Optional[CursorInteractive]:
        return pointed[0] if (pointed := get_sprites_at_point((x, y), sprites)) else None

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.cursor = x, y, dx, dy

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        pointed = self.cursor_pointed
        if pointed is not None:
            pointed.on_mouse_press(button)
            if pointed.can_be_dragged:
                self.cursor_dragged = pointed

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        if self.cursor_dragged is not None:
            self.cursor_dragged.on_mouse_release(button)
        self.cursor_dragged = None

    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, _buttons: int, _modifiers: int):
        if (dragged := self.cursor_dragged) is not None and dragged.can_be_dragged:
            self.cursor_pointed.on_mouse_drag(x, y)

    def on_key_press(self, symbol: int, modifiers: int):
        self.window.show_view(self.window.views[LOADING])


class LoadingScreen(arcade.View):
    progress = 0

    def on_show_view(self):
        self.progress = 0
        self.window.set_mouse_visible(False)
        self.window.background_color = arcade.color.BLACK

    def on_update(self, delta_time: float):
        self.progress += random.uniform(0.1, 1.0)
        if self.progress > 100:
            sandbox = self.window.views[SANDBOX]
            self.window.show_view(sandbox)

    def on_draw(self):
        self.window.clear()
        l = 100
        r = l + (SCREEN_WIDTH - 200)
        t = SCREEN_HEIGHT // 2 + 15
        b = t - 30
        arcade.draw_lrtb_rectangle_outline(l, r, t, b, arcade.color.WHITE)
        r = l + (SCREEN_WIDTH - 200) * (self.progress / 99)
        arcade.draw_lrtb_rectangle_filled(l, r, t - 1, b + 1, arcade.color.GREEN)
        text = f'Loading progress: {int(self.progress)}'
        arcade.draw_text(text, l, t + 20, arcade.color.WHITE, 20)


if __name__ == "__main__":
    window = Application(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.center_window()
    loading = LoadingScreen()
    window.show_view(loading)
    arcade.run()
