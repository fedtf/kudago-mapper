import abc
from xml.etree import ElementTree

import six
from django.forms import modelformset_factory

from .parsers import XmlListConfig


@six.add_metaclass(abc.ABCMeta)
class Mapper(object):
    def __init__(self, data):
        if not hasattr(self, 'Meta') or not hasattr(self.Meta, 'model'):
            raise ValueError('No model is specified for {}.'.format(self.__class__.__name__))
        self.model = self.Meta.model
        self.fields = self.Meta.fields
        self.field_map = getattr(self.Meta, 'field_map', {})

        self.data = self._parse_data(data)
        formdict = self._datalist_to_formdict(self.data)
        self._formset = modelformset_factory(self.model, fields=self.fields)(formdict)

    @abc.abstractmethod
    def _parse_data(self, data):
        pass

    def _datalist_to_formdict(self, data):
        formdict = {
            'form-TOTAL_FORMS': str(len(data)),
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
        }
        for i, item in enumerate(data):
            for field in item:
                formdict['form-{}-{}'.format(i, self.field_map.get(field, field))] = item[field]

        return formdict

    def save(self, commit=True):
        if self._formset.is_valid():
            return self._formset.save(commit=commit)
        else:
            raise ValueError("The following errors were found: {}".format(self._formset.errors))


class XMLMapper(Mapper):
    def _parse_data(self, data):
        data = XmlListConfig(ElementTree.fromstring(data))
        return data
