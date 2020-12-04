#!/usr/bin/env python

import os

from typing import Union, Tuple, List, Callable, Sized, Collection, Optional
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


def update_string_with_pressed_key(key: int, query_variable: str) -> str:
    if (pressed := key) == BACKSPACE:
        return query_variable[:-1]
    elif (letter := chr(pressed)).isalpha() or letter.isspace():
        return query_variable + letter
    else:
        return query_variable


def update_list_of_matching_results(query: str,
                                    searched: Collection,
                                    updated_list: Union[Listbox, List]):
    if isinstance(updated_list, Listbox):
        updated_list.delete(0, END)
        for x in (x.name for x in searched if query in x.name):
            updated_list.insert(END, x)
    else:  # updated is a normal python list object
        return [x.name for x in searched if query in x.name.lower()]


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


def clamp(value, maximum, minimum) -> Union[int, float]:
    """Guarantee that number will by larger than min and less than max."""
    return max(minimum, min(value, maximum))
