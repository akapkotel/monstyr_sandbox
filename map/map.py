#!/usr/bin/env python
from __future__ import annotations

import math

from random import randint, choice
from typing import Optional, Union, Any, List, Tuple, Dict
from multiprocessing import Pool
from shapely.geometry import MultiPoint, Point as ShapelyPoint
from shapely.ops import triangulate

from tkinter import EventType, Canvas, Tk, PhotoImage, SUNKEN

from utils.enums import LocationType
from utils.classes import Location, Nobleman
from utils.functions import clamp, distance_2d, calculate_angle, Point
from lords_manager.lords_manager import LordsManager

MAP_CANVAS_WIDTH = 600
MAP_CANVAS_HEIGHT = 600
MIN_ZOOM = 1
MAX_ZOOM = 5
NAME_ONLY = (LocationType.village, LocationType.town, LocationType.city)
VILLAGES_COUNT = 2900
VILLAGES_RADIUS = 150
TREES_RADIUS = 75


class WorldBuilder:

    def __init__(self, map: Map):
        self.map = map
        self.borders = [
            (0, 0), (0, self.map.height), (self.map.width, self.map.height),
            (self.map.width, 0)
        ]
        self.points = []

    def build_world(self, villages_count=0) -> Tuple[List, Dict]:
        if locations := self.map.manager.locations:
            points = [location.position for location in locations]
        else:
            points = self.get_random_points(villages_count, VILLAGES_RADIUS)
            self.spawn_villages_at_points(points)
        borders = self.borders
        roads = self.connect_locations_with_roads(borders + points)
        regions = self.generate_map_regions(roads, locations)
        return [r for r in roads if distance_2d(*r[0]) < 250], regions

    def spawn_villages_at_points(self, points):
        for point in points:
            lords = [l for l in self.map.manager.lords]
            villages_names = self.map.manager.villages_names
            self.map.manager.add(
                Location(
                    len(self.map.manager.locations) + 1,
                    villages_names.pop(randint(0, len(villages_names) - 1)),
                    choice([f'village_{i}.png' for i in range(1, 5, 1)]),
                    point,
                    owner=choice(lords),
                    population=randint(65, 240)
                )
            )

    def get_random_points(self, count, radius) -> List[Point]:
        cell_size = int(radius / math.sqrt(2))
        grid: Dict[Tuple[int, int], Any] = self.generate_grid(cell_size)
        grid_rows = self.map.height // cell_size
        grid_columns = self.map.width // cell_size
        points = []

        required_villages_count = count or VILLAGES_COUNT
        while required_villages_count:
            point = (randint(25, self.map.width-150),
                     randint(25, self.map.height-150))
            cell = int(point[0]) // cell_size, int(point[1] // cell_size)
            if self.valid(cell, point, radius, grid, grid_columns, grid_rows):
                grid[cell] = point
                points.append(point)
                required_villages_count -= 1
        return points

    @staticmethod
    def random_point_in_cell(cell, cell_size) -> Point:
        x = randint(0, cell_size) * cell[0]
        y = randint(0, cell_size) * cell[1]
        return x, y

    @staticmethod
    def valid(cell, point, radius, grid, grid_columns, grid_rows):
        """
        Check if there is no other spawn-point in any of the 5x5 cells-matrix
        around the point containing other point closer than radius distance.
        """
        if grid[cell] is not None:
            return False
        x, y = cell
        min_x = max(0, x - 2)
        max_x = min(grid_columns, x + 2)
        min_y = max(0, y - 2)
        max_y = min(grid_rows, y + 2)
        for i in range(min_x, max_x):
            for j in range(min_y, max_y):
                if (other := grid[(i, j)]) is not None:
                    dist = math.hypot((other[0] - point[0]), (other[1] - point[1]))
                    if dist < radius:
                        return False
        return True

    def generate_grid(self, cell_size: int) -> Dict[Tuple[int, int], Any]:
        grid_rows = self.map.height // cell_size
        grid_columns = self.map.width // cell_size
        return {
            (c, r): None for c in range(grid_columns) for r in range(grid_rows)
        }

    @staticmethod
    def connect_locations_with_roads(points):
        shapely_points = MultiPoint(points)
        connections = triangulate(shapely_points, edges=True)
        return [([p for p in c.coords], c.centroid) for c in connections]

    @staticmethod
    def generate_map_regions(roads, locations) -> Dict[Point, List[Point]]:
        regions: Dict[Point, List[Point]] = {
            loc.position: [] for loc in locations
        }
        # add road centroid to each region this road connects, since both
        # ends of road are centers of regions:
        for road in roads:
            for x, y in road[0]:
                try:
                    regions[(int(x), int(y))].append((road[1].x, road[1].y))
                except KeyError:
                    pass
        # sort vertices in regions to use them later to build polygons
        for center, points in regions.items():
            points.sort(key=lambda e: calculate_angle(*center, *e))
        return regions


