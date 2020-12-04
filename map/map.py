#!/usr/bin/env python

from tkinter import Canvas, Event


from lords_manager.lords_manager import LordsManager


class Map:

    def __init__(self, manager: LordsManager, width: int, height: int):
        self.manager = manager
        self.width = width
        self.height = height

    def add_location(self, event: Event):
        print(f'Added location to map canvas at: {event.x, event.y}')
        event.widget: Canvas
        event.widget.create_rectangle(event.x - 5, event.y - 5, event.x + 5,
                                      event.y + 5)

    def mouse_over(self, event: Event):
        print(f'Mouse moving above canvas!')
