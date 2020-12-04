#!/usr/bin/env python
from __future__ import annotations

from typing import Optional, List, Tuple

from tkinter import EventType, Canvas, Tk

from utils.classes import Location
from lords_manager.lords_manager import LordsManager


class Map:

    def __init__(self, application: Tk, width: int, height: int):
        self.application = application
        self.manager: LordsManager = application.manager
        self.locations: List[Location] = []
        self.width = width
        self.height = height
        self.viewport = 0, 0, 600, 600  # TODO: update it with cursor-drag
        self.cursor_position = None
        self.pointed_location: Optional[Location] = None
        self.update()

    def update(self):
        try:
            self.application.map_canvas.delete('location')
            self.draw_visible_map_locations()
        except AttributeError:
            pass
        self.application.after(13, self.update)

    def draw_visible_map_locations(self):
        pointed = False
        self.pointed_location = None
        for location in (l for l in self.manager.locations if self.visible(l)):
            x, y = location.position
            if not pointed and self.cursor_position is not None:
                cx, cy = self.cursor_position
                color, pointed = self.check_if_pointing_at_location(x, y, cx, cy)
                if pointed:
                    self.pointed_location = location
            else:
                color = 'grey'
            self.draw_location(color, location, x, y)

    def draw_location(self, color, location, x, y):
        self.application.map_canvas.create_rectangle(
            x - 5, y - 5, x + 5, y + 5, fill=color, outline='black',
            tags='location'
        )
        text = location.name
        self.application.map_canvas.create_text(x + 50, y, text=text,
                                                fill='black', tags='location')

    def visible(self, location: Location):
        x, y = location.position
        l, b, r, t = self.viewport
        return l < x < r and b < y < t

    @staticmethod
    def check_if_pointing_at_location(x, y, cx, cy) -> Tuple[str, bool]:
        l, b, r, t = x - 5, y - 5, x + 5, y + 5
        if l < cx < r and b < cy < t:
            return 'lightgreen', True
        else:
            return 'grey', False

    def on_left_click(self, event: EventType):
        print(f'Left click on map canvas at: {event.x, event.y}')
        canvas: Canvas = event.widget
        if self.pointed_location is not None:
            print(f'Clicked at {self.pointed_location.full_name}')

    def on_right_click(self, event: EventType):
        print(f'Right click on map canvas at: {event.x, event.y}')
        canvas: Canvas = event.widget

    def mouse_motion(self, event: EventType):
        canvas: Canvas = event.widget
        self.cursor_position = event.x, event.y

    def on_mouse_exit(self, event: EventType):
        print(f'Cursor exited canvas!')
        self.cursor_position = None

    def on_mouse_enter(self, event: EventType):
        print(f'Cursor entered canvas!')
        self.cursor_position = event.x, event.y

    def highlight_pointed_location(self, pointed: Location):
        print(f'Mouse pointing at: {pointed.name}')
