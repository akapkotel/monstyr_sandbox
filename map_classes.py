#!/usr/bin/env python
from __future__ import annotations

from arcade import Sprite, SpriteSolidColor as ArcadeSpriteSolidColor
from typing import Set, Optional, Callable, Union, Tuple, List


# typing aliases:
Color = Union[Tuple[int, int, int, int], Tuple[int, int, int], List[int]]


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
        self._visible = value


class Hierarchical:
    """
    Interface offering hierarchical order of elements, e.g. one element can
    have 'children' and/or 'parent' object. Hierarchy allows user to work
    with an objects and theirs children-objects simultaneously.
    """

    def __init__(self, parent: Optional[VHO] = None):
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
            self._parent.remove_child(self)
        self._parent = parent

    @property
    def children(self):
        return self._children

    def add_child(self, child: VHO):
        if self._children is None:
            self._children = set()
        self._children.add(child)

    def remove_child(self, child: VHO):
        self._children.discard(child)


VHO = Hierarchical


class CursorInteractive:
    """Interface for all objects which are clickable etc."""

    def __init__(self,
                 active: bool = True,
                 can_be_dragged: bool = False,
                 function_on_left_click: Optional[Callable] = None,
                 function_on_right_click: Optional[Callable] = None):
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

    def on_mouse_exit(self):
        if self.pointed:
            print(f'Mouse left {self}')
            self.pointed = False

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


class SpriteSolidColor(Visible, Hierarchical, ArcadeSpriteSolidColor):
    """Wrapper to instantiate SpriteSolidColor with position."""

    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 color: Color,
                 visible: bool = True,
                 parent: Hierarchical = None):
        Visible.__init__(self, visible)
        Hierarchical.__init__(self, parent)
        ArcadeSpriteSolidColor.__init__(self, width, height, color)
        self.position = x, y


class Button(SpriteSolidColor, CursorInteractive):

    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 color: Color,
                 function: Optional[Callable] = None,
                 visible: bool = True,
                 parent: Hierarchical = None):
        SpriteSolidColor.__init__(self, x, y, width, height, color, visible, parent)
        CursorInteractive.__init__(self, can_be_dragged=True,
                                   function_on_left_click=function)

    def draw(self):
        super().draw()


class Map(Hierarchical, CursorInteractive, Sprite):
    """
    Class for all map Sprites representing Locations in the game-world.
    """
    pass
