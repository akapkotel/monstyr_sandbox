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

LORDS_VASSALS = {
    Title.client: {},
    Title.chevalier: {Title.client: 2},
    Title.baronet: {Title.client: 4},
    Title.baron: {Title.baronet: 5, Title.chevalier: 5, Title.client: 6},
    # Title.vicecount: {Title.baronet: 6, Title.chevalier: 6, Title.client: 8},
    Title.count: {Title.baron: 4, Title.baronet: 4, Title.chevalier: 4,
                  Title.client: 10},
    # Title.duke: {Title.count: 4, Title.baron: 4, Title.baronet: 3,
    #              Title.chevalier: 1, Title.client: 15},
    }


class LordsManager:
    """Container and manager for all Nobleman instances."""
    names: Dict[Sex, List[str]] = {}
    surnames: List[str]
    prefixes = List[str]
    lords: Set[Nobleman] = set()
    locations: Set[Location] = set()
    discarded: Set = set()

    def __init__(self):
        self.load_data_from_text_files()

    def load_data_from_text_files(self):
        self.names[Sex.man] = self.load_names('m_names.txt')
        self.names[Sex.woman] = self.load_names('f_names.txt')
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

    def create_random_nobleman(self, name: str) -> Nobleman:
        lord = Nobleman(name, randint(16, 61), RAGADAN, Faction.choice(),
                        Title.choice())
        lord.portrait = self.get_generic_portrait_name(lord)
        return lord

    @staticmethod
    def get_generic_portrait_name(lord):
        if lord.title is Title.client:
            return f'portraits/client_{lord.sex.value}.png'
        if lord.age < 25:
            age_part = 'young_'
        else:
            age_part = '' if lord.age < 50 else 'old_'
        return f'portraits/{age_part}noble{lord.sex.value}.png'

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
        print(
            f'Saved {len(self.lords)} lords and {len(self.locations)} locations')

    def _load_data_from_db(self) -> Tuple[Set[Nobleman], Set[Location]]:
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
        return choice([lord for lord in self.lords])

    @lru_cache(maxsize=2048)
    def get_lord_by_name(self, name: str) -> Nobleman:
        return (noble for noble in self.lords if
        name in noble.title_and_name).__next__()

    def get_lords_of_family(self, family_name: str) -> Set[Nobleman]:
        return set(
            noble for noble in self.lords if noble.family_name == family_name)

    def get_lords_of_sex(self, sex: Sex) -> Set[Nobleman]:
        return set(noble for noble in self.lords if noble.sex is sex)

    def get_lords_of_title(self, title: Title = None) -> Set[Nobleman]:
        if title is None:
            return self.lords
        return set(noble for noble in self.lords if noble.title is title)

    def get_lords_of_military_rank(self,
                                   rank: MilitaryRank = MilitaryRank.no_rank) -> Set[Nobleman]:
        if rank is MilitaryRank.no_rank:
            return set(n for n in self.lords if n.military_rank is not rank)
        return set(n for n in self.lords if n.military_rank is rank)

    def get_lords_of_church_title(self, title: ChurchTitle = None) -> Set[
        Nobleman]:
        if title is None:
            return set(noble for noble in self.lords if
                       noble.church_title is not ChurchTitle.no_title)
        return set(
            noble for noble in self.lords if noble.church_title is title)

    def get_potential_vassals_for_lord(self,
                                       lord: Nobleman,
                                       title: Title = None) -> Set[Nobleman]:
        if title is None:
            return set(v for v in self.get_lords_without_liege() if v < lord)
        return self.get_lords_of_title(title).intersection(
            self.get_potential_vassals_for_lord(lord))

    def get_lords_without_liege(self):
        return set(noble for noble in self.lords if noble.liege is None)

    def get_lords_by_faction(self, faction: Faction) -> Set[Nobleman]:
        return set(noble for noble in self.lords if noble.faction is faction)

    def get_locations_of_type(self,
                              locations_type: LocationType = None) -> Set[Location]:
        if locations_type is None:
            return self.locations
        return set(loc for loc in self.locations if loc.type is locations_type)

    def get_locations_by_owner(self, owner: Nobleman) -> Set[Location]:
        return set(loc for loc in self.locations if loc.owner is owner)

    @lru_cache(maxsize=1024)
    def get_location_by_name(self, name: str) -> Location:
        return (loc for loc in self.locations if name in loc.full_name).__next__()

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
                # lord.vassals.discard(vassal)
                # vassal.liege = None
                self.break_feudal_bond(liege, vassal)
            vassal.liege = lord

    @staticmethod
    def break_feudal_bond(lord: Nobleman, vassal: Nobleman):
        lord.vassals.discard(vassal)
        vassal.liege = None

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

    def collection(self, obj: Union[Nobleman, Location]) -> Union[
        Set[Nobleman], Set[Location]]:
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

    def build_feudal_hierarchy(self):
        if not self.enough_lords():
            return
        titles = (Title.count, Title.baron, Title.baronet, Title.chevalier)
        vassals_count = 0
        for title in titles:
            lords = self.get_lords_of_title(title)
            for lord in lords:
                for vassal_title, count in LORDS_VASSALS[lord.title].items():
                    available = self.get_potential_vassals_for_lord(lord, vassal_title)
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
        real_numbners = {
            Title.count: len(self.get_lords_of_title(Title.count)),
            Title.baron: len(self.get_lords_of_title(Title.baron)),
            Title.baronet: len(self.get_lords_of_title(Title.baronet)),
            Title.chevalier: len(self.get_lords_of_title(Title.chevalier)),
            Title.client: len(self.get_lords_of_title(Title.client)),
            }

        counter = {Title.baron: 0, Title.baronet: 0, Title.chevalier: 0,
                  Title.client: 0}

        for title, vassals in LORDS_VASSALS.items():
            for i in range(real_numbners[title]):
                for lower_title, value in vassals.items():
                    counter[lower_title] += value

        for title, count in counter.items():
            if count > real_numbners[title]:
                print(f'Not enaugh lords of title: {title.value}, '
                      f'required: {count}, actual: {real_numbners[title]}')
                return False
        else:
            print('ok', counter)
            return True


if __name__ == '__main__':
    manager = LordsManager()
    manager.create_lords_set(1552)
    manager.build_feudal_hierarchy()
    manager.save()
