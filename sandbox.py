#!/usr/bin/env python

import arcade

from random import uniform
from arcade.color import GREEN, DARK_MOSS_GREEN
from functools import partial

from lords_manager import LordsManager
from map_classes import *
from functions import *
from classes import *


get_sprites_at_point = arcade.get_sprites_at_point


SCREEN_WIDTH, SCREEN_HEIGHT = get_screen_size()
SCREEN_TITLE = 'Monastyr Sandbox'
FULL_SCREEN = False
LOADING_VIEW = 'loading view'
SANDBOX_VIEW = 'sandbox view'
MENU_VIEW = 'menu view'


class Application(arcade.Window):
    """
    Main window. It handles basic, commonly-shared by all Views logic and
    only delegates some tasks to the Views methods and uses Views
    properties.
    """

    def __init__(self, width: int, height: int, title: str, language: str):
        super().__init__(width, height, title)
        self.language = language
        self.views = {
            LOADING_VIEW: LoadingScreen(),
            MENU_VIEW: Menu(),
            SANDBOX_VIEW: Sandbox()
        }
        # --- cursor-related ---
        self.cursor_position = (0, 0, 0, 0)
        self.cursor_pointed: Optional[CursorInteractive] = None
        self.cursor_dragged: Optional[CursorInteractive] = None

    def switch_view(self, view_name: str, loading: bool = False):
        """
        Wrapper allowing using LoadingScreen between Views.
        """
        if loading:
            self.show_view(LoadingScreen(view_name))
        else:
            view = self.views[view_name]
            self.show_view(view)

    def on_draw(self):
        """ Draw everything """
        self.clear()
        view = self._current_view
        view.on_draw()
        if hasattr(view, 'drawn'):
            drawn = view.drawn
            for spritelist in (s for s in drawn if isinstance(s, UiSpriteList)):
                for elem in spritelist:
                    elem.draw()

    def on_update(self, dt):
        """ Update everything """
        self._current_view.on_update(dt)
        if self._mouse_visible:
            self.update_cursor()

    def update_cursor(self):
        x, y, *_ = self.cursor_position
        pointed = self.get_pointed_sprite(x, y)
        self.update_mouse_pointed(pointed)

    def update_mouse_pointed(self, pointed: Optional[CursorInteractive]):
        if self.cursor_pointed not in (None, pointed):
            self.cursor_pointed.on_mouse_exit()
        if pointed is not None:
            pointed.on_mouse_enter()
        self.cursor_pointed = pointed

    def get_pointed_sprite(self, x, y) -> Optional[CursorInteractive]:
        # Since we have many spritelists which are drawn in some
        # hierarchical order, we must iterate over them catching
        # cursor-pointed elements in backward order: last draw, is first to
        # be mouse-pointed (it lies on the top)
        if (pointed_sprite := self.cursor_dragged) is None:
            for drawn in self._current_view.drawn[::-1]:
                if not (pointed_sprite := self.cursor_points(drawn, x, y)):
                    continue
                else:
                    break
            else:
                return
        return pointed_sprite if pointed_sprite.active else None

    @staticmethod
    def cursor_points(sprites: SpriteList, x, y) -> Optional[CursorInteractive]:
        # Since our Sprites can have 'children' e.g. Buttons, which should
        # be first to interact with cursor, we discard all parents and seek
        # for first child, which is pointed instead:
        if pointed := get_sprites_at_point((x, y), sprites):
            s: CursorInteractive
            for sprite in (s for s in pointed if not s.children):
                return sprite
        return None

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.cursor_position = x, y, dx, dy

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if (pointed := self.cursor_pointed) is not None:
            if button == arcade.MOUSE_BUTTON_LEFT:
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
        self.switch_view(MENU_VIEW)


