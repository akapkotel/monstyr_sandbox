#!/usr/bin/env python
from __future__ import annotations

import math

from random import randint, choice, random
from typing import Optional, Union, Any, List, Tuple, Dict
from shapely.geometry import MultiPoint, Point as ShapelyPoint
from shapely.ops import triangulate

from tkinter import EventType, Canvas, Tk, PhotoImage, SUNKEN

from utils.enums import LocationType, Title
from utils.classes import Location, Nobleman
from utils.functions import (
    clamp, distance_2d, calculate_angle, move_along_vector, Point
)
from lords_manager.lords_manager import (
    LORDS_FIEFS, LordsManager, TerrainElements
)

MAP_CANVAS_WIDTH = 600
MAP_CANVAS_HEIGHT = 600
MIN_ZOOM = 0.2
MAX_ZOOM = 5
NAME_ONLY_LOCATIONS = (LocationType.village, LocationType.town, LocationType.city)
COURTS_COUNT = 360
VILLAGES_COUNT = 1600
VILLAGES_RADIUS = 200
FORRESTS_COUNT = 1200
TREES_RADIUS = 175


Road = Tuple[List, ShapelyPoint, float]


class WorldBuilder:

    def __init__(self, map: Map):
        self.map = map
        self.borders = [
            (0, 0), (0, self.map.height), (self.map.width, self.map.height),
            (self.map.width, 0)
        ]
        self.points = []
        self.locations_names = self.map.manager.locations_names

    def build_world(self,
                    courts=COURTS_COUNT,
                    villages=VILLAGES_COUNT) -> Tuple[List, Dict, Dict]:
        """
        Generate or use loaded data for map displayed elements.
        """
        locations, points = self.load_or_spawn_locations(courts, villages)
        roads, regions = self.load_or_spawn_roads_and_regions(points)
        forests = self.load_or_spawn_forests()
        return [r for r in roads if r[2] < 300], regions, forests

    def load_or_spawn_locations(self, courts, villages):
        if locations := self.map.manager.locations:
            points = [location.position for location in locations]
        else:
            points = self.spawn_locations(courts, villages)
        return locations, points

    def spawn_locations(self, courts, villages):
        points_count = courts + villages
        points = self.get_random_points(points_count, VILLAGES_RADIUS)
        villages_points = self.spawn_noble_courts(points)
        self.spawn_villages_at_points(villages_points)
        return points

    def spawn_noble_courts(self, points):
        used = set()
        court_types = {
            Title.baron: choice((LocationType.palace, LocationType.castellum)),
            Title.baronet: choice((LocationType.manor_house, LocationType.castellum)),
            Title.chevalier: choice((LocationType.manor_house, LocationType.villa)),
        }
        lords = [l for l in self.map.manager.lords if l.title != Title.client]
        for lord in [l for l in lords if not l.fiefs and l.title != Title.count]:
            location_type = court_types[lord.title]
            name = choice(self.locations_names)
            self.locations_names.remove(name)
            position = choice([p for p in points if p not in used])
            used.add(position)
            court = Location(
                len(self.map.manager.locations) + 1,
                name=name,
                position=position,
                location_type=location_type,
                owner=lord
            )
            self.map.manager.add(court)
            lord.add_fief(court)
        return [p for p in points if p not in used]

    def spawn_villages_at_points(self, points):
        for point in points:
            villages_names = self.locations_names
            location_type = LocationType.village if random() > 0.02 else LocationType.town
            population = (
            65, 240) if location_type == LocationType.village else (500, 1750)
            self.map.manager.add(
                Location(
                    len(self.map.manager.locations) + 1,
                    villages_names.pop(randint(0, len(villages_names) - 1)),
                    position=point,
                    location_type=location_type,
                    population=randint(*population)
                )
            )

    def distribute_fiefs_among_lords(self):
        available = self.map.manager.get_locations_by_owner(owner=None)

        for title in (Title.count, Title.baron, Title.baron, Title.chevalier):
            lords = self.map.manager.get_lords_of_title(title)

            for lord in lords:
                while len(lord.fiefs) < LORDS_FIEFS[title]:
                    pass

    def load_or_spawn_roads_and_regions(self, points):
        # roads and regions are connected because polygon representing map
        # region around a location  contains centroids of the roads
        # connecting this location with adjacent locations
        if self.map.manager.roads and self.map.manager.regions:
            return self.map.manager.roads, self.map.manager.regions
        roads = self.connect_locations_with_roads(self.borders + points)
        regions = self.generate_map_regions(roads, points)
        return roads, regions

    def load_or_spawn_forests(self) -> Dict[Point, List[Tuple[Point, ...]]]:
        if self.map.manager.forests:
            return self.map.manager.forests
        else:
            points = self.get_random_points(FORRESTS_COUNT, TREES_RADIUS)
            return self.spawn_forests(points)

    def spawn_forests(self, points) -> Dict[Point, List[Tuple[Point, ...]]]:
        forests = {}
        trees_count = 0
        for x, y in points:
            trees = []
            for i in range(randint(6, 36)):
                yi = y + choice(range(-6, 6, 1)) * 10
                xi = x + choice(range(-6, 6, 1)) * 15
                tree = ((xi, yi - 7), (xi - 5, yi + 7), (xi + 6, yi + 7))
                trees.append(tree)
                trees_count += 1
            forests[(x, y)] = trees
        print(f'Total number of trees grown: {trees_count}')
        return forests

    def get_random_points(self, required_points_count, radius) -> List[Point]:
        cell_size = int(radius / math.sqrt(2))
        grid: Dict[Tuple[int, int], Any] = self.generate_grid(cell_size)
        grid_rows = self.map.height // cell_size
        grid_columns = self.map.width // cell_size
        points = []
        available_cells = [
            k for k in grid.keys() if k[0] if
            0 < k[0] < grid_columns and 0 < k[1] < grid_rows
        ]
        while required_points_count and available_cells:
            cell = choice(available_cells)
            point = (
                cell[0] * cell_size + randint(1, cell_size),
                cell[1] * cell_size + randint(1, cell_size)
            )
            if self.valid(cell, point, radius, grid, grid_columns, grid_rows):
                grid[cell] = point
                points.append(point)
                required_points_count -= 1
                available_cells.remove(cell)
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
                    dist = math.hypot((other[0] - point[0]),
                                      (other[1] - point[1]))
                    if dist < radius:
                        return False
        return True

    def generate_grid(self, cell_size: int) -> Dict[Tuple[int, int], Any]:
        grid_rows = self.map.height // cell_size
        grid_columns = self.map.width // cell_size
        grid = {
            (c, r): None for c in range(grid_columns) for r in range(grid_rows)
        }
        return grid

    def connect_locations_with_roads(self, points) -> List[Road]:
        shapely_points = MultiPoint(points)
        connections = triangulate(shapely_points, edges=True)
        roads = [(c.coords, c.centroid, c.length) for c in connections]
        curved_roads = self.curve_roads(roads)
        return curved_roads

    def curve_roads(self, roads: List) -> List[Road]:
        curved = []
        for coords, centroid, length in roads:
            points = [p for p in coords]
            for i in range(4, 0, -1):
                start, end = points[-2:]
                if i > 1:
                    angle = calculate_angle(*start, *end) + randint(-15, 15)
                else:
                    angle = calculate_angle(*start, *end)
                dist = distance_2d(start, end) / i
                new_end = move_along_vector(start, dist, angle=angle)
                points.insert(-1, new_end)
            curved.append((points, centroid, length))
        return curved

    @staticmethod
    def generate_map_regions(roads, points) -> Dict[Point, List[Point]]:
        regions: Dict[Point, List[Point]] = {
            p: [] for p in points
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
        self.forests: TerrainElements = {}
        self.roads: List[Tuple[List[Point], ShapelyPoint, float]] = []
        self.regions: Dict[Point, List[Point]] = {}
        self.windrose = PhotoImage(file='windrose.png')
        self.builder = WorldBuilder(self)
        self.application.after(13, self._update)

    def create_map_canvas(self, parent) -> Canvas:
        canvas = Canvas(parent, width=MAP_CANVAS_WIDTH,
                        height=MAP_CANVAS_HEIGHT,
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
        canvas.bind('<Double-1>', self.create_new_location)
        return canvas

    def _update(self):
        # if (not self.roads) and self.manager.lords:
        #     self._build_world()
        if self.application.map_canvas is not None:
            canvas: Canvas = self.application.map_canvas
            self._draw_map(canvas)
        self.application.after(13, self._update)

    def _build_world(self):
        self.roads, self.regions, self.forests = self.builder.build_world()

    def _draw_map(self, canvas):
        canvas.delete('all')
        self._draw_visible_map_contents(canvas)
        self._draw_scale_and_wind_rose(canvas)
        self._draw_minimap(canvas)

    def _draw_visible_map_contents(self, canvas: Canvas):
        zoom = self.zoom
        l, b, r, t = self.viewport
        self._draw_regions(canvas, b, l, r, t, zoom)
        self._draw_forests(canvas, b, l, r, t, zoom)
        self._draw_roads(canvas, b, l, r, t, zoom)
        self._draw_locations(b, canvas, l, r, t, zoom)

    def _draw_roads(self, canvas, b, l, r, t, zoom):
        for i, (road, centroid, length) in enumerate(self.roads):
            if any((l < p[0] * zoom < r and b < p[1] * zoom < t) for p in
                   road):
                points = [(p[0] * zoom - l, p[1] * zoom - b) for p in road]
                canvas.create_line(*points, dash=(6, 3), fill='brown')

    def _draw_regions(self, canvas, b, l, r, t, zoom):
        for location in self.selected_locations:
            region = self.regions[location.position]
            if any((l < p[0] * zoom < r and b < p[1] * zoom < t) for p in
                   region):
                points = [(p[0] * zoom - l, p[1] * zoom - b) for p in region]
                canvas.create_polygon(*points, dash=(6, 3), outline='yellow',
                                      fill='DarkOliveGreen3', width=2)

    def _draw_forests(self, canvas, b, l, r, t, zoom):
        for position, trees in self.forests.items():
            x, y = position
            if (l < x * zoom < r) and (b < y * zoom < t):
                for tree in trees:
                    points = [(p[0] * zoom - l, p[1] * zoom - b) for p in tree]
                    canvas.create_polygon(*points, fill='green')

    def _draw_locations(self, b, canvas, l, r, t, zoom):
        pointed = False
        self.pointed_location = None
        for location in self.manager.locations:
            x, y = location.position[0] * zoom, location.position[1] * zoom
            if l < x < r and b < y < t:
                if not pointed and self.cursor_position is not None:
                    color, pointed = self.if_cursor_points_location(x, y, l, b)
                    if pointed:
                        self.pointed_location = location
                else:
                    color = 'white'
                self._draw_single_location(canvas, color, location, x - l,
                                           y - b)

    def _draw_single_location(self, canvas, color, location, x, y):
        zoom = self.zoom
        text = location.name
        if location in self.selected_locations:
            self._draw_selection_gizmo_around_location(canvas, zoom, x, y)
        if location.type in NAME_ONLY_LOCATIONS:
            self._draw_populated_location(canvas, color, zoom, x, y, location)
        else:
            self._draw_rectanle_icon(canvas, color, zoom, x, y)
            text = location.full_name
        self._draw_location_name(canvas, text, x, y, zoom)

    def _draw_populated_location(self, canvas, color, zoom, x, y, location):
        size_modifier, icons_number = self._population_size_modifier(location)
        size = zoom * (4 + size_modifier)
        if not icons_number:
            return self._draw_house_icon(canvas, color, size, x, y)
        for i in range(0, icons_number):
            angle_offset = 360 / icons_number
            xi, yi = move_along_vector((x, y), size * 3,
                                       angle=angle_offset * i)
            self._draw_house_icon(canvas, color, size, xi, yi)

    @staticmethod
    def _draw_house_icon(canvas, color, size, x, y):
        canvas.create_polygon(
            x - size, y - size, x, y - 2 * size, x + size, y - size, x + size,
            y + size, x - size, y + size, fill=color, outline='black'
        )

    @staticmethod
    def _population_size_modifier(location) -> Tuple[int, int]:
        if location.type == LocationType.village:
            return int(location.population / 100), 0
        elif location.type == LocationType.town:
            return int(location.population / 500), 3
        else:
            return int(location.population / 1500), 5

    @staticmethod
    def _draw_rectanle_icon(canvas, color, zoom, x, y):
        size = 7 * zoom
        canvas.create_rectangle(
            x - size, y - size, x + size, y + size, fill=color, outline='black'
        )

    @staticmethod
    def _draw_abbey_icon(canvas, color, zoom, x, y):
        size = 5 * zoom
        canvas.create_polygon(
            x - size, y - size, x, y - 2 * size, x + size, y - size, x + size,
            y + size, x - size, y + size, fill=color, outline='black'
        )
        Map._draw_cross(canvas, x, y, zoom)

    @staticmethod
    def _draw_cross(canvas, x, y, zoom):
        size = 3 * zoom
        y -= 4 * size
        canvas.create_line(x - size, y, x + size, y, fill='black', width=2)
        canvas.create_line(x, y - size, x, y + size, fill='black', width=2)

    @staticmethod
    def _draw_selection_gizmo_around_location(canvas, zoom, x, y):
        size = 10 * zoom
        canvas.create_rectangle(
            x - size, y - size, x + size, y + size, outline='yellow', width=3
        )

    def if_cursor_points_location(self, x, y, vl, vb) -> Tuple[str, bool]:
        cx, cy = self.cursor_position
        size = 7 * self.zoom
        l, b, r, t = x - size, y - size, x + size, y + size
        if l < cx + vl < r and b < cy + vb < t:
            return 'yellow', True
        else:
            return 'white', False

    @staticmethod
    def _draw_location_name(canvas, text, x, y, zoom):
        font = f'Times {int(12 * zoom)} bold'
        canvas.create_text(x + 10, y, font=font, text=text, anchor='w')

    def _draw_minimap(self, canvas: Canvas):
        canvas.create_rectangle(
            10, 10, 10 + self.width / 100, 10 + self.height / 100,
            fill='white')
        self._draw_locations_points(canvas)
        self._draw_forests_points(canvas)
        self._draw_viewport(canvas)

    def _draw_locations_points(self, canvas):
        for location in self.manager.locations:
            if location.population > 200:
                x, y = location.position
                canvas.create_oval(
                    10 + x / 100, 10 + y / 100, 10 + x / 100, 10 + y / 100,
                    outline='grey30'
                )

    def _draw_forests_points(self, canvas):
        for (x, y), forest in self.forests.items():
            if len(forest) > 25:
                canvas.create_oval(
                    10 + x / 100, 10 + y / 100, 10 + x / 100, 10 + y / 100,
                    outline='green'
                )

    def _draw_viewport(self, canvas):
        canvas.create_rectangle(
            *[10 + (i / 100) / self.zoom for i in self.viewport], outline='red'
        )

    def _draw_scale_and_wind_rose(self, canvas):
        x, y = 525, 70
        canvas.create_image(x, y, image=self.windrose)
        # distance scale:
        x, size = 450, self.zoom * 35
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
            self.selected_locations.clear()
            self.selected_locations.add(location)
            self.application.open_new_or_show_opened_window(location)

    def on_right_click(self, event: EventType):
        canvas: Canvas = event.widget

    def on_mouse_motion(self, event: EventType):
        canvas: Canvas = event.widget
        self.cursor_position = event.x, event.y

    def on_mouse_drag(self, event: EventType):
        if self.cursor_position is not None:
            x, y = self.cursor_position
            self._update_viewport(x - event.x, y - event.y)
        self.cursor_position = event.x, event.y

    def on_mouse_scroll(self, event: EventType):
        ratio = 1 - 1 / (self.zoom / 0.1)
        if event.num == 4 or event.delta == 120:
            self._zoom_out(ratio)
        elif event.num == 5 or event.delta == -120:
            self._zoom_in(ratio)
        self._update_viewport(0, 0)

    def _zoom_out(self, ratio):
        if self.zoom > MIN_ZOOM:
            self.zoom = clamp(self.zoom * ratio, MAX_ZOOM, MIN_ZOOM)
            self.viewport = [v * ratio for v in self.viewport]

    def _zoom_in(self, ratio):
        if self.zoom < MAX_ZOOM:
            self.zoom = clamp(self.zoom / ratio, MAX_ZOOM, MIN_ZOOM)
            self.viewport = [v / ratio for v in self.viewport]

    def _update_viewport(self, dx, dy):
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
            self._update_viewport(new_left - l, new_bottom - b)

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

    def create_new_location(self, event: EventType):
        new_id = len(self.manager.locations) + 1
        l, b, _, _ = self.viewport
        position = event.x + l, event.y + b
        location = Location(new_id, name='', position=position)
        self.manager.add(location)
        self._build_world()
        self.application.open_new_or_show_opened_window(location)
