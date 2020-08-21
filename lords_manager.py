#!/usr/bin/env python

from functools import lru_cache

from classes import *


LORDS_FIEFS = {  # title: (min fiefs, max fiefs)
    Title.client: (0, 0),
    Title.chevalier: (1, 5),
    Title.baronet: (2, 8),
    Title.baron: (3, 10),
    Title.vicecount: (4, 12),
    Title.count: (5, 15),
    Title.duke: (6, 18),
    Title.prince: (8, 24),
    Title.king: (10, 30)
}


class LordsManager:
    """Container and manager for all Nobleman instances."""
    names: List[str]
    surnames: List[str]
    prefixes = List[str]
    lords: Set[Nobleman] = set()
    locations: Set[Location] = set()
    discarded: Set = set()

    def __init__(self):
        self.names = self.load_names('names.txt')
        self.surnames = self.load_names('surnames.txt')
        self.prefixes = self.load_names('prefixes.txt')

    @staticmethod
    def load_names(file_name: str) -> List[str]:
        """Load list of str names from txt file."""
        with open(file_name, 'r') as file:
            names = file.readline().rstrip('\n').split(',')
        return names

    def load_full_lords_names_set(self,
                                  file_name: str = 'lords.txt',
                                  required_lords: int = 0) -> Set[str]:
        """
        Load full lords names in format {first_name family-first_name} from txt file, check if
        there is enough names, generate random names if not, and return Set of names.
        """
        lords_names = set(self.load_names(file_name))
        while len(lords_names) < required_lords:
            lords_names.add(self.random_lord_name(Sex.choice()))
        with open(file_name, 'w') as file:
            file.write(','.join(lords_names))
        return lords_names

    def random_lord_name(self, sex: Sex) -> str:
        """
        Get single nobleman first_name in format: <first_name prefix family-first_name> which fits
        to the gender of the lord.
        """
        name = choice(self.names)
        while name.endswith('a') if sex is Sex.man else not name.endswith('a'):
            name = choice(self.names)
        return f'{name} {choice(self.prefixes)} {choice(self.surnames)}'

    def create_lords_set(self, lords_number: int = 0):
        names = list(self.load_full_lords_names_set(required_lords=lords_number))

        numbers = {Title.baron: 25, Title.baronet: 150,
                   Title.chevalier: 165, Title.client: 600}
        counts = ['Giovanni di Castiliogne', 'Giovanni di Firenze',
                  'Vittorio di Stravicii', 'Amadeus da Orsini',
                  'Agostino di Mozzenigo']

        self.lords = set(
            Nobleman(name, 20, RAGADAN, Faction.choice(), Title.count)
            for name in counts
        )

        for title, counter in numbers.items():
            for i in range(counter):
                name = choice(names)
                names.remove(name)
                self.lords.add(Nobleman(
                    name, randint(20, 65), RAGADAN, Faction.choice(), title)
                )

    @staticmethod
    def create_random_nobleman(name: str) -> Nobleman:
        return Nobleman(name, randint(16, 61), RAGADAN, Faction.choice(), Title.choice())

    def _save_data_to_db(self):
        import shelve
        with shelve.open('noblemen.sdb', 'c') as file:
            for lord in self.lords:
                print(f'saving {lord}')
                file[lord.full_name] = lord
            for location in self.locations:
                print(f'saving {location}')
                file[location.name] = location
            for discarded in self.discarded:
                print(f'deleting {discarded.name}')
                del file[discarded.name]
        print(f'Saved {len(self.lords)} lords and {len(self.locations)} locations')

    @staticmethod
    def _load_data_from_db() -> Tuple[Set[Nobleman], Set[Location]]:
        import shelve
        lords: Set[Nobleman] = set()
        locations: Set[Location] = set()
        with shelve.open('noblemen.sdb', 'r') as file:
            for elem in file:
                print(f'loading {elem}')
                if isinstance(loaded := file[elem], Nobleman):
                    lords.add(file[elem])
                else:
                    locations.add(file[elem])
        print(f'Loaded {len(lords)} lords and {len(locations)} locations.')
        return lords, locations

    def random_lord(self) -> Nobleman:
        index = randint(0, len(self.lords) - 1)
        return (noble for i, noble in enumerate(self.lords) if i == index).__next__()

    @lru_cache(maxsize=1024)
    def get_lord_by_name(self, name: str) -> Nobleman:
        return (noble for noble in self.lords if name in noble.title_and_name).__next__()

    def get_lords_of_family(self, family_name: str) -> Set[Nobleman]:
        return set(noble for noble in self.lords if noble.family_name == family_name)

    def get_lords_of_sex(self, sex: Sex) -> Set[Nobleman]:
        return set(noble for noble in self.lords if noble.sex is sex)

    def get_lords_of_title(self, title: Title = None) -> Set[Nobleman]:
        if title is None:
            return self.lords
        return set(noble for noble in self.lords if noble.title == title)

    def get_lords_of_military_rank(self, rank: MilitaryRank = None) -> Set[Nobleman]:
        if rank is None:
            return set(noble for noble in self.lords if noble.military_rank != MilitaryRank.no_rank)
        return set(noble for noble in self.lords if noble.military_rank == rank)

    def get_lords_of_church_title(self, title: ChurchTitle = None) -> Set[Nobleman]:
        if title is None:
            return set(noble for noble in self.lords if noble.church_title != ChurchTitle.no_title)
        return set(noble for noble in self.lords if noble.church_title == title)

    def get_lords_by_faction(self, faction: Faction) -> Set[Nobleman]:
        return set(noble for noble in self.lords if noble.faction == faction)

    def get_locations_of_type(self, locations_type: LocationType = None) -> Set[Location]:
        if locations_type is None:
            return self.locations
        return set(location for location in self.locations if location.type == locations_type)

    def get_locations_by_owner(self, owner: Nobleman) -> Set[Location]:
        return set(location for location in self.locations if location.owner == owner)

    @lru_cache(maxsize=1024)
    def get_location_by_name(self, location_name: str) -> Location:
        return (loc for loc in self.locations if location_name in loc.full_name).__next__()

    def get_vassals_of(self, liege: Union[Nobleman, str]) -> Set[Nobleman]:
        if isinstance(liege, str):
            liege = self.get_lord_by_name(name=liege)
        return liege.vassals

    def extend(self, *objects: Union[Nobleman, Location]):
        collection = self.collection(objects[0])
        collection.update(objects)

    def add(self, new_object: Union[Nobleman, Location]):
        collection = self.collection(new_object)
        collection.add(new_object)

    def discard(self, discarded: Union[Nobleman, Location]):
        collection = self.collection(discarded)
        collection.discard(discarded)
        self.discarded.add(discarded)

    def collection(self, obj: Union[Nobleman, Location]) -> Union[Set[Nobleman], Set[Location]]:
        return self.lords if isinstance(obj, Nobleman) else self.locations

    def clear(self):
        self.lords.clear()
        self.locations.clear()

    @staticmethod
    def clear_db():
        import shelve
        with shelve.open('noblemen.sdb', 'c') as file:
            file.clear()

    def save(self):
        self._save_data_to_db()

    def load(self):
        self.lords, self.locations = self._load_data_from_db()

    def __contains__(self, lord: Nobleman):
        return lord in self.lords

    def __len__(self):
        return len(self.lords)


if __name__ == '__main__':
    manager = LordsManager()
    manager.create_lords_set(950)
    manager.save()