class Sandbox(arcade.View):
    """Main view displaying actual map."""
    instance = None

    def __new__(cls, *args, **kwargs):
        if Sandbox.instance is None:
            return super().__new__(cls)
        else:
            return Sandbox.instance

    def __init__(self):
        super().__init__()

        self.manager = LordsManager()
        self.manager.load()

        self.map_icons_to_labels: Dict[int, MapIcon] = {}

        # --- arcade SpriteLists ---
        self.terrain = SpriteList(is_static=True)
        self.map_icons: SpriteList = self.create_map_icons_spritelist()
        self.map_labels: UiSpriteList = self.create_map_labels_spritelist()
        del self.map_icons_to_labels
        self.ui_elements: UiSpriteList = self.create_ui_elements_spritelist()

        # reference used to keep window alive when it is not drawn
        self.location_window = self.create_location_window()

        self.testing_ideas()  # TODO: discard this before release

        # to draw and update everything with one instruction in on_draw()
        # and on_update() methods:
        self.drawn = self.get_attributes_of_name('draw')
        self.updated = self.get_attributes_of_name('update')
        Sandbox.instance = self

    @remove_arcade_window_from_returned_value
    def get_attributes_of_name(self, name: str) -> List:
        return [attr for attr in self.__dict__.values() if hasattr(attr, name)]

    def create_map_icons_spritelist(self) -> SpriteList:
        locations = SpriteList(is_static=True)
        for location in self.manager.locations:
            map_icon = MapIcon(location, location.map_icon,
                               function_on_left_click=
                               partial(self.open_location_window, location))
            # used later to bind text map label to map icon:
            self.map_icons_to_labels[location.id] = map_icon
            locations.append(map_icon)
        return locations

    def create_map_labels_spritelist(self) -> UiSpriteList:
        map_labels = UiSpriteList(is_static=True)
        for location in self.manager.locations:
            x, y = location.position
            map_icon = self.map_icons_to_labels[location.id]
            label = MapTextLabel(location.name, x + 40, y - 10, 100, 20,
                                 map_icon=map_icon, active=False)
            map_labels.append(label)
        return map_labels

    def create_ui_elements_spritelist(self) -> UiSpriteList:
        ui = UiSpriteList(is_static=False)

        width = SCREEN_WIDTH // 5
        x = SCREEN_WIDTH - (width // 2)
        y = SCREEN_HEIGHT // 2
        right_panel = UiPanelFactory.new(x, y, width, SCREEN_HEIGHT, BLACK)

        function = partial(self.window.switch_view, MENU_VIEW)
        exit_button = Button('quit', x, 75, function, parent=right_panel)

        ui.extend([right_panel, exit_button])
        return ui

    def testing_ideas(self):
        pass

    def on_show_view(self):
        self.window.set_mouse_visible(True)
        self.window.background_color = DARK_MOSS_GREEN

    def on_update(self, delta_time: float):
        for obj in self.updated:
            obj.update()

    def on_draw(self):
        for obj in self.drawn:
            obj.draw()

    def create_location_window(self) -> Dict[str, Union[UiPanel, List[Union[TextField, Button]]]]:
        """
        All Ui elements of window are instantiated once at the beginning,
        to make opening the window by user faster. All elements are
        reusable and their values are dynamically changed, when user clicks
        on the MapIcon.
        There are two kind of Ui elements: static labels, and dynamic text
        fields which are filled each time, when user opens the window and
        updated with the proper values of Location attributes.
        """
        window, fields, buttons = None, [], []
        x, y = int(SCREEN_WIDTH // 2), int(SCREEN_HEIGHT // 2)
        width = int((SCREEN_WIDTH - 300) * 0.7)
        height = int(SCREEN_HEIGHT * 0.7)

        window = UiPanelFactory.new(x, y, width, height, DUTCH_WHITE)
        y = y - 50 + height // 2
        buttons.append(self.new_close_button(window, width, x, y))

        attributes = ['',
                      f'Location type:',
                      f'Owner:',
                      f'Faction:',
                      f'Population:',
                      f'Garrison:']

        for i, attr in enumerate(a for a in attributes):
            ix = x - (width / 2) + 50 if i else int(SCREEN_WIDTH // 2)
            field = TextField(ix, y, attr, text_size=20, parent=window)
            fields.append(field)
            y -= 50
        return {'window': window, 'fields': fields, 'buttons': buttons}

    def new_close_button(self, location_window, width, x, y) -> Button:
        x = x - 30 + (width // 2)
        function = partial(self.close_window, location_window)
        return Button('close', x, y + 20, function, parent=location_window)

    def open_location_window(self, location: Location):
        """
        Display window with Location detail when user clicks on it's MapIcon.
        """
        # to avoid instantiating fields each time, window is reopened,
        # we keep the TextField instances and other Ui elements cached:
        cached_window = self.location_window
        window = cached_window['window']
        fields: List[TextField] = cached_window['fields']
        buttons = cached_window['buttons']
        # and only fill their values with correct data from actual Location
        # instance:
        attributes = (
            location.name, location.type.value, location.owner.name,
            location.faction.value, location.population,
            location.soldiers
        )
        for i, attr in enumerate(a for a in attributes):
            if attr:
                fields[i].value_text = str(attr)
            else:
                fields[i].value_text = '0' if isinstance(attr, int) else ''

        # start updating and drawing window on the screen:
        self.ui_elements.extend([window] + fields + buttons)

    def close_window(self, window: UiPanel):
        for child in window.children:
            self.ui_elements.remove(child)
        self.ui_elements.remove(window)


class Menu(arcade.View):

    def __init__(self):
        super().__init__()
        self.buttons = SpriteList(is_static=True)

        names = ['Quit', 'Lords manager', 'Open map']
        functions = [
            self.window.close,
            partial(self.window.switch_view, MENU_VIEW, True),
            partial(self.window.switch_view, SANDBOX_VIEW, True)
        ]

        width = SCREEN_WIDTH//2
        for i, name in enumerate(names):
            self.buttons.append(
                Button(no_spaces(names[i]), width, 300 * (i + 1), functions[i])
            )

        self.drawn = self.updated = [self.buttons]

    def on_show_view(self):
        self.window.set_mouse_visible(True)
        self.window.background_color = arcade.color.AIR_FORCE_BLUE

    def on_draw(self):
        """ Draw everything """
        self.window.clear()
        self.buttons.draw()

    def on_update(self, dt):
        """ Update everything """
        self.buttons.update()


class LoadingScreen(arcade.View):
    progress = 0

    def __init__(self, next_view: str = MENU_VIEW):
        super().__init__()
        self.next_view = next_view

    def on_show_view(self):
        self.progress = 0
        self.window.set_mouse_visible(False)
        self.window.background_color = arcade.color.BLACK

    def on_update(self, delta_time: float):
        self.progress += uniform(0.3, 3.0)
        if self.progress > 100:
            self.window.switch_view(self.next_view)

    def on_draw(self):
        self.window.clear()
        l = 100
        r = l + (SCREEN_WIDTH - 200)
        t = SCREEN_HEIGHT // 2 + 15
        b = t - 30
        arcade.draw_lrtb_rectangle_outline(l, r, t, b, arcade.color.WHITE)
        r = l + (SCREEN_WIDTH - 200) * (self.progress / 99)
        arcade.draw_lrtb_rectangle_filled(l, r, t - 1, b + 1, GREEN)
        text = f'Loading progress: {int(self.progress)}'
        arcade.draw_text(text, l, t + 20, arcade.color.WHITE, 20)


if __name__ == "__main__":
    language = get_current_language()
    application = Application(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, language)
    application.center_window()
    application.switch_view(MENU_VIEW, loading=True)
    arcade.run()
