#!/usr/bin/env python

from random import randint, choice, random as random_float
from enum import Enum


class MyEnum(Enum):

    @classmethod
    def hierarchy(cls):
        return {
            title: i for i, title in enumerate(cls)
        }

    def __gt__(self, other):
        return self.hierarchy()[self] > other.hierarchy()[other]

    @classmethod
    def choice(cls):
        return choice([t for i, t in enumerate(cls)])

        # index = randint(2, len(cls) - 1)
        # return [x for i, x in enumerate(cls) if i == index][0]


class Sex(MyEnum):
    man = 'man'
    woman = 'woman'

    @classmethod
    def choice(cls):
        return Sex.man if random_float() < 0.75 else Sex.woman


class Title(MyEnum):
    client = 'client'
    chevalier = 'chevalier'
    baronet = 'baronet'
    baron = 'baron'
    vicecount = 'vicecount'
    count = 'count'
    duke = 'duke'
    prince = 'prince'
    king = 'king'


class ChurchTitle(MyEnum):
    no_title = ''
    priest = 'priest'  # prezbiter / proboszcz
    decanus = 'decanus'  # diakon
    prelate = 'prelate'  # prałat
    canonicus = 'canonicus'  # kanonik
    bishop = 'bishop'
    any = 'any'

    @classmethod
    def choice(cls):
        return choice([t for i, t in enumerate(cls)][:-1])


class AbbeyRank(MyEnum):
    no_rank = ''
    monk = 'monk'
    prior = 'prior'
    abbot = 'abbot'


class MilitaryRank(MyEnum):
    no_rank = ''
    sergeant = 'sergeant'
    captain = 'captain'
    colonel = 'colonel'
    general = 'general'
    marshal = 'marshal'
    any = 'any'

    @classmethod
    def choice(cls):
        return choice([t for i, t in enumerate(cls)][:-1])


class Faction(MyEnum):
    royalists = 'royalists'
    nationalists = 'nationalists'
    neutral = 'neutral'

    @classmethod
    def choice(cls):
        return choice([t for i, t in enumerate(Faction)])


class LocationType(MyEnum):
    village = 'village'
    town = 'town'
    city = 'city'
    palace = 'palace'
    windmill = 'windmill'
    watermill = 'watermill'
    winery = 'winery'
    brewery = 'brewery'
    mine = 'mine'
    quarry = 'quarry'
    church = 'church'
    hideout = 'hideout'
    military_post = 'military post'
    caste = 'castle'
    fortress = 'fortress'
    printing_house = 'printing house'
    hunting_court = 'hunting manor'
    villa = 'villa'
    sawmill = 'sawmill'
    chapel = 'chapel'
    forest = 'forest'
    manufacture = 'manufacture'
    abbey = 'abbey'
    inn = 'inn'
    manor_house = 'manor house'
    stable = 'stable'
    hospital = 'hospital'
    fortified_tower = 'fortified tower'
    castellum = 'castellum'
    grange = 'grange'
    plantation = 'plantation'
    shipyard = 'shipyard'
