from xml.etree import ElementTree

import six
from django.forms import modelformset_factory, BaseModelFormSet
from django.conf import settings

from kudago_mapper.parsers import XmlListConfig
from kudago_mapper.utils import DeclarativeMapperMetaclass, M2MThroughSavingModelForm
from kudago_mapper.fields import Field


DEFAULT_MAX_ITEMS = 2000


@six.add_metaclass(DeclarativeMapperMetaclass)
class Mapper(object):
    """
    Abstract base class for all the mappers.
    Subclasses should implement `parse_data` method.

    Internal Meta class supports the following properties:
        - model: model corresponding to the mapper (required)
        - fields: model fields to be parsed (required)
        - field_map: mapping from the mapper field names to the model field names

    Any fields declared on the class will be added to the model fields.
    """
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

        class MapperModelFormSet(BaseModelFormSet):
            def save_new_objects(self, commit=True):
                self.new_objects = []
                for form in self.extra_forms:
                    if not form.has_changed():
                        continue
                    if self.can_delete and self._should_delete_form(form):
                        continue
                    try:
                        self.new_objects.append(self.save_new(form, commit=commit))
                    except ValueError:
                        continue
                    if not commit:
                        self.saved_forms.append(form)
                return self.new_objects

        self.data = self.parse_data(data)
        formdict = self._datalist_to_formdict(self.data)
        max_num = getattr(self.Meta, 'max_items', getattr(settings, 'KUDAGO_MAPPER_MAX_ITEMS', DEFAULT_MAX_ITEMS))
        self._formset = modelformset_factory(self.model, form=MapperModelForm, formset=MapperModelFormSet,
                                             fields=self.fields, max_num=max_num)(formdict)

    def parse_data(self, data):
        """
        Abstract method to be implemented by subclasses.
        :param data: raw data.
        :return: parsed data as a list of dictionaries corresponding to objects.
        """
        raise NotImplementedError("You should subclass Mapper and implement the parse_data method.")

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

    def save(self, commit=True, raise_invalid=False):
        """
        Create and (possibly) save the parsed objects.
        :param commit: if True (default), objects will be saved to the database.
        :param raise_invalid: if False (default), invalid objects will be ignored and valid ones will be saved;
        otherwise, invalid objects will raise an error and nothing will be saved.
        :returns: a list of objects created.
        """
        if not self._formset.is_valid() and raise_invalid:
            raise ValueError("The following errors were found: {}".format(self._formset.errors))

        return self._formset.save(commit=commit)


class RSSMapper(Mapper):
    """
    Mapper for xml input of type
    <root>
    <item>...</item>
    <item>...</item>
    ...
    </root>
    where each item corresponds to an object.
    """
    def parse_data(self, data):
        data = XmlListConfig(ElementTree.fromstring(data))
        return data


class MapperComposite(object):
    """
    Represents a composition of mappers applied on the input with objects of multiple classes.

    Internal Meta class supports the following properties:
        - mappers: an iterable of at least 2 Mapper subclasses (required)
    """
    def __init__(self, payload):
        if not hasattr(self, 'Meta') or not hasattr(self.Meta, 'mappers') or len(self.Meta.mappers) < 2:
            raise ValueError('{} requires at least 2 mappers.'.format(self.__class__.__name__))
        self.mappers = []

        for mapper in self.Meta.mappers:
            self.mappers.append(mapper(payload))

    def save(self, commit=True):
        """
        Create and (possibly) save the parsed objects.
        :param commit: if True (default), objects will be saved to the database.
        :returns: a list of objects created.
        """
        res = []
        for mapper in self.mappers:
            res.extend(mapper.save(commit=commit))

        return res
