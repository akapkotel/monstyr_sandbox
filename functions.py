#!/usr/bin/env python

import os

from typing import Union, Tuple, List, Callable, Sized
from functools import wraps
from tkinter import StringVar, Listbox, Event, END
from arcade import Window
from arcade.key import BACKSPACE, SPACE

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
    import os
    from tkinter import PhotoImage
    if os.path.exists(filename):
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
                       event: Union[Event, int]):
    """
    Handle dynamic search called when user writes his query in tkinter
    lords manager or in arcade map application. There are two cases
    with different types of parameters passed to this function. Both of them
    are handled in two steps: (1) updating value of virtual variable which
    stores current query with the last user-pressed key, and then (2)
    updating the list of elements of searched collection to match the query.
    """
    if isinstance(query_variable, StringVar):
        query = update_tk_stringvar(event, query_variable)
    else:
        query = update_string(event, query_variable)
    update_target_with_variable(query, searched, updated)


def update_tk_stringvar(event: Event, query_variable: StringVar) -> str:
    if (pressed := event.keysym) == 'BackSpace':
        query = query_variable.get()[:-1]
    elif pressed == 'space':
        query = query_variable.get() + ' '
    else:
        query = query_variable.get() + pressed
    return query


def update_string(event: int, query_variable: str) -> str:
    if (pressed := event) == BACKSPACE:
        query = query_variable[:-1]
    elif pressed == SPACE:
        query = query_variable + ' '
    else:
        query = query_variable + chr(pressed)
    return query


def update_target_with_variable(query: str,
                                searched: Callable,
                                updated: Union[Listbox, List]):
    if isinstance(updated, Listbox):
        updated.delete(0, END)
        for x in (x.name for x in searched() if query in x.name):
            updated.insert(END, x)
    else:  # updated is a normal python list object
        updated = [x.name for x in searched() if query in x.name]


def remove_arcade_window_from_returned_value(func: Callable):
    @wraps(func)
    def remover(*args, **kwargs):
        result = func(*args, **kwargs)
        return [e for e in result if not isinstance(e, Window)]
    return remover


def open_if_not_opened(func, window, spritelist):
    @wraps(func)
    def wrapper(*args, **kwargs):
        window = func(*args, **kwargs)
        if window[0] not in spritelist:
            spritelist.append(window)
    return wrapper


def get_current_language():
    with open('config.txt', 'r') as config:
        language = config.readline().rstrip('\n')
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