class Map:
    """
    This class handles rendering the graphic representation of the world (using
    the tk.Canvas to draw) and user-navigation across the world-map (handles
    user mouse-actions on the tk.Canvas).
    """

    def __init__(self, application: Tk, width: int, height: int):
        self.application = application
        self.manager: LordsManager = application.manager
        self.width = width
        self.height = height
        self.zoom = 1.0
        self.viewport = [0, 0, MAP_CANVAS_WIDTH, MAP_CANVAS_HEIGHT]
        self.cursor_position = None
        self.pointed_location: Optional[Location] = None
        self.selected_locations = set()
        self.minimap_points: List[Point] = []
        self.roads: List[Tuple[List[Point], ShapelyPoint]] = []
        self.regions: Dict[Point, List[Point]] = {}
        self.windrose = PhotoImage(file='windrose.png')
        self.builder = WorldBuilder(self)
        self.update()

    def create_map_canvas(self, parent) -> Canvas:
        canvas = Canvas(parent, width=MAP_CANVAS_WIDTH, height=MAP_CANVAS_HEIGHT,
                        bg='DarkOliveGreen3', borderwidth=2, relief=SUNKEN,
                        cursor='crosshair')
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
        if not self.roads and self.manager.lords:  # build only once
            self.build_world()
        try:
            canvas: Canvas = self.application.map_canvas
            self.draw_map(canvas)
        except AttributeError:
            pass
        self.application.after(13, self.update)

    def draw_map(self, canvas):
        canvas.delete('all')
        self.draw_visible_map_contents(canvas)
        self.draw_scale_and_wind_rose(canvas)
        self.draw_minimap(canvas)

    def build_world(self):
        self.roads, self.regions = self.builder.build_world()
        self.minimap_points = [l.position for l in self.manager.locations]

    def draw_visible_map_contents(self, canvas: Canvas):
        pointed = False
        self.pointed_location = None
        l, b, r, t = self.viewport
        zoom = self.zoom
        self.draw_regions(canvas, b, l, r, t, zoom)
        self.draw_roads(canvas, b, l, r, t, zoom)
        self.draw_locations(b, canvas, l, pointed, r, t, zoom)

    def draw_roads(self, canvas, b, l, r, t, zoom):
        for i, (road, centroid) in enumerate(self.roads):
            if any((l < p[0] * zoom < r and b < p[1] * zoom < t) for p in road):
                points = [(p[0] * zoom - l, p[1] * zoom - b) for p in road]
                canvas.create_line(*points, dash=(6, 3), fill='brown')

    def draw_regions(self, canvas, b, l, r, t, zoom):
        for location in self.selected_locations:
            region = self.regions[location.position]
            if any((l < p[0] * zoom < r and b < p[1] * zoom < t) for p in region):
                points = [(p[0] * zoom - l, p[1] * zoom - b) for p in region]
                canvas.create_polygon(*points, dash=(6, 3), outline='yellow',
                                      fill='DarkOliveGreen3')

    def draw_locations(self, b, canvas, l, pointed, r, t, zoom):
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
            self.draw_single_location(canvas, color, location, x - l, y - b)

    def draw_single_location(self, canvas, color, location, x, y):
        zoom = self.zoom
        text = location.name
        if location.type in NAME_ONLY:
            population = int(location.population // 100)
            self.draw_house_icon(canvas, color, zoom, x, y, population)
        else:
            self.draw_rectanle_icon(canvas, color, zoom, x, y)
            text = location.full_name
        if location in self.selected_locations:
            self.draw_selection_gizmo_around_location(canvas, zoom, x, y)
        font = f'Times {int(12 * zoom)} bold'
        canvas.create_text(x + 10, y, font=font, text=text, anchor='w')

    @staticmethod
    def draw_house_icon(canvas, color, zoom, x, y, population):
        size = zoom * (4 + population)
        canvas.create_polygon(
            x - size, y - size, x, y - 2 * size, x + size, y - size, x + size,
            y + size, x - size, y + size, fill=color, outline='black'
        )

    @staticmethod
    def draw_rectanle_icon(canvas, color, zoom, x, y):
        size = 7 * zoom
        canvas.create_rectangle(
            x - size, y - size, x + size, y + size, fill=color, outline='black'
        )

    @staticmethod
    def draw_abbey_icon(canvas, color, zoom, x, y):
        size = 5 * zoom
        canvas.create_polygon(
            x - size, y - size, x, y - 2 * size, x + size, y - size, x + size,
            y + size, x - size, y + size, fill=color, outline='black'
        )
        Map.draw_cross(canvas, x, y, zoom)

    @staticmethod
    def draw_cross(canvas, x, y, zoom):
        size = 3 * zoom
        y -= 4 * size
        canvas.create_line(x - size, y, x + size, y, fill='black', width=2)
        canvas.create_line(x, y - size, x, y + size, fill='black', width=2)

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
            return 'white', False

    def draw_minimap(self, canvas: Canvas):
        canvas.create_rectangle(
            10, 10, 10 + self.width // 100, 10 + self.height // 100, fill='white')
        self.draw_locations_points(canvas)
        self.draw_viewport(canvas)

    def draw_locations_points(self, canvas):
        for x, y in self.minimap_points:
            canvas.create_oval(
                10 + x / 100, 10 + y / 100, 10 + x / 100, 10 + y / 100,
                outline='grey50'
            )

    def draw_viewport(self, canvas):
        canvas.create_rectangle(
            *[10 + (i / 100) / self.zoom for i in self.viewport], outline='red'
        )

    def draw_scale_and_wind_rose(self, canvas):
        x, y = 525, 70
        canvas.create_image(x, y, image=self.windrose)
        # distance scale:
        x, size = 450, self.zoom * 25
        for i in range(1, 6, 1):
            xi = x - (size * i)
            y = xi + size
            color = 'white' if i % 2 else 'black'
            canvas.create_rectangle(xi, 40, y, 45, fill=color, outline='black')

    def on_mouse_enter(self, event: EventType):
        self.cursor_position = event.x, event.y

    def on_mouse_exit(self, event: EventType):
        self.cursor_position = None

    def on_left_click(self, event: EventType):
        if (location := self.pointed_location) is not None:
            self.application.open_new_or_show_opened_window(location)

    def on_right_click(self, event: EventType):
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
        self.update_viewport(0, 0)

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
