import re

from django import forms

from kudago_mapper.mappers import XMLMapper
from kudago_mapper.transforms import MapperTransform, SplitMapperTransform, StackMapperTransform

from .models import Hall, Event, Artist, ArtistThrough, ActionThrough


class HallXMLMapper(XMLMapper):
    class Meta:
        model = Hall
        fields = ('name', 'url', 'ext_id')
        field_map = {'originalUrl': 'url', 'id': 'ext_id'}


class EventXMLMapper(XMLMapper):
    class Meta:
        model = Event
        fields = ('url', 'start_date', 'hall', 'ext_id', 'end_date', 'name', 'category',
                  'action', 'price_min', 'price_max')
        field_map = {'originalUrl': 'url', 'date': 'start_date', 'hall_id': 'hall', 'id': 'ext_id'}


class ArtistXMLMapper(XMLMapper):
    class Meta:
        model = Artist
        fields = ('name', 'actions',)
        field_map = {'action': 'actions'}


class ModelCommaSeparatedChoiceField(forms.ModelMultipleChoiceField):
    def clean(self, value):
        if value is not None and not isinstance(value, list):
            value = [item.strip() for item in value.split(",")]
        return super(ModelCommaSeparatedChoiceField, self).clean(value)


class ArtistThroughXMLMapper(XMLMapper):
    actions = ModelCommaSeparatedChoiceField(queryset=ActionThrough.objects.all(), to_field_name='ext_id')

    class Meta:
        model = ArtistThrough
        fields = ('ext_id', 'name', )
        field_map = {'id': 'ext_id', 'action': 'actions'}


class RubleField(forms.DecimalField):
    def to_python(self, value):
        matches = re.findall(r'(\d+)\sруб(\s(\d+)\sкоп)?', value)
        value = '{}.{}'.format(matches[0][0], matches[0][2])
        return super().to_python(value)


class TrimField(forms.CharField):
    def __init__(self, *args, **kwargs):
        self.trim_length = kwargs.pop('trim_length')
        super(TrimField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(TrimField, self).clean(value)
        if len(value) > self.trim_length:
            value = '{}...'.format(value[:self.trim_length])
        return value


class EventTransfXMLMapper(XMLMapper):
    price_min = RubleField()
    price_max = RubleField()
    start_date = forms.DateTimeField(input_formats=['%d.%m.%y %H', '%d.%m.%y %H:%M'])
    end_date = forms.DateTimeField(input_formats=['%d.%m.%y %H', '%d.%m.%y %H:%M'])
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


class LowerCharField(forms.CharField):
    def clean(self, value):
        value = super(LowerCharField, self).clean(value)
        return value.lower()

class EventTransfMultipleXMLMapper(EventTransfXMLMapper):
    age_range = forms.CharField()
    category1 = LowerCharField()
    category2 = LowerCharField()
    category3 = LowerCharField()

    ttd_transform = TimesToDurationTransform()
    age_range_transform = IntSplitTransform(from_field='age_range', to_fields=('age_min','age_max'), sep='-')
    categories_transform = StackMapperTransform(from_fields=('category1', 'category2', 'category3'),
                                                to_field='category')
