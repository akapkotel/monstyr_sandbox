#!/usr/bin/env python

from typing import Tuple
from functools import wraps


def localize(text: str) -> str:
    return {
        'locations total': 'wszystkie', 'villages': 'wsie',
        'towns:': 'miasteczka', 'cities': 'miasta',
        'palaces': 'pałace', 'windmills': 'wiatraki',
        'watermills': 'młyny wodne', 'wineries': 'winnice',
        'breweries': 'browary', 'mines': 'kopalnie',
        'quarries': 'kamieniołomy', 'churches': 'kościoły',
        'hideouts': 'kryjóœki', 'castles': 'zamki',
        'millitary posts': 'stanice wosjkowe',
        'fortesses': 'fortece', 'manufactures': 'manufaktury',
        'stables': 'hodowle koni', 'hospitals': 'szpitale',
        'fortified towers': 'baszty', 'castellums': 'kasztele',
        'granges': 'folwarki', 'plantations': 'plantacje',
        'shipyards': 'stocznie'
    }[text]


def plural(word: str) -> str:
    if word.endswith('bey'):
        return word + 's'
    elif word.endswith('y'):
        return word.rstrip('y') + 'ies'
    elif word.endswith('e'):
        return word + 's'
    elif word.endswith(('ch', 's')):
        return word + 'es'
    else:
        return word + 's'


def get_screen_size() -> Tuple[int, int]:
    from PIL import ImageGrab
    screen = ImageGrab.grab()
    return int(screen.width), int(screen.height)


def load_image_or_placeholder(filename: str):
    import os
    from tkinter import PhotoImage
    filename = filename.replace('_', ' ')
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


def single_slashes(path: str) -> str:
    return path.replace('\\\\', "\\")
