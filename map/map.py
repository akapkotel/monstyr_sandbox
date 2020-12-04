#!/usr/bin/env python
from __future__ import annotations

from typing import Optional, List, Tuple

from tkinter import EventType, Canvas, Tk

from utils.enums import LocationType
from utils.classes import Location
from utils.functions import clamp
from lords_manager.lords_manager import LordsManager


NAME_ONLY = (LocationType.village, LocationType.town, LocationType.city)


class Map:

    def __init__(self, application: Tk, width: int, height: int):
        self.application = application
        self.manager: LordsManager = application.manager
        self.locations: List[Location] = []
        self.width = width
        self.height = height
        self.viewport = [0, 0, 600, 600]
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
        l, b, r, t = self.viewport
        for location in self.manager.locations:
            x, y = location.position
            if not (l < x < r and b < y < t):
                continue

            if not pointed and self.cursor_position is not None:
                color, pointed = self.check_if_pointing_at_location(x, y, l, b)
                if pointed:
                    self.pointed_location = location
            else:
                color = 'grey'
            self.draw_location(color, location, x - l, y - b)

    def visible(self, location: Location):
        x, y = location.position
        l, b, r, t = self.viewport
        return l < x < r and b < y < t

    def draw_location(self, color, location, x, y):
        self.application.map_canvas.create_rectangle(
            x - 5, y - 5, x + 5, y + 5, fill=color, outline='black',
            tags='location'
        )
        text = location.name if location.type in NAME_ONLY else location.full_name
        offset = 17 + len(text) * 3
        self.application.map_canvas.create_text(x + offset, y, text=text, tags='location')
        if location == self.pointed_location:
            self.application.map_canvas.create_rectangle(
                x - 10, y - 10, x + len(text) * 9, y + 10, outline='green', tags='location'
            )

    def check_if_pointing_at_location(self, x, y, vl, vb) -> Tuple[str, bool]:
        cx, cy = self.cursor_position
        l, b, r, t = x - 5, y - 5, x + 5, y + 5
        if l < cx + vl < r and b < cy + vb < t:
            return 'green', True
        else:
            return 'grey', False

    def on_left_click(self, event: EventType):
        print(f'Left click on map canvas at: {event.x, event.y}')
        if (location := self.pointed_location) is not None:
            self.application.open_new_or_show_opened_window(location)

    def on_right_click(self, event: EventType):
        print(f'Right click on map canvas at: {event.x, event.y}')
        canvas: Canvas = event.widget

    def on_mouse_motion(self, event: EventType):
        canvas: Canvas = event.widget
        self.cursor_position = event.x, event.y

    def on_mouse_drag(self, event: EventType):
        if self.cursor_position is not None:
            x, y = self.cursor_position
            self.update_viewport(x - event.x, y - event.y)
        self.cursor_position = event.x, event.y

    def on_mouse_exit(self, event: EventType):
        print(f'Cursor exited canvas!')
        self.cursor_position = None

    def on_mouse_enter(self, event: EventType):
        print(f'Cursor entered canvas!')
        self.cursor_position = event.x, event.y

    def update_viewport(self, dx, dy):
        l, b, r, t = self.viewport
        l = clamp(l + dx, self.width - 600, 0)
        b = clamp(b + dy, self.height - 600, 0)
        self.viewport = l, b, r + 600, t + 600
