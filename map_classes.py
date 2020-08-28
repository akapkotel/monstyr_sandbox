#!/usr/bin/env python
from __future__ import annotations


from typing import Set, Optional, Callable, Union, Tuple, List
from arcade import (
    Sprite, SpriteList, SpriteSolidColor as ArcadeSpriteSolidColor, draw_text
)
from arcade.color import WHITE

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
        print(f'{self} was dragged to {x, y}')
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


class UiPanel(Visible, CursorInteractive, SpriteSolidColor):

    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 color: Color,
                 visible: bool = True,
                 active: bool = True,
                 parent: Hierarchical = None):
        Visible.__init__(self, visible)
        CursorInteractive.__init__(self, active, parent=parent)
        SpriteSolidColor.__init__(self, x, y, width, height, color)


class UiText(Visible, CursorInteractive, SpriteSolidColor):

    def __init__(self,
                 text: str,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 color: Color,
                 visible: bool = True,
                 active: bool = True,
                 parent: Hierarchical = None):
        Visible.__init__(self, visible)
        CursorInteractive.__init__(self, active, parent=parent)
        SpriteSolidColor.__init__(self, x, y, width, height, color)
        self.text = text

    def draw(self):
        super().draw()
        draw_text(self.text, self.center_x, self.center_y, WHITE, self.height)


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
        texture = f'ui/{text.lower()} button.png'
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
        """..."""
        self.location: Location = location
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


class MapTextLabel(UiText):

    def __init__(self,
                 text: str,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 visible: bool = True,
                 active: bool = True,
                 parent: Hierarchical = None):
        UiText.__init__(self, text, x, y, width, height, ALPHA, visible,
                        active, parent)


class UiSpriteList(SpriteList):
    """
    Wrapper for SpriteLists containing only UiPanels and Buttons used to
    cheaply identify them in on_draw() to call their draw() methods.
    """
