import re

from kudago_mapper.mappers import RSSMapper, MapperComposite
from kudago_mapper import fields
from kudago_mapper.transforms import MapperTransform, SplitMapperTransform, StackMapperTransform

from .models import Hall, Event, Artist, ArtistThrough, ActionThrough, EventThrough


class HallRSSMapper(RSSMapper):
    type_ = fields.EnsureField('hall')

    class Meta:
        model = Hall
        fields = ('name', 'url', 'ext_id')
        field_map = {'originalUrl': 'url', 'id': 'ext_id', 'type': 'type_'}


class EventRSSMapper(RSSMapper):
    type_ = fields.EnsureField('event')

    class Meta:
        model = Event
        fields = ('url', 'start_date', 'hall', 'ext_id', 'end_date', 'name', 'category',
                  'action', 'price_min', 'price_max')
        field_map = {'originalUrl': 'url', 'date': 'start_date', 'hall_id': 'hall', 'id': 'ext_id',
                     'type': 'type_'}


class ArtistRSSMapper(RSSMapper):
    class Meta:
        model = Artist
        fields = ('name', 'actions',)
        field_map = {'action': 'actions', }


class ModelCommaSeparatedChoiceField(fields.ModelMultipleChoiceField):
    def clean(self, value):
        if value is not None and not isinstance(value, list):
            value = [item.strip() for item in value.split(",")]
        return super(ModelCommaSeparatedChoiceField, self).clean(value)


class ArtistThroughRSSMapper(RSSMapper):
    actions = ModelCommaSeparatedChoiceField(queryset=ActionThrough.objects.all(), to_field_name='ext_id')
    type_ = fields.EnsureField('artist')

    class Meta:
        model = ArtistThrough
        fields = ('ext_id', 'name', )
        field_map = {'id': 'ext_id', 'action': 'actions', 'type': 'type_'}


class RubleField(fields.DecimalField):
    def to_python(self, value):
        matches = re.findall(r'(\d+)\sруб(\s(\d+)\sкоп)?', value)
        value = '{}.{}'.format(matches[0][0], matches[0][2])
        return super().to_python(value)


class TrimField(fields.CharField):
    def __init__(self, *args, **kwargs):
        self.trim_length = kwargs.pop('trim_length')
        super(TrimField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(TrimField, self).clean(value)
        if len(value) > self.trim_length:
            value = '{}...'.format(value[:self.trim_length])
        return value


class EventTransfRSSMapper(RSSMapper):
    price_min = RubleField()
    price_max = RubleField()
    start_date = fields.DateTimeField(input_formats=['%d.%m.%y %H', '%d.%m.%y %H:%M'])
    end_date = fields.DateTimeField(input_formats=['%d.%m.%y %H', '%d.%m.%y %H:%M'])
    name = TrimField(trim_length=5)

    class Meta:
        model = Event
        fields = ('url', 'start_date', 'hall', 'ext_id', 'end_date', 'name',
                  'action', 'price_min', 'price_max')
        field_map = {'originalUrl': 'url', 'date': 'start_date', 'hall_id': 'hall', 'id': 'ext_id'}


class TimesToDurationTransform(MapperTransform):
    def __call__(self, start_date, end_date):
        return {'duration': end_date - start_date}

    class Meta:
        fields = ('start_date', 'end_date')


class IntSplitTransform(SplitMapperTransform):
    def __call__(self, **kwargs):
        res = super(IntSplitTransform, self).__call__(**kwargs)
        return {key: int(val) for key, val in res.items()}


class LowerCharField(fields.CharField):
    def clean(self, value):
        value = super(LowerCharField, self).clean(value)
        return value.lower()


class EventTransfMultipleRSSMapper(EventTransfRSSMapper):
    age_range = fields.CharField()
    category1 = LowerCharField()
    category2 = LowerCharField()
    category3 = LowerCharField()

    ttd_transform = TimesToDurationTransform()
    age_range_transform = IntSplitTransform(from_field='age_range', to_fields=('age_min', 'age_max'), sep='-')
    categories_transform = StackMapperTransform(from_fields=('category1', 'category2', 'category3'),
                                                to_field='category')


class EventTransfRSSMapper(RSSMapper):
    price_min = RubleField()
    price_max = RubleField()
    start_date = fields.DateTimeField(input_formats=['%d.%m.%y %H', '%d.%m.%y %H:%M'])
    end_date = fields.DateTimeField(input_formats=['%d.%m.%y %H', '%d.%m.%y %H:%M'])
    name = TrimField(trim_length=5)

    class Meta:
        model = Event
        fields = ('url', 'start_date', 'hall', 'ext_id', 'end_date', 'name',
                  'action', 'price_min', 'price_max')
        field_map = {'originalUrl': 'url', 'date': 'start_date', 'hall_id': 'hall', 'id': 'ext_id'}


class CheapEventRSSMapper(EventRSSMapper):
    price_min = fields.DecimalField(max_value=400)


class ActionThroughRSSMapper(RSSMapper):
    type_ = fields.EnsureField('action')

    class Meta:
        model = ActionThrough
        fields = '__all__'
        field_map = {'originalUrl': 'url', 'id': 'ext_id', 'type': 'type_'}


class HallActionMapperComposite(MapperComposite):
    class Meta:
        mappers = (HallRSSMapper, ActionThroughRSSMapper)


class EventThroughRSSMapper(EventRSSMapper):
    class Meta:
        model = EventThrough
        # duplicated; get rid of Meta syntax?
        fields = ('url', 'start_date', 'hall', 'ext_id', 'end_date', 'name',
                  'action', 'price_min', 'price_max')
        field_map = {'originalUrl': 'url', 'date': 'start_date', 'hall_id': 'hall', 'id': 'ext_id',
                     'type': 'type_'}


class KassirMapperComposite(MapperComposite):
    class Meta:
        mappers = (HallRSSMapper, ActionThroughRSSMapper, ArtistThroughRSSMapper, EventThroughRSSMapper)
