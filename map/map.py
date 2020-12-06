#!/usr/bin/env python
from __future__ import annotations

import math
from math import radians, sin, cos

from random import randint, choice
from typing import Optional, Union, Any, List, Tuple, Dict

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
        self.points = []
        self.windrose = PhotoImage(file='windrose.png')
        self.update()

    def generate_random_vilages(self, number_of_villages: int) -> List[Point]:
        points = self.generate_random_spawn_points(number_of_villages)
        for point in points:
            lords = [l for l in self.manager.lords]
            villages_names = self.manager.villages_names
            self.manager.add(
                Location(
                    len(self.manager.locations) + 1,
                    villages_names.pop(randint(0, len(villages_names) - 1)),
                    choice([f'village_{i}.png' for i in range(1, 5, 1)]),
                    point,
                    owner=choice(lords),
                    population=randint(145, 325)
                )
            )
        return points

    def generate_random_spawn_points(self, number_of_villages) -> List[Point]:
        radius = 150
        grid_cell_size = int(radius / math.sqrt(2))
        grid: Dict[Tuple[int, int], Any] = self.generate_grid(grid_cell_size)
        points = []

        grid_rows = self.height // grid_cell_size
        grid_columns = self.width // grid_cell_size

        while number_of_villages:
            point = randint(0, self.width), randint(0, self.height)
            cell = int(point[0]) // grid_cell_size, int(point[1] // grid_cell_size)
            if self.valid(cell, point, radius, grid, grid_columns, grid_rows):
                grid[cell] = point
                points.append(point)
                number_of_villages -= 1
        return points

    def valid(self, cell, point, radius, grid, grid_columns, grid_rows):
        x, y = cell
        min_x = max(0, x - 2)
        max_x = min(grid_columns, x + 2)
        min_y = max(0, y - 2)
        max_y = min(grid_rows, y + 2)
        for i in range(min_x, max_x):
            for j in range(min_y, max_y):
                if (other := grid[(i, j)]) is not None:
                    dist = math.hypot(
                        (other[0] - point[0]), (other[1] - point[1])
                    )
                    if dist < radius:
                        return False
        return True

    def generate_grid(self, grid_cell_size: int) -> Dict[Tuple[int, int], Any]:
        grid_rows = self.height // grid_cell_size
        grid_columns = self.width // grid_cell_size
        return {
            (c, r): None for c in range(grid_columns) for r in
            range(grid_rows)
        }

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
        if not self.points and self.manager.lords:
            self.points = [l.position for l in self.manager.locations]
        try:
            canvas: Canvas = self.application.map_canvas
            canvas.delete('loc', 'p', 'gizmo')
            self.draw_visible_map_locations(canvas)
            self.draw_scale_and_wind_rose()
            self.draw_minimap(canvas)
        except AttributeError:
            pass
        self.application.after(13, self.update)

    def draw_visible_map_locations(self, canvas: Canvas):
        pointed = False
        self.pointed_location = None
        l, b, r, t = self.viewport
        zoom = self.zoom
        for p in self.points:
            if not (l < p[0] * zoom < r and b < p[1] * zoom < t):
                continue
            p = p[0] * zoom - l, p[1] * zoom - b
            canvas.create_oval(
                p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5, outline='red', tags='p'
            )
        for location in self.manager.locations:
            x, y = location.position
            if not (l < x * zoom < r and b < y * zoom < t):
                continue
            x *= zoom
            y *= zoom
            if not pointed and self.cursor_position is not None:
                color, pointed = self.check_if_pointing_at_location(x, y, l, b)
                if pointed:
                    self.pointed_location = location
            else:
                color = 'white'
            self.draw_location(canvas, color, location, x - l, y - b)

    def draw_location(self, canvas, color, location, x, y):
        zoom = self.zoom
        if location.type in NAME_ONLY:
            text = location.name
            self.draw_house_icon(canvas, color, zoom, x, y)
        else:
            self.draw_rectanle_icon(canvas, color, zoom, x, y)
            text = location.full_name
        if location in self.selected_locations:
            self.draw_selection_gizmo_around_location(canvas, zoom, x, y)
        font = f'Times {int(12 * zoom)}'
        canvas.create_text(x + 10, y, font=font, text=text, tags='loc', anchor='w')

    @staticmethod
    def draw_house_icon(canvas, color, zoom, x, y):
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
            x - size, y - size, x + size, y + size, outline='yellow', width=3, tags='gizmo'
        )

    def check_if_pointing_at_location(self, x, y, vl, vb) -> Tuple[str, bool]:
        cx, cy = self.cursor_position
        size = 7 * self.zoom
        l, b, r, t = x - size, y - size, x + size, y + size
        if l < cx + vl < r and b < cy + vb < t:
            return 'yellow', True
        else:
            return 'white', False

    def draw_minimap(self, canvas: Canvas):
        canvas.create_rectangle(
            10, 10, 10 + self.width // 100, 10 + self.height // 100, fill='white', tags='gizmo')
        for p in self.points:
            canvas.create_oval(
                10 + p[0] / 100, 10 + p[1] / 100, 10 + p[0] / 100, 10 + p[1] / 100,
                outline='grey50', tags='p'
            )
        canvas.create_rectangle(
            *[10 + (i / 100) / self.zoom for i in self.viewport], outline='black'
        )

    def draw_scale_and_wind_rose(self):
        x, y = 525, 70
        self.application.map_canvas.create_image(x, y, image=self.windrose, tags='gizmo')

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
        if (position := self._get_position_to_move(instance)) is not None:
            new_left = position[0] - MAP_CANVAS_WIDTH // 2
            new_bottom = position[1] - MAP_CANVAS_HEIGHT // 2
            l, b, *_ = self.viewport
            self.update_viewport(new_left - l, new_bottom - b)

    def _get_position_to_move(self, instance) -> Optional[Point]:
        self.selected_locations.clear()
        if isinstance(instance, Location):
            self.selected_locations.add(instance)
            return instance.position
        elif instance.fiefs:
            return self._get_average_position_of_lords_fiefs(instance)

    def _get_average_position_of_lords_fiefs(self, lord: Nobleman) -> Point:
        fiefs = [self.manager.get_location_of_id(i) for i in lord.fiefs]
        self.selected_locations.update(fiefs)
        position = [0, 0]
        positions = len(fiefs)
        for fief in fiefs:
            position[0] += fief.position[0]
            position[1] += fief.position[1]
        return position[0] / positions, position[1] / positions
