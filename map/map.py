#!/usr/bin/env python
from __future__ import annotations

import PIL

from typing import Optional, Union, List, Tuple

from tkinter import EventType, Canvas, Tk, PhotoImage, SUNKEN

from utils.enums import LocationType
from utils.classes import Location, Nobleman
from utils.functions import clamp
from lords_manager.lords_manager import LordsManager

MAP_CANVAS_WIDTH = 600
MAP_CANVAS_HEIGHT = 600
MIN_ZOOM = 1
MAX_ZOOM = 5
NAME_ONLY = (LocationType.village, LocationType.town, LocationType.city)


Point = Tuple[Union[int, float], Union[int, float]]


class Map:
    """
    This class handles rendering the graphic representation of the world (using
    the tk.Canvas to draw) and user-navigation across the world-map (handles
    user mouse-actions on the tk.Canvas).
    """

    def __init__(self, application: Tk, width: int, height: int):
        self.application = application
        self.manager: LordsManager = application.manager
        self.locations: List[Location] = []
        self.width = width
        self.height = height
        self.zoom = 1.0
        self.viewport = [0, 0, MAP_CANVAS_WIDTH, MAP_CANVAS_HEIGHT]
        self.cursor_position = None
        self.pointed_location: Optional[Location] = None
        self.selected_locations = set()
        self.update()

    def create_map_canvas(self, parent) -> Canvas:
        canvas = Canvas(parent, width=MAP_CANVAS_WIDTH, height=MAP_CANVAS_HEIGHT,
                        bg='DarkOliveGreen3', borderwidth=2, relief=SUNKEN)
        canvas.bind('<Enter>', self.on_mouse_enter)
        canvas.bind('<Leave>', self.on_mouse_exit)
        canvas.bind('<Motion>', self.on_mouse_motion)
        canvas.bind('<B3-Motion>', self.on_mouse_drag)
        canvas.bind('<Button-1>', self.on_left_click)
        canvas.bind('<Button-3>', self.on_right_click)
        canvas.bind('<Button-4>', self.on_mouse_scroll)
        canvas.bind('<Button-5>', self.on_mouse_scroll)
        return canvas

    def update(self):
        try:
            canvas = self.application.map_canvas
            canvas.delete('all')
            self.draw_visible_map_locations(canvas)
            self.draw_minimap(canvas)
        except AttributeError:
            pass
        self.application.after(13, self.update)

    def draw_visible_map_locations(self, canvas: Canvas):
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
            self.draw_location(canvas, color, location, x - l, y - b)

    def draw_location(self, canvas, color, location, x, y):
        zoom = self.zoom
        if location.type in NAME_ONLY:
            text = location.name
            self.draw_town_icon(canvas, color, zoom, x, y)
        else:
            self.draw_rectanle_icon(canvas, color, zoom, x, y)
            text = location.full_name
        if location in self.selected_locations:
            self.draw_selection_gizmo_around_location(canvas, zoom, x, y)
        font = f'Times {int(12 * zoom)}'
        canvas.create_text(x + 10, y, font=font, text=text, tags='loc', anchor='w')

    @staticmethod
    def draw_town_icon(canvas, color, zoom, x, y):
        size = 5 * zoom
        canvas.create_polygon(
            x - size, y - size, x, y - 2 * size, x + size, y - size, x + size,
            y + size, x - size, y + size, fill=color, outline='black', tags='loc'
        )

    @staticmethod
    def draw_rectanle_icon(canvas, color, zoom, x, y):
        size = 7 * zoom
        canvas.create_rectangle(
            x - size, y - size, x + size, y + size, fill=color, outline='black', tags='loc'
        )

    @staticmethod
    def draw_selection_gizmo_around_location(canvas, zoom, x, y):
        size = 10 * zoom
        canvas.create_rectangle(
            x - size, y - size, x + size, y + size, outline='yellow', width=3
        )

    def check_if_pointing_at_location(self, x, y, vl, vb) -> Tuple[str, bool]:
        cx, cy = self.cursor_position
        size = 7 * self.zoom
        l, b, r, t = x - size, y - size, x + size, y + size
        if l < cx + vl < r and b < cy + vb < t:
            return 'yellow', True
        else:
            return 'grey', False

    def draw_minimap(self, canvas: Canvas):
        canvas.create_rectangle(
            10, 10, 10 + self.width // 100, 10 + self.height // 100, fill='white')
        canvas.create_rectangle(
            *[10 + (i / 100) / self.zoom for i in self.viewport], outline='black'
        )

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
        l = clamp(l + dx, self.width - MAP_CANVAS_WIDTH, 0)
        b = clamp(b + dy, self.height - MAP_CANVAS_HEIGHT, 0)
        self.viewport = [l, b, l + MAP_CANVAS_WIDTH, b + MAP_CANVAS_HEIGHT]

    def move_to_position(self, instance: Union[Nobleman, Location]):
        """
        Move map viewport to the position of the selected Location, or to the
        averaged position of the selected Nobleman fiefs.
        """
        l, b, *_ = self.viewport
        position = self._get_position_to_move(instance)
        new_left = position[0] - 300
        new_bottom = position[1] - 300
        self.update_viewport(new_left - l, new_bottom - b)

    def _get_position_to_move(self, instance) -> Point:
        self.selected_locations.clear()
        if isinstance(instance, Location):
            self.selected_locations.add(instance)
            return instance.position
        elif len(instance.fiefs) == 0:
            self.selected_locations.update(instance.fiefs)
            return self.width // 2, self.height // 2
        else:
            return self._get_average_position_of_lords_fiefs(instance)

    @staticmethod
    def _get_average_position_of_lords_fiefs(lord: Nobleman) -> Point:
        position = 0, 0
        positions = len(lord.fiefs)
        for fief in lord.fiefs:
            position[0] += fief.position[0]
            position[1] += fief.position[1]
        return position[0] / positions, position[1] / positions
