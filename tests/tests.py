import os
import datetime
from decimal import Decimal

from django.test import TestCase

from kudago_mapper.mappers import Mapper

from .models import Action, Event, Hall, Artist
from .mappers import HallXMLMapper, EventXMLMapper, ArtistXMLMapper


from django.forms import modelformset_factory


def get_payload(filepath):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(test_dir, 'xml_cases', filepath), encoding='utf8') as f:
        return f.read()


class MapperTest(TestCase):
    def test_mapper_without_model_raises(self):
        class WithoutMetaMapper(Mapper):
            def _parse_data(self, data):
                pass

        class WithoutModelMapper(WithoutMetaMapper):
            class Meta:
                fields = ('name', 'url',)

        payload = get_payload('single_item.xml')

        with self.assertRaises(ValueError):
            WithoutMetaMapper(payload)

        with self.assertRaises(ValueError):
            WithoutModelMapper(payload)


class XMLMapperTest(TestCase):
    def create_halls_and_actions(self):
        action0 = Action.objects.create(id=10960, name='Original Meet 2017',
                                        url='https://spb.kassir.ru/kassir/action/view/10960')
        action1 = Action.objects.create(id=13985, name='Балет на льду "Вечер балета"',
                                        url='https://spb.kassir.ru/kassir/action/view/13985')
        hall0 = Hall.objects.create(id=310712, name='Городское пространство "Порт Севкабель"',
                                    url='https://spb.kassir.ru/kassir/hall/view/310712')
        hall1 = Hall.objects.create(id=1099, name='ДК Выборгский',
                                    url='https://spb.kassir.ru/kassir/hall/view/1099')

        return action0, action1, hall0, hall1

    def test_single_object_created(self):
        payload = get_payload('single_item.xml')

        hall = HallXMLMapper(payload).save()[0]

        self.assertEqual(hall.name, 'Городское пространство "Порт Севкабель"')
        self.assertEqual(hall.url, 'https://spb.kassir.ru/kassir/hall/view/310712')
        #self.assertEqual(hall.id, 310712)

        #self.assertEqual(Hall.objects.get(id=310712), hall)
        self.assertEqual(Hall.objects.first(), hall)

    def test_multiple_objects_created(self):
        payload = get_payload('multiple_items.xml')

        halls = HallXMLMapper(payload).save()

        names = ['Городское пространство "Порт Севкабель"',
                 'ДК Выборгский', 'ДК Выборгский (Малый зал)',
                 'Концертный Зал Колизей']
        urls = ['https://spb.kassir.ru/kassir/hall/view/310712',
                'https://spb.kassir.ru/kassir/hall/view/1099',
                'https://spb.kassir.ru/kassir/hall/view/1022',
                'https://spb.kassir.ru/kassir/hall/view/1061']
        self.assertEqual(set(halls), set(Hall.objects.all()))
        self.assertEqual(names, list(Hall.objects.values_list('name', flat=True)))
        self.assertEqual(urls, list(Hall.objects.values_list('url', flat=True)))

    def test_create_with_date_decimal_foreign(self):
        _, _, hall0, hall1 = self.create_halls_and_actions()

        payload = get_payload('events.xml')

        EventXMLMapper(payload).save()

        dates = [datetime.datetime(2017, 9, 10, 13),
                 datetime.datetime(2017, 9, 9, 13),
                 datetime.datetime(2017, 10, 29, 19)]
        prices = [Decimal(400), Decimal(400), Decimal(1200)]
        halls = [hall0, hall0, hall1]
        self.assertEqual(dates, list(Event.objects.values_list('start_date', flat=True)))
        self.assertEqual(prices, list(Event.objects.values_list('price_max', flat=True)))
        self.assertEqual(halls, [event.hall for event in Event.objects.all()])

    def test_create_with_m2m(self):
        action0, action1, _, _ = self.create_halls_and_actions()

        payload = get_payload('artists.xml')

        ArtistXMLMapper(payload).save()

        actions = [(action0, action1,), (action0, action1,), (action0, action1)]
        self.assertEqual(actions, [tuple(artist.actions.all()) for artist in Artist.objects.all()])
