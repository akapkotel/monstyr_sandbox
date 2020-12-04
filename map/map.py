#!/usr/bin/env python
from __future__ import annotations

import os

from typing import Optional, List, Tuple

from tkinter import EventType, Canvas, Tk, PhotoImage

from utils.enums import LocationType
from utils.classes import Location
from utils.functions import clamp
from lords_manager.lords_manager import LordsManager

MIN_ZOOM = 1
MAX_ZOOM = 5
NAME_ONLY = (LocationType.village, LocationType.town, LocationType.city)


class Map:

    def __init__(self, application: Tk, width: int, height: int):
        self.application = application
        self.manager: LordsManager = application.manager
        self.locations: List[Location] = []
        self.width = width
        self.height = height
        self.zoom = 1.0
        self.viewport = [0, 0, 600, 600]
        self.cursor_position = None
        self.pointed_location: Optional[Location] = None
        self.images = {}
        self.update()

    def update(self):
        try:
            self.application.map_canvas.delete('loc')
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
            zoom = self.zoom
            if not (l < x * zoom < r and b < y * zoom < t):
                continue
            x *= zoom
            y *= zoom
            if not pointed and self.cursor_position is not None:
                color, pointed = self.check_if_pointing_at_location(x, y, l, b)
                if pointed:
                    self.pointed_location = location
            else:
                color = 'grey'
            self.draw_location(color, location, x - l, y - b)

    def draw_location(self, color, location, x, y):
        canvas = self.application.map_canvas
        if location.type in NAME_ONLY:
            text = location.name
            self.draw_town_icon(canvas, color, x, y)
        else:
            self.draw_rectanle_icon(canvas, color, x, y)
            text = location.full_name
        font = f'Times {int(12 * self.zoom)}'
        canvas.create_text(x + 10, y, font=font, text=text, tags='loc', anchor='w')

    def draw_town_icon(self, canvas, color, x, y):
        size = 5 * self.zoom
        canvas.create_polygon(
            x - size, y - size, x, y - 2 * size, x + size, y - size, x + size,
            y + size, x - size, y + size, fill=color, outline='black', tags='loc'
        )

    def draw_rectanle_icon(self, canvas, color, x, y):
        size = 7 * self.zoom
        canvas.create_rectangle(
            x - size, y - size, x + size, y + size, fill=color, outline='black', tags='loc'
        )

    def check_if_pointing_at_location(self, x, y, vl, vb) -> Tuple[str, bool]:
        cx, cy = self.cursor_position
        size = 7 * self.zoom
        l, b, r, t = x - size, y - size, x + size, y + size
        if l < cx + vl < r and b < cy + vb < t:
            return 'yellow', True
        else:
            return 'grey', False

    def on_mouse_enter(self, event: EventType):
        print(f'Cursor entered canvas!')
        self.cursor_position = event.x, event.y

    def on_mouse_exit(self, event: EventType):
        print(f'Cursor exited canvas!')
        self.cursor_position = None

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

    def on_mouse_scroll(self, event: EventType):
        ratio = 1 - 1 / (self.zoom / 0.1)
        if event.num == 4 or event.delta == 120:
            self.zoom_out(ratio)
        elif event.num == 5 or event.delta == -120:
            self.zoom_in(ratio)

    def zoom_out(self, ratio):
        if self.zoom > MIN_ZOOM:
            self.zoom = clamp(self.zoom - 0.1, MAX_ZOOM, MIN_ZOOM)
            self.viewport[0] *= ratio
            self.viewport[1] *= ratio
            
    def zoom_in(self, ratio):
        if self.zoom < MAX_ZOOM:
            self.zoom = clamp(self.zoom + 0.1, MAX_ZOOM, MIN_ZOOM)
            self.viewport[0] /= ratio
            self.viewport[1] /= ratio

    def update_viewport(self, dx, dy):
        l, b, r, t = self.viewport
        l = clamp(l + dx, self.width - 600, 0)
        b = clamp(b + dy, self.height - 600, 0)
        self.viewport = [l, b, r + 600, t + 600]
