from django import forms

from kudago_mapper.mappers import XMLMapper

from .models import Hall, Event, Artist, ArtistThrough, ActionThrough


class HallXMLMapper(XMLMapper):
    class Meta:
        model = Hall
        fields = ('name', 'url', 'ext_id')
        field_map = {'originalUrl': 'url', 'id': 'ext_id'}


class EventXMLMapper(XMLMapper):
    class Meta:
        model = Event
        fields = '__all__'
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
