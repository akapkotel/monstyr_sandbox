#!/usr/bin/env python
from __future__ import annotations

import arcade

from random import choice, randint
from typing import List, Tuple, Set, Dict, Union, Optional, Callable
from dataclasses import dataclass, field

from functions import print_return
from enums import *

RAGADAN = 'Ragada'


class Nobleman:
    """Base class for all noblemen in sandbox."""

    __slots__ = ['full_name', 'portrait', 'sex', 'age', '_spouse', '_siblings',
                 '_children', 'nationality', 'faction', 'title',
                 'church_title', 'abbey_rank', 'military_rank', 'liege',
                 '_vassals', '_fiefs', 'info']

    def __init__(self,
                 full_name: str = '',
                 age: int = 25,
                 nationality: str = '',
                 faction: Faction = Faction.neutral,
                 title: Title = Title.chevalier,
                 church_title: ChurchTitle = ChurchTitle.no_title,
                 abbey_rank: AbbeyRank = AbbeyRank.no_rank,
                 military_rank: MilitaryRank = MilitaryRank.no_rank,
                 liege: Optional[Nobleman] = None
                 ):
        self.full_name = full_name
        self.portrait = f'portraits/{full_name}.png'
        self.sex: Sex = Sex.woman if self.first_name.endswith('a') else Sex.man
        self.age = age
        self._spouse: Optional[Nobleman] = None
        self._siblings: Set[Nobleman] = set()
        self._children: Set[Nobleman] = set()
        self.nationality = nationality
        self.faction = faction
        self.title = title
        self.church_title = church_title
        self.abbey_rank = abbey_rank
        self.military_rank = military_rank
        self.liege = liege
        self._vassals = set()
        self._fiefs = set()
        self.info: List[str] = []

    def __repr__(self):
        return f'Nobleman: {self.title_and_name}'

    @property
    def spouse(self) -> Optional[Nobleman]:
        return self._spouse

    @spouse.setter
    def spouse(self, spouse: Nobleman):
        if spouse.sex != self.sex:  # Homophobic! ;)
            self._spouse = spouse
            spouse._spouse = self  # use protected attr to avoid circular call

    @property
    def siblings(self):
        return self._siblings

    @siblings.setter
    def siblings(self, *siblings: Nobleman):
        for sibling in siblings:
            self._siblings.add(sibling)
            sibling.siblings.add(self)

    @siblings.deleter
    def siblings(self):
        for sibling in self._siblings:
            sibling.siblings.discard(self)
        self._siblings.clear()

    @property
    def children(self) -> Set[Nobleman]:
        return self._children

    @children.setter
    def children(self, *children: Nobleman):
        for child in children:
            if self.age - child.age > 12:
                self._children.add(child)

    @property
    def vassals(self) -> Set[Nobleman]:
        return self._vassals

    def vassals_of_title(self, title: Title) -> Set[Nobleman]:
        return set(vassal for vassal in self.vassals if vassal.title is title)

    def add_vassals(self, *vassals: Nobleman):
        self._vassals.update(vassals)
        for vassal in vassals:
            vassal.liege = self

    @vassals.deleter
    def vassals(self):
        self._vassals.clear()

    @property
    def fiefs(self) -> Set[Location]:
        return self._fiefs

    def add_fiefs(self, *fiefs: Location):
        self._fiefs.update(fiefs)
        for fief in fiefs:
            fief.owner = self

    @fiefs.deleter
    def fiefs(self):
        self._fiefs.clear()

    @property
    def first_name(self) -> str:
        return self.full_name.split(' ')[0]

    @property
    def name(self) -> str:
        return self.full_name

    @property
    def family_name(self) -> str:
        return self.full_name.split(' ')[-1]

    @property
    def title_and_name(self) -> str:
        return f"{self.proper_title()} {self.full_name}"

    def proper_title(self) -> str:
        """
        Get str value of the highest title this Nobleman posses. For
        egzample, an ordinary 'chevalier' (lowest noble rank) can bear
        also a high military rank of 'colonel'. In such case, he would
        be often titled as 'colonel + his first_name' instead of 'chevalier +
        his first_name'. But most of times, the noblemen title is used.
        """
        titles = [t for t in (self.title, self.church_title, self.abbey_rank,
                              self.military_rank) if t is not None]
        highest = -1
        best_title = ''
        for title in titles:
            if (title_rank := title.hierarchy()[title]) > highest:
                highest = title_rank
                best_title = title.value
        return best_title

    def full_domain(self) -> Set[Location]:
        """
        Return all Locations this Noblemen posses, and all Locations
        of his vassals queried recursively.
        """
        return self.fiefs.union(v.full_domain() for v in self.vassals)

    def set_fiefs(self, *fiefs: Location):
        self.fiefs.update(fiefs)
        for location in fiefs:
            location.owner = self

    def get_fiefs_of_type(self, location_type: LocationType) -> Set[Location]:
        return set(fief for fief in self.fiefs if fief.type == location_type)

    def __gt__(self, other: Nobleman) -> bool:
        """Compare two Noblemen titles."""
        return self.hierarchy[self.title] > other.hierarchy[other.title]

    def __lt__(self, other: Nobleman) -> bool:
        """Compare two Noblemen titles."""
        return self.hierarchy[self.title] < other.hierarchy[other.title]

    @property
    def hierarchy(self) -> Dict:
        return self.title.hierarchy()


