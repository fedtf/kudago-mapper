from xml.etree import ElementTree

import six
from django.forms import modelformset_factory, Field

from kudago_mapper.parsers import XmlListConfig
from kudago_mapper.utils import DeclarativeMapperMetaclass, M2MThroughSavingModelForm


@six.add_metaclass(DeclarativeMapperMetaclass)
class Mapper(object):
    def __init__(self, data):
        if not hasattr(self, 'Meta') or not hasattr(self.Meta, 'model'):
            raise ValueError('No model is specified for {}.'.format(self.__class__.__name__))
        self.model = self.Meta.model
        self.fields = self.Meta.fields
        self.field_map = getattr(self.Meta, 'field_map', {})

        transforms = self.declared_transforms

        declared_fields = self.declared_fields

        class MapperModelForm(M2MThroughSavingModelForm):
            def __init__(self, *args, **kwargs):
                super(MapperModelForm, self).__init__(*args, **kwargs)
                self.fields.update(declared_fields)

            def clean(self):
                cleaned_data = super(MapperModelForm, self).clean()
                for name, transform in transforms.items():
                    if transform.fields == '__all__':
                        res = transform(**cleaned_data)
                    else:
                        res = transform(**{field: cleaned_data[field] for field in transform.fields})
                    cleaned_data.update(res)
                    # hack to pass the new fields through checks in construct_instance
                    self._meta.fields = tuple(set(self._meta.fields + tuple(res)))
                    self.fields.update({field: Field() for field in res})
                return cleaned_data

        self.data = self._parse_data(data)
        formdict = self._datalist_to_formdict(self.data)
        self._formset = modelformset_factory(self.model, form=MapperModelForm, fields=self.fields)(formdict)

    def _parse_data(self, data):
        raise NotImplementedError("You should subclass Mapper and implement the _parse_data method.")

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
