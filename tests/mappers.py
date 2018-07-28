from kudago_mapper.mappers import XMLMapper

from .models import Hall, Event, Artist


class HallXMLMapper(XMLMapper):
    class Meta:
        model = Hall
        fields = ('name', 'url',)
        field_map = {'originalUrl': 'url'}


class EventXMLMapper(XMLMapper):
    class Meta:
        model = Event
        fields = '__all__'
        field_map = {'originalUrl': 'url', 'date': 'start_date', 'hall_id': 'hall'}


class ArtistXMLMapper(XMLMapper):
    class Meta:
        model = Artist
        fields = ('name', 'actions',)
        field_map = {'action': 'actions'}
