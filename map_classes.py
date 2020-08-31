#!/usr/bin/env python
from __future__ import annotations


from typing import Set, Optional, Callable, Union, Tuple, List
from arcade import (
    Window, Sprite, SpriteList, SpriteSolidColor as ArcadeSpriteSolidColor,
    Texture, draw_text, draw_circle_outline, draw_ellipse_outline
)
from arcade.color import WHITE, BLACK, GREEN, DUTCH_WHITE

from classes import Location

# typing aliases:
Color = Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]]


ALPHA: Color = (0, 0, 0, 0)


class Visible:
    """
    Interface offering possibility to hide or reveal object.
    """

    def __init__(self, visible: bool = True):
        self._visible = visible

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool):
        self.visible = value


class Hierarchical:
    """
    Interface offering hierarchical order of elements, e.g. one element can
    have 'children' and/or 'parent' object. Hierarchy allows user to work
    with an objects and theirs children-objects simultaneously.
    """

    def __init__(self, parent: Optional[Hierarchical] = None):
        self._parent: Optional[Hierarchical] = parent
        self._children: Optional[Set] = None

        if parent is not None:
            parent.add_child(self)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent: Optional[Hierarchical]):
        if parent is None:
            self._parent.discard_child(self)
        self._parent = parent

    @property
    def children(self):
        return self._children

    def add_child(self, child: Hierarchical):
        if self._children is None:
            self._children = set()
        self._children.add(child)

    def discard_child(self, child: Hierarchical):
        self._children.discard(child)


class CursorInteractive(Hierarchical):
    """Interface for all objects which are clickable etc."""

    def __init__(self,
                 active: bool = True,
                 can_be_dragged: bool = False,
                 function_on_left_click: Optional[Callable] = None,
                 function_on_right_click: Optional[Callable] = None,
                 parent: Optional[Hierarchical] = None):
        Hierarchical.__init__(self, parent)
        self.active = active
        self.pointed = False
        self.dragged = False
        self.can_be_dragged = can_be_dragged
        self.function_on_left_click = function_on_left_click
        self.function_on_right_click = function_on_right_click

    def __repr__(self):
        return f'{self.__class__.__name__} id: {id(self)}'

    def on_mouse_enter(self):
        if not self.pointed:
            print(f'Mouse over {self}')
            self.pointed = True
            self._func_on_mouse_enter()

    def _func_on_mouse_enter(self):
        pass

    def on_mouse_exit(self):
        if self.pointed:
            print(f'Mouse left {self}')
            self.pointed = False
            self._func_on_mouse_exit()

    def _func_on_mouse_exit(self):
        pass

    def on_mouse_press(self, button: int):
        print(f'Mouse button {button} clicked on {self}')
        if self.function_on_left_click is not None:
            self.function_on_left_click()
        self.dragged = self.can_be_dragged

    def on_mouse_release(self, button: int):
        print(f'Released button {button} on {self}')
        self.dragged = False

    def on_mouse_drag(self, x: float = None, y: float = None):
        if x is not None:
            setattr(self, 'center_x', x)
        if y is not None:
            setattr(self, 'center_y', y)


class SpriteSolidColor(ArcadeSpriteSolidColor):
    """Wrapper to instantiate SpriteSolidColor with position."""

    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 color: Color):
        ArcadeSpriteSolidColor.__init__(self, width, height, color)
        self.position = x, y


class UiPanelFactory:
    """
    Return one of two types of UiPanel objects depending on the 'texture'
    param presence. Just call the UiPanelFactory.new() method with params You
    would normally pass to the __init__ of your target UiPanel class.
    """

    @staticmethod
    def new(x: int,
            y: int,
            width: int,
            height: int,
            color: Color = DUTCH_WHITE,
            texture: str = None,
            visible: bool = True,
            active: bool = True,
            parent: Hierarchical = None):
        if texture is None:
            return SimpleUiPanel(x, y, width, height, color, visible, active, parent)
        return TexturedUiPanel(x, y, width, height, texture, visible, active, parent)


class UiPanel(Visible, CursorInteractive):

    def __init__(self,
                 visible: bool = True,
                 active: bool = True,
                 parent: Hierarchical = None):
        Visible.__init__(self, visible)
        CursorInteractive.__init__(self, active, parent=parent)


class SimpleUiPanel(UiPanel, SpriteSolidColor):

    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 color: Color,
                 visible: bool = True,
                 active: bool = True,
                 parent: Hierarchical = None):
        UiPanel.__init__(self, visible, active, parent)
        SpriteSolidColor.__init__(self, x, y, width, height, color)