class Location:

    __slots__ = ['name', 'picture', 'position', 'type', 'owner', 'faction',
                 'population', 'soldiers', 'description']

    def __init__(self,
                 name: str = '',
                 picture: str = '',
                 position: tuple = (0, 0),
                 location_type: LocationType = LocationType.village,
                 owner: Optional[Nobleman] = None,
                 population: int = 0,
                 soldiers: int = 0
                 ):
        self.picture = picture
        self.name = name or location_type.value
        self.position = position
        self.type = location_type
        self.owner = owner
        self.faction = Faction.neutral if owner is None else owner.faction
        self.population = population
        self.soldiers = soldiers
        self.description = ''

    def __repr__(self):
        return f'{self.type.value} {self.name if self.name != self.type.value else ""}'

    @property
    def full_name(self):
        return self.__repr__()


class Sprite(arcade.Sprite):

    def __init__(self, visible: bool = True):
        self.visible = visible


class Counter:
    """
    Counter is a container for an int value, which allows increasing/decreasing
    value and returning it at the same time. You can assign the Counter value to
    some variable and increment it in one line of code instead of two.
    """

    def __init__(self, start: int = 0,
                 step: int = 1,
                 max: int = None,
                 increasing: bool = True):
        self.start = start
        self.max = max if increasing else -max
        self.value = start
        self.step = step
        self.increasing = increasing

    def __call__(self):
        """Return current value without changing it."""
        return self.value

    def next(self):
        """Change value by self.step and return increased/decreased value."""
        if self.max is None or abs(self.max) - abs(self.value):
            self.value += self.step if self.increasing else - self.step
            return self.value
        else:
            self.restart()
            return self.value

    def restart(self):
        """set value back to start value."""
        self.value = self.start

    def reverse(self):
        self.increasing = not self.increasing


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


class SpriteSolidColor(arcade.SpriteSolidColor):
    """Wrapper to instantiate SpriteSolidColor with position."""

    def __init__(self, x: int, y: int, width: int, height: int, color):
        super().__init__(width, height, color)
        self.position = x, y


class Button(SpriteSolidColor, CursorInteractive):

    def __init__(self, x: int, y: int, width: int, height: int, color, function: Optional[Callable] = None):
        super().__init__(x, y, width, height, color)
        CursorInteractive.__init__(self, can_be_dragged=True, function_on_left_click=function)

    def draw(self):
        super().draw()
