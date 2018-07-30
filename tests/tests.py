import os
import datetime
from decimal import Decimal

from django.test import TestCase

from kudago_mapper.mappers import Mapper, XMLMapper

from .models import Action, Event, Hall, Artist, ActionThrough, ArtistThrough, EventThrough
from .mappers import (HallXMLMapper, EventXMLMapper, ArtistXMLMapper, ArtistThroughXMLMapper,
                      EventTransfXMLMapper, EventTransfMultipleXMLMapper, CheapEventXMLMapper,
                      HallActionMapperComposite, KassirMapperComposite, ActionThroughXMLMapper)


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
        action0 = Action.objects.create(id=10960, ext_id=10960, name='Original Meet 2017',
                                        url='https://spb.kassir.ru/kassir/action/view/10960')
        action1 = Action.objects.create(id=13985, ext_id=13985, name='Балет на льду "Вечер балета"',
                                        url='https://spb.kassir.ru/kassir/action/view/13985')
        hall0 = Hall.objects.create(id=310712, ext_id=310712, name='Городское пространство "Порт Севкабель"',
                                    url='https://spb.kassir.ru/kassir/hall/view/310712')
        hall1 = Hall.objects.create(id=1099, ext_id=1099, name='ДК Выборгский',
                                    url='https://spb.kassir.ru/kassir/hall/view/1099')

        return action0, action1, hall0, hall1

    def test_single_object_created(self):
        payload = get_payload('single_item.xml')

        hall = HallXMLMapper(payload).save()[0]

        self.assertEqual(hall.name, 'Городское пространство "Порт Севкабель"')
        self.assertEqual(hall.url, 'https://spb.kassir.ru/kassir/hall/view/310712')
        self.assertEqual(hall.ext_id, 310712)

        self.assertEqual(Hall.objects.get(ext_id=310712), hall)
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

    def test_custom_fields(self):
        action0 = ActionThrough.objects.create(id=10960, ext_id=10960, name='Original Meet 2017',
                                               url='https://spb.kassir.ru/kassir/action/view/10960')
        action1 = ActionThrough.objects.create(id=13985, ext_id=13985, name='Балет на льду "Вечер балета"',
                                               url='https://spb.kassir.ru/kassir/action/view/13985')

        payload = get_payload('artists2.xml')

        ArtistThroughXMLMapper(payload).save()

        actions = [(action0, action1,), (action0, action1,), (action1,)]
        ext_ids = [210, 526, 926]

        self.assertEqual(actions, [tuple(artist.actions.all()) for artist in ArtistThrough.objects.all()])
        self.assertEqual(ext_ids, list(ArtistThrough.objects.values_list('ext_id', flat=True)))

    def test_single_field_transforms(self):
        self.create_halls_and_actions()

        payload = get_payload('raw_events.xml')

        EventTransfXMLMapper(payload).save()

        # custom parsing
        prices = [(Decimal('400.1'), Decimal('400.2')),
                  (Decimal('400.1'), Decimal('400.2')),
                  (Decimal(500), Decimal(1200)),]
        dates = [(datetime.datetime(2017, 9, 10, 13), datetime.datetime(2017, 9, 10, 20)),
                 (datetime.datetime(2017, 9, 9, 13), datetime.datetime(2017, 9, 9, 21)),
                 (datetime.datetime(2017, 10, 29, 19), datetime.datetime(2017, 10, 29, 19, 1))]

        # custom transform
        names = ['Origi...', 'Origi...', 'Балет']

        self.assertEqual(dates, list(Event.objects.values_list('start_date', 'end_date')))
        self.assertEqual(prices, list(Event.objects.values_list('price_min', 'price_max')))
        self.assertEqual(names, list(Event.objects.values_list('name', flat=True)))

    def test_multiple_field_transforms(self):
        self.create_halls_and_actions()

        payload = get_payload('raw_events.xml')

        EventTransfMultipleXMLMapper(payload).save()

        # field stacking (+ single field transform)
        categories = ['фестивали,музыкальные фестивали,фестивали на открытом воздухе',
                      'фестивали,музыкальные фестивали,фестивали на открытом воздухе',
                      'театр,балет / танец,другое']
        # field aggregation
        durations = [datetime.timedelta(hours=7),
                     datetime.timedelta(hours=8),
                     datetime.timedelta(minutes=1)]
        # field disaggregation
        ages = [(18, 25), (18, 25), (35, 60)]

        self.assertEqual(categories, list(Event.objects.values_list('category', flat=True)))
        self.assertEqual(durations, list(Event.objects.values_list('duration', flat=True)))
        self.assertEqual(ages, list(Event.objects.values_list('age_min', 'age_max')))

    def test_filtering_by_validation(self):
        _, _, hall0, _ = self.create_halls_and_actions()

        payload = get_payload('events.xml')

        CheapEventXMLMapper(payload).save()

        prices = [Decimal(400), Decimal(400)]
        self.assertEqual(prices, list(Event.objects.values_list('price_max', flat=True)))

    def test_multimodel_input(self):
        payload = get_payload('multiple_models.xml')

        HallActionMapperComposite(payload).save()

        hall_names = ['Городское пространство "Порт Севкабель"',
                      'ДК Выборгский', 'ДК Выборгский (Малый зал)',
                      'Концертный Зал Колизей']
        action_names = ['Original Meet 2017',
                        'Балет на льду "Вечер балета"',
                        'Спектакль "Уикенд по-французски"']
        self.assertEqual(hall_names, list(Hall.objects.values_list('name', flat=True)))
        self.assertEqual(action_names, list(ActionThrough.objects.values_list('name', flat=True)))

    def test_linked_multimodel_input(self):
        payload = get_payload('multiple_linked_models.xml')

        KassirMapperComposite(payload).save()

        self.assertEqual(3, ArtistThrough.objects.count())
        self.assertEqual(4, Hall.objects.count())
        self.assertEqual(3, ActionThrough.objects.count())
        self.assertEqual(3, EventThrough.objects.count())

        action0, action1 = list(ActionThrough.objects.all()[:2])
        artist_actions = [(action0, action1,), (action0, action1,), (action1,)]
        event_actions = [action0, action0, action1,]
        hall0, hall1 = list(Hall.objects.all()[:2])
        halls = [hall0, hall0, hall1]

        self.assertEqual(artist_actions, [tuple(artist.actions.all()) for artist in ArtistThrough.objects.all()])
        self.assertEqual(halls, [event.hall for event in EventThrough.objects.all()])
        self.assertEqual(event_actions, [event.action for event in EventThrough.objects.all()])

    def test_max_items(self):
        payload = get_payload('multiple_items.xml')

        hall_mapper = HallXMLMapper(payload)
        self.assertEqual(2000, hall_mapper._formset.max_num)

        with self.settings(KUDAGO_MAPPER_MAX_ITEMS=5000):
            hall_mapper = HallXMLMapper(payload)
            self.assertEqual(5000, hall_mapper._formset.max_num)

            class LargeHallXMLMapper(XMLMapper):
                class Meta:
                    model = Hall
                    max_items = 10000
                    fields = '__all__'

            hall_mapper = LargeHallXMLMapper(payload)
            self.assertEqual(10000, hall_mapper._formset.max_num)
