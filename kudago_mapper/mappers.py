from xml.etree import ElementTree
from itertools import chain

import six
from django.forms import modelformset_factory, ModelForm
from django.forms.forms import DeclarativeFieldsMetaclass
from django.db.models import ForeignKey

from .parsers import XmlListConfig


class M2MThroughSavingModelForm(ModelForm):
    def _save_m2m(self):
        cleaned_data = self.cleaned_data
        opts = self.instance._meta
        for f in chain(opts.many_to_many, opts.private_fields):
            if not hasattr(f, 'save_form_data'):
                continue
            if f.name not in self.fields:
                continue
            if f.name in cleaned_data:
                through_rel = f.remote_field.through
                if through_rel._meta.auto_created:
                    f.save_form_data(self.instance, cleaned_data[f.name])
                else:
                    for el in cleaned_data[f.name]:
                        through_fks = tuple(filter(lambda x: isinstance(x, ForeignKey), through_rel._meta.fields))
                        if len(through_fks) != 2:
                            raise ValueError("Only through tables with 2 foreign keys are supported.")

                        from_field = through_fks[isinstance(self.instance, through_fks[1].related_model)]
                        to_field = through_fks[isinstance(self.instance, through_fks[0].related_model)]

                        through_rel.objects.create(**{from_field.name: self.instance, to_field.name: el})


@six.add_metaclass(DeclarativeFieldsMetaclass)
class Mapper(object):
    def __init__(self, data):
        if not hasattr(self, 'Meta') or not hasattr(self.Meta, 'model'):
            raise ValueError('No model is specified for {}.'.format(self.__class__.__name__))
        self.model = self.Meta.model
        self.fields = self.Meta.fields
        self.field_map = getattr(self.Meta, 'field_map', {})

        declared_fields = self.declared_fields

        class MapperModelForm(M2MThroughSavingModelForm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields.update(declared_fields)

        self.data = self._parse_data(data)
        formdict = self._datalist_to_formdict(self.data)
        self._formset = modelformset_factory(self.model, form=MapperModelForm, fields=self.fields)(formdict)

    def _parse_data(self, data):
        raise NotImplementedError("You should sublcass Mapper and implement the _parse_data method.")

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
