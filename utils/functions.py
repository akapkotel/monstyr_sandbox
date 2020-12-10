#!/usr/bin/env python

import os

from math import hypot, atan2, degrees, radians, sin, cos
from typing import Union, Tuple, List, Callable, Collection, Optional
from functools import wraps
from tkinter import StringVar, Listbox, Event, END


Point = Tuple[Union[int, float], Union[int, float]]


ENGLISH = 'english'
POLISH = 'polish'

LANGUAGES = {}
LANG_DIR = 'languages/'
for lang_file in os.listdir(LANG_DIR):
    lang_dict = LANGUAGES[lang_file.rstrip('.txt')] = {}
    with open(LANG_DIR + lang_file, 'r') as file:
        for line in file.readlines():
            key, value = line.rstrip('\n').split(' = ')
            lang_dict[key] = value


def localize(text: str, language: str) -> str:
    # text is localized by choosing a proper language-dict from dict of all
    # languages available, and then getting a value of a text-key from the
    # dict obtained:
    if language != ENGLISH:
        return LANGUAGES[language][text]
    return text


def plural(word: str, language: str = POLISH) -> str:
    if word.endswith(('e', 'bey')):
        word += 's'
    elif word.endswith('y'):
        word = word.rstrip('y') + 'ies'
    elif word.endswith(('ch')):
        word = word + 'es'
    elif word.endswith('s'):
        pass
    else:
        word = word + 's'
    return localize(word, language)


def get_screen_size() -> Tuple[int, int]:
    from PIL import ImageGrab
    screen = ImageGrab.grab()
    return int(screen.width), int(screen.height)


def load_image_or_placeholder(filename: str):
    from tkinter import PhotoImage
    if os.path.isfile(filename):
        return PhotoImage(file=filename)
    return PhotoImage(file='no_image.png')


def print_return(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        returned = func(*args, **kwargs)
        print(returned)
        return returned
    return wrapper


def input_match_search(query_variable: Union[StringVar, str],
                       searched: Callable,
                       updated: Union[Listbox, List],
                       event: Union[Event, int]) -> Optional[List]:
    """
    Handle dynamic search called when user writes his query in tkinter
    lords manager or in arcade map application.

    :param updated: lambda expression
    """
    if isinstance(query_variable, StringVar):
        # because this function is called by tkinter bind() method, the
        # StringVar value is not yet updated with pressed key, so we must
        # use as a query our own variable updated before actual StringVar
        # is modified:
        query = update_tk_stringvar(event, query_variable)
    else:
        query = query_variable
    return update_list_of_matching_results(query, searched(), updated)


def update_tk_stringvar(event: Event, query_variable: StringVar) -> str:
    if (pressed := event.keysym) == 'BackSpace':
        return query_variable.get()[:-1]
    elif pressed == 'space':
        return query_variable.get() + ' '
    else:
        return query_variable.get() + pressed


def update_list_of_matching_results(query: str,
                                    searched: Collection,
                                    updated_list: Union[Listbox, List]):
    if isinstance(updated_list, Listbox):
        updated_list.delete(0, END)
        for x in (x.name for x in searched if query in x.name):
            updated_list.insert(END, x)
    else:  # updated is a normal python list object
        return [x.name for x in searched if query in x.name.lower()]


def open_if_not_opened(func, window, spritelist):
    @wraps(func)
    def wrapper(*args, **kwargs):
        window = func(*args, **kwargs)
        if window[0] not in spritelist:
            spritelist.append(window)
    return wrapper


def get_current_language():
    with open('config.txt', 'r') as config:
        language = config.readline().rstrip('\n').split('=')[1]
    return language


def no_spaces(text: str) -> str:
    """Replace all spaces with underscores."""
    return text.replace(' ', '_')


def slots_to_fields(_object, ignore_fields: Tuple) -> List[str]:
    return [slot_to_field(s) for s in filtered_slots_names(_object, ignore_fields)]


def filtered_slots_names(_object, ignore_fields: Tuple) -> List[str]:
    return [slot for slot in _object.__slots__ if slot not in ignore_fields]


def slot_to_field(slot: str) -> str:
    return f"{slot.lstrip('_').replace('_', ' ').title()}:"


def clamp(value, maximum, minimum) -> Union[int, float]:
    """Guarantee that number will by larger than min and less than max."""
    return max(minimum, min(value, maximum))


def distance_2d(coord_a: Point, coord_b: Point) -> float:
    """Calculate distance between two points in 2D space."""
    return hypot(coord_b[0] - coord_a[0], coord_b[1] - coord_a[1])


def calculate_angle(sx: float, sy: float, ex: float, ey: float) -> float:
    """
    Calculate angle in direction from 'start' to the 'end' point in degrees.

    :param:sx float -- x coordinate of start point
    :param:sy float -- y coordinate of start point
    :param:ex float -- x coordinate of end point
    :param:ey float -- y coordinate of end point
    :return: float -- degrees in range 0-360.
    """
    rads = atan2(ex - sx, ey - sy)
    return degrees(rads) % 360


def move_along_vector(start: Point,
                      velocity: float,
                      target: Optional[Point] = None,
                      angle: Optional[float] = None) -> Point:
    """
    Create movement vector starting at 'start' point angled in direction of
    'target' point with scalar velocity 'velocity'. Optionally, instead of
    'target' position, you can pass starting 'angle' of the vector.

    Use 'current_waypoint' position only, when you now the point and do not know the
    angle between two points, but want quickly calculate position of the
    another point lying on the line connecting two, known points.

    :param start: tuple -- point from vector starts
    :param target: tuple -- current_waypoint that vector 'looks at'
    :param velocity: float -- scalar length of the vector
    :param angle: float -- angle of the vector direction
    :return: tuple -- (optional)position of the vector end
    """
    if target is None and angle is None:
        raise ValueError("You MUST pass current_waypoint position or vector angle!")
    p1 = (start[0], start[1])
    if target:
        p2 = (target[0], target[1])
        angle = calculate_angle(*p1, *p2)
    vector = vector_2d(angle, velocity)
    return p1[0] + vector[0], p1[1] + vector[1]


def vector_2d(angle: float, scalar: float) -> Point:
    """
    Calculate x and y parts of the current vector.

    :param angle: float -- angle of the vector
    :param scalar: float -- scalar difference of the vector (e.g. max_speed)
    :return: Point -- x and y parts of the vector in format: (float, float)
    """
    rad = radians(angle)
    return sin(rad) * scalar, cos(rad) * scalar
