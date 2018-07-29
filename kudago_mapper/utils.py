from collections import OrderedDict
from itertools import chain

from django.forms import Field, ModelForm
from django.db.models import ForeignKey

from kudago_mapper.transforms import MapperTransform


class DeclarativeMapperMetaclass(type):
    """Collect Fields and Transforms declared on the base classes."""
    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        current_fields = []
        current_transforms = []
        for key, value in list(attrs.items()):
            if isinstance(value, Field):
                current_fields.append((key, value))
                attrs.pop(key)
            elif isinstance(value, MapperTransform):
                current_transforms.append((key, value))
                attrs.pop(key)
        attrs['declared_fields'] = OrderedDict(current_fields)
        attrs['declared_transforms'] = OrderedDict(current_transforms)

        new_class = super(DeclarativeMapperMetaclass, mcs).__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        declared_fields = OrderedDict()
        declared_transforms = OrderedDict()
        for base in reversed(new_class.__mro__):
            # Collect fields and transforms from base class.
            if hasattr(base, 'declared_fields'):
                declared_fields.update(base.declared_fields)
                declared_transforms.update(base.declared_transforms)

            # Shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_fields:
                    declared_fields.pop(attr)
                if value is None and attr in declared_transforms:
                    declared_transforms.pop(attr)

        new_class.declared_fields = declared_fields
        new_class.declared_transforms = declared_transforms

        return new_class

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        # Remember the order in which form fields are defined.
        return OrderedDict()


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
