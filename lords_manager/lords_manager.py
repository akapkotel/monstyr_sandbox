#!/usr/bin/env python
import os
import shelve
import string

from typing import List, Dict, Set, Union, Optional
from functools import lru_cache
from random import random, choice, randint
from typing import Tuple
from shapely.geometry import Point as ShapelyPoint

from utils.enums import (
    Title, Sex, Nationality, Faction, ChurchTitle, MilitaryRank, LocationType
)
from utils.classes import Nobleman, Location
from utils.functions import Point

LORDS_FIEFS = {  # title: (min fiefs, max fiefs)
    Title.client: 0,
    Title.chevalier: 3,
    Title.baronet: 5,
    Title.baron: 8,
    Title.vicecount: 12,
    Title.count: 15,
    Title.duke: 18,
    Title.prince: 24,
    Title.king: 30
}

LORDS_VASSALS = {
    Title.client: {},
    Title.chevalier: {Title.client: 2},
    Title.baronet: {Title.chevalier: 4},
    Title.baron: {Title.baronet: 5, Title.chevalier: 5, Title.client: 6},
    # Title.vicecount: {Title.baronet: 6, Title.chevalier: 6, Title.client: 8},
    Title.count: {Title.baron: 4, Title.baronet: 4, Title.chevalier: 4,
                  Title.client: 10},
    # Title.duke: {Title.count: 4, Title.baron: 4, Title.baronet: 3,
    #              Title.chevalier: 1, Title.client: 15},
}


FORBIDEN = ('x', 'y', 'j', 'k', 'w')
LETTERS = string.ascii_lowercase
ALLOWED = [l for l in LETTERS if l not in FORBIDEN]
VOVELS = 'a', 'o', 'i', 'u', 'e'
CONSONANTS = [l for l in ALLOWED if l not in VOVELS]


TerrainElements = Dict[Point, List[Tuple[Point, ...]]]