class TexturedUiPanel(UiPanel, Sprite):

    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 texture: str,
                 visible: bool = True,
                 active: bool = True,
                 parent: Hierarchical = None):
        UiPanel.__init__(self, visible, active, parent)
        Sprite.__init__(self, texture, x, y, width, height)


class UiText(Visible, CursorInteractive, SpriteSolidColor):

    def __init__(self,
                 text: str,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 text_color: Color = BLACK,
                 background_color: Color = ALPHA,
                 visible: bool = True,
                 active: bool = True,
                 parent: Hierarchical = None):
        Visible.__init__(self, visible)
        CursorInteractive.__init__(self, active, parent=parent)
        SpriteSolidColor.__init__(self, x, y, width, height, background_color)
        self.text = text
        self.text_color = text_color

    def draw(self):
        super().draw()
        draw_text(self.text, self.center_x, self.center_y, self.text_color, self.height)


class Button(Visible, CursorInteractive, Sprite):
    """
    Simple button using static Sprite, interacting with mouse-cursor and
    calling functions assigned to it. It can be a child of other Hierarchical
    object.
    """

    def __init__(self,
                 text: str,
                 x: int,
                 y: int,
                 function: Optional[Callable] = None,
                 visible: bool = True,
                 parent: Hierarchical = None):
        Visible.__init__(self, visible)
        CursorInteractive.__init__(self, can_be_dragged=True,
                                   function_on_left_click=function,
                                   parent=parent)
        texture = f'ui/{text.lower()}_button.png'
        Sprite.__init__(self, texture, center_x=x, center_y=y)
        self.text = text


class MapIcon(Visible, CursorInteractive, Sprite):
    """
    Class for all map Sprites representing Locations in the game-world.
    """

    def __init__(self,
                 location: Location,
                 map_texture: str,
                 visible: bool = True,
                 parent: Optional[Hierarchical] = None,
                 active: bool = True,
                 can_be_dragged: bool = False,
                 function_on_left_click: Optional[Callable] = None,
                 function_on_right_click: Optional[Callable] = None):
        self.location: Location = location
        self.map_label: Optional[MapTextLabel] = None
        self.map_indicator: Optional[MapIndicator] = None
        self.x, self.y = location.position
        Sprite.__init__(self, f'map_icons/{map_texture}', center_x=self.x,
                        center_y=self.y)
        Visible.__init__(self, visible)
        CursorInteractive.__init__(self, active,
                                   can_be_dragged,
                                   function_on_left_click,
                                   function_on_right_click,
                                   parent=parent)

    def on_mouse_press(self, button: int):
        print(f'Mouse button {button} clicked on {self}')
        if self.function_on_left_click is not None:
            self.function_on_left_click(self.location)
        self.dragged = self.can_be_dragged

    def _func_on_mouse_enter(self):
        self.map_label.text_color = GREEN
        self.create_map_indicator()

    def create_map_indicator(self):
        spritelist = self.map_label.sprite_lists[0]
        indicator = MapIndicator(*self.position, 60, 60, 60, ALPHA)
        self.map_indicator = indicator
        spritelist.append(indicator)

    def _func_on_mouse_exit(self):
        self.map_label.text_color = WHITE
        self.kill_map_indicator()

    def kill_map_indicator(self):
        spritelist = self.map_label.sprite_lists[0]
        spritelist.remove(self.map_indicator)
        self.map_indicator = None


class MapIndicator(SpriteSolidColor):
    """Draw circular indicator around mouse-pointed MapIcon on the map."""

    def __init__(self, x: int, y: int, radius: int, width: int, height: int, color: Color):
        super().__init__(x, y, width, height, color)
        self.radius = radius

    def draw(self):
        super().draw()
        x, y = self.position
        draw_ellipse_outline(x, y, 120, 95, GREEN)


class MapTextLabel(UiText):
    """Text label displayed near the MapIcon on the map."""

    def __init__(self,
                 text: str,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 text_color: Color = WHITE,
                 map_icon: Optional[MapIcon] = None,
                 visible: bool = True,
                 active: bool = True,
                 parent: Hierarchical = None):
        UiText.__init__(self, text, x, y, width, height, text_color,
                        visible=visible, active=active, parent=parent)
        self.map_icon: Optional[MapIcon] = map_icon
        if map_icon is not None:
            self.bind_to_map_icon()

    def bind_to_map_icon(self):
        self.map_icon.map_label = self


class UiSpriteList(SpriteList):
    """
    Wrapper for SpriteLists containing only UiPanels and Buttons used to
    cheaply identify them in on_draw() to call their draw() methods.
    """
