#!/usr/bin/env python

import os

from typing import Tuple
from functools import wraps

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
    return LANGUAGES[language][text]


def plural(word: str, language: str = POLISH) -> str:
    if word.endswith(('e', 'bey')):
        word += 's'
    elif word.endswith('y'):
        word = word.rstrip('y') + 'ies'
    elif word.endswith(('ch', 's')):
        word = word + 'es'
    else:
        word = word + 's'
    if language != ENGLISH:
        return localize(word, language)
    return word


def get_screen_size() -> Tuple[int, int]:
    from PIL import ImageGrab
    screen = ImageGrab.grab()
    return int(screen.width), int(screen.height)


def load_image_or_placeholder(filename: str):
    import os
    from tkinter import PhotoImage
    # filename.replace('_', ' ')
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