class LordsManager:
    """Container and manager for all Nobleman instances."""

    def __init__(self):
        self.locations_names = []
        self.names: Dict[Sex, List[str]] = {}
        self.surnames: List[str]
        self.prefixes = List[str]
        self._lords: Dict[int, Nobleman] = {}
        self._locations: Dict[int, Location] = {}
        self.roads: List[Tuple[List[Point], ShapelyPoint, float]] = []
        self.regions: Dict[Point, List[Point]] = {}
        self.forests: TerrainElements = {}
        self.hills: TerrainElements = {}
        self.discarded: Set = set()
        self.ready = self.load_data_from_text_files()

    def load_data_from_text_files(self):
        try:
            self.names[Sex.man] = self.load_names('m_names.txt')
            self.names[Sex.woman] = self.load_names('f_names.txt')
            self.surnames = self.load_names('surnames.txt')
            self.prefixes = self.load_names('prefixes.txt')
            self.locations_names = list(set(self.load_names('locations.txt')))
            return True
        except Exception as e:
            print(str(e))
            return False

    @property
    def lords(self):
        return self._lords.values()

    @property
    def locations(self):
        return self._locations.values()

    @staticmethod
    def load_names(file_name: str) -> List[str]:
        """Load list of str names from txt file."""
        full_path_name = os.path.join(os.getcwd(), 'names', file_name)
        with open(full_path_name, 'r') as file:
            names = file.read().rstrip('\n').split(',')
        return sorted(names)

    def load_full_lords_names_set(self,
                                  file_name: str = 'lords.txt',
                                  required_lords: int = 0) -> Set[str]:
        """
        Load full lords names in format {first_name family-first_name} from txt
        file, check if there is enough names, generate random names if not,
        and return Set of names.
        """
        lords_names = set()
        while len(lords_names) < required_lords:
            lords_names.add(self.random_lord_name(Sex.choice()))
        with open(os.path.join(os.getcwd(), 'databases', file_name), 'w') as file:
            file.write(','.join(lords_names))
        return lords_names

    def random_lord_name(self, sex: Sex) -> str:
        """
        Get single nobleman first_name in format: <first_name prefix
        family-first_name> which fits to the gender of the lord.
        """
        name = choice(self.names[sex])
        return f'{name} {choice(self.prefixes)} {choice(self.surnames)}'

    def create_lords_set(self, lords_number: int = 0):
        names = list(
            self.load_full_lords_names_set(required_lords=lords_number))

        numbers = {Title.baron: 28, Title.baronet: 160,
                   Title.chevalier: 167, Title.client: 1192}
        counts = ['Giovanni di Castiliogne', 'Giovanni di Firenze',
                  'Vittorio di Stravicii', 'Amadeus da Orsini',
                  'Agostino di Mozzenigo']

        self._lords = {i: Nobleman(i, name, 20, Nationality.ragada,
                                   Faction.choice(), Title.count)
                       for i, name in enumerate(counts, start=0)}

        for title, counter in numbers.items():
            for i in range(counter):
                name = choice(names)
                names.remove(name)
                lord = self.create_random_nobleman(name, title=title)
                self._lords[lord.id] = lord

    def create_random_nobleman(self,
                               name: str,
                               nationality: Nationality = None,
                               title: Title = None) -> Nobleman:
        lord = Nobleman(len(self._lords), name, randint(16, 65),
                        nationality or Nationality.choice(),
                        Faction.choice(),
                        Title.choice() if title is None else title)
        lord.portrait = self.get_generic_portrait_name(lord)
        return lord

    @staticmethod
    def get_generic_portrait_name(lord):
        if lord.title is Title.client:
            return f'portraits/client {lord.sex.value}.png'
        if lord.age < 25:
            age_part = 'young '
        else:
            age_part = '' if lord.age < 50 else 'old '
        return f'portraits/{age_part}noble{lord.sex.value}.png'

    def _save_data_to_db(self, convert_data: bool):
        full_path_name = os.path.join(os.getcwd(), 'databases', 'lords.sdb')
        if self.discarded and os.path.exists(full_path_name):
            os.remove(full_path_name)
        with shelve.open(full_path_name, 'c') as file:
            for lord in (l for l in self.lords if l not in self.discarded):
                if convert_data:
                    file[f'lord: {lord.id}'] = lord.prepare_to_save(self)
                else:
                    file[f'lord: {lord.id}'] = lord
            for location in (l for l in self.locations if l not in self.discarded):
                file[f'location: {location.id}'] = location.prepare_to_save(self)
            file['roads'] = self.roads
            file['regions'] = self.regions
            file['forests'] = self.forests
        print(f'Saved {len(self._lords)} lords, {len(self._locations)}'
              f' locations, {sum([len(f) for f in self.forests.values()])} '
              f'trees and {len(self.roads)} roads.')

    def prepare_to_save(self,
                        instance: Union[Nobleman, Location]) -> Union[Nobleman, Location]:
        """
        When saving instances of Nobleman and location replace their
        references to other instances with these instances id's. It helps
        keeping our shelve file small, loading time short, and references
        correct, since id's are not changing, when instances attributes are
        modified.
        """
        return instance.prepare_to_save(manager=self)

    def convert_ids_to_instances(self, instance: Union[Nobleman, Location]):
        # Since we saved our instances with id's instead of the other objects
        # references, we need to get_data our references back, when loading our
        # instance:
        functions = self.get_location_of_id, self.get_lord_of_id
        return instance.convert_ids_to_instances(*functions)

    def _load_data_from_db(self):
        full_path_name = os.path.join(os.getcwd(), 'databases', 'lords.sdb')
        with shelve.open(full_path_name, 'r') as file:
            for elem in file:
                instance = file[elem]
                if isinstance(instance, Nobleman):
                    self._lords[instance.id] = instance
                elif isinstance(instance, List):
                    self.roads = instance
                elif isinstance(instance, Dict):
                    if elem == 'regions':
                        self.regions = instance
                    else:
                        self.forests = instance
                else:
                    self._locations[instance.id] = instance
        print(f'Loaded {len(self._lords)} lords, {len(self._locations)}'
              f' locations, {sum([len(f) for f in self.forests.values()])} '
              f'trees and {len(self.roads)} roads.')

    def random_lord(self) -> Nobleman:
        return choice([lord for lord in self.lords])

    def get_lord_of_id(self, id: Union[int, Nobleman]) -> Nobleman:
        try:
            return self._lords[id]
        except KeyError:
            return self._lords[id.id]

    @lru_cache(maxsize=2048)
    def get_lord_by_name(self, name: str) -> Nobleman:
        return next((noble for noble in self.lords if name in noble.title_and_name))

    def get_lords_of_family(self, family_name: str) -> Set[Nobleman]:
        return {noble for noble in self.lords if noble.family_name == family_name}

    def get_lords_of_sex(self, sex: Sex) -> Set[Nobleman]:
        return {noble for noble in self.lords if noble.sex is sex}

    def get_lords_of_title(self, title: Title = None) -> Set[Nobleman]:
        if title is None:
            return set(self.lords)
        return {
            n for n in self.lords if n.title is title and self.is_not_spouse(n)
        }

    @staticmethod
    def is_not_spouse(nobleman: Nobleman) -> bool:
        return nobleman.title == Title.client or len(nobleman.vassals) > 0

    def get_lords_of_military_rank(self,
                                   rank: MilitaryRank = None) -> Set[Nobleman]:
        if rank is None:
            return {n for n in self.lords if n.military_rank is not MilitaryRank.no_rank}
        return {n for n in self.lords if n.military_rank is rank}

    def get_lords_of_church_title(self, title: ChurchTitle = None) -> Set[Nobleman]:
        if title is None:
            return {noble for noble in self.lords if
                       noble.church_title is not ChurchTitle.no_title}
        return {noble for noble in self.lords if noble.church_title is title}

    def get_potential_vassals_for_lord(self,
                                       lord: Nobleman,
                                       title: Title = None) -> Set[Nobleman]:
        potential = set(v for v in self.get_lords_without_liege() if v < lord)
        if title is not None:
            potential = set(v for v in potential if v.title is title)
        potential.discard(lord)
        return potential

    def get_lords_without_liege(self) -> Set[Nobleman]:
        return {noble for noble in self.lords if noble.liege is None}

    def get_lords_by_faction(self, faction: Faction) -> Set[Nobleman]:
        return {noble for noble in self.lords if noble.faction is faction}

    def get_locations_of_type(self,
                              locations_type: LocationType = None) -> Set[
        Location]:
        if locations_type is None:
            return set(self.locations)
        return {loc for loc in self.locations if loc.type is locations_type}

    def get_locations_by_owner(self,
                               owner: Optional[Nobleman] = None) -> Set[Location]:
        return {loc for loc in self.locations if loc.owner is owner}

    def get_location_of_id(self, id: Union[int, Location]) -> Location:
        try:
            return self._locations[id]
        except KeyError:
            return self._locations[id.id]

    @lru_cache(maxsize=1024)
    def get_location_by_name(self, name: str) -> Location:
        return next((loc for loc in self.locations if name == loc.name))

    def get_vassals_of(self, liege: Union[Nobleman, str]) -> Set[Nobleman]:
        if isinstance(liege, str):
            liege = self.get_lord_by_name(name=liege)
        return liege.vassals

    def set_feudal_bond(self, lord: Nobleman, vassal: Nobleman):
        """
        Set lord as liege of vassal and add vassal to lord's vassals set. If
        vassal already has liege, remove vassal from liege vassals.
        """
        if lord > vassal:
            lord.vassals.add(vassal)
            if (liege := vassal.liege) is not None:
                self.break_feudal_bond(liege, vassal)
            vassal.liege = lord

    @staticmethod
    def break_feudal_bond(lord: Nobleman, vassal: Nobleman):
        lord.vassals.discard(vassal)
        vassal.liege = None

    def add(self, new_object: Union[Nobleman, Location]):
        if isinstance(new_object, Location):
            self._locations[new_object.id] = new_object
        else:
            self._lords[new_object.id] = new_object

    def discard(self, discarded: Union[Nobleman, Location]):
        self.discarded.add(discarded)
        if isinstance(discarded, Nobleman):
            del self._lords[discarded.id]
        else:
            del self._locations[discarded.id]

    def clear(self, all=False, _lords=False, _locations=False, roads=False,
              forests=False, hills=False):
        names = locals()
        for name in (n for n in names if n != 'self' and (names['all'] or names[n])):
            try:
                self.discarded.update(getattr(self, name))
            except (TypeError, AttributeError):
                pass
            if name != 'all':
                self.__dict__[name].clear()

    @staticmethod
    def clear_db():
        import shelve
        with shelve.open('../noblemen.sdb', 'c') as file:
            file.clear()

    def save(self, create=False):
        self._save_data_to_db(create)

    def load(self):
        self._load_data_from_db()

    def __contains__(self, lord: Nobleman):
        return lord in self._lords

    def __len__(self):
        return len(self._lords)

    def build_feudal_hierarchy(self):
        """
        Assign correct amount of vassals of all titles for each Nobleman.
        """
        if not self.enough_lords():
            return
        titles = (Title.count, Title.baron, Title.baronet, Title.chevalier)
        vassals_count = 0
        for title in titles:
            lords = self.get_lords_of_title(title)
            for lord in lords:
                for vassal_title, count in LORDS_VASSALS[lord.title].items():
                    available = self.get_potential_vassals_for_lord(lord,
                                                                    vassal_title)
                    for i in range(count):
                        if len(lord.vassals_of_title(vassal_title)) == count:
                            continue
                        try:
                            new_vassal = choice(list(available))
                        except IndexError:
                            print(title, vassal_title)
                        else:
                            self.set_feudal_bond(lord, new_vassal)
                            vassals_count += 1
                print(f'Added {len(lord.vassals)} vassals')
                print(f'Vassals count: {vassals_count}')

    def enough_lords(self):
        """
        Check if there is enough number od Nobleman of each Title to get_data
        correct amount of vassals for each lord in game.
        """
        real_numbers = {
            Title.count: len(self.get_lords_of_title(Title.count)),
            Title.baron: len(self.get_lords_of_title(Title.baron)),
            Title.baronet: len(self.get_lords_of_title(Title.baronet)),
            Title.chevalier: len(self.get_lords_of_title(Title.chevalier)),
            Title.client: len(self.get_lords_of_title(Title.client)),
        }

        counter = {Title.baron: 0, Title.baronet: 0, Title.chevalier: 0,
                   Title.client: 0}

        for title, vassals in LORDS_VASSALS.items():
            for i in range(real_numbers[title]):
                for lower_title, value in vassals.items():
                    counter[lower_title] += value

        for title, count in counter.items():
            if count > real_numbers[title]:
                print(f'Not enough lords of title: {title.value}, '
                      f'required: {count}, actual: {real_numbers[title]}')
                return False
        return True

    def add_spouses(self):
        unmarried = {l for l in self.lords if l.spouse is None and random() > 0.25}
        for lord in (n for n in unmarried if n.title is not Title.client):
            sex = Sex.man if lord.sex is Sex.woman else Sex.woman
            name = choice(self.names[sex])
            prefix = lord.prefix
            surname = lord.family_name
            full_name = f'{name} {prefix} {surname}'
            min_age = lord.age - 10 if sex is Sex.woman else lord.age
            max_age = lord.age if sex is Sex.woman else lord.age + 10
            age = randint(min_age, max_age)
            id = len(self.lords)
            spouse = Nobleman(id, full_name, age, title=lord.title)
            spouse.portrait = self.get_generic_portrait_name(spouse)
            self.prepare_to_save(spouse)
            self._lords[id] = spouse
            self.convert_ids_to_instances(lord)
            lord.spouse = spouse
            self.prepare_to_save(lord)
        self.save()

    def make_marriages(self):
        raise NotImplementedError


if __name__ == '__main__':
    manager = LordsManager()
    manager.create_lords_set(1552)
    manager.build_feudal_hierarchy()
    manager.save(create=True)
    manager.add_spouses()
