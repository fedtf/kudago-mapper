from django.forms import (Field, CharField, IntegerField, DateField, TimeField, # NOQA
                          DateTimeField, DurationField, RegexField, EmailField,
                          URLField, BooleanField, NullBooleanField, ChoiceField,
                          MultipleChoiceField, ComboField, MultiValueField, FloatField,
                          DecimalField, SplitDateTimeField, GenericIPAddressField, FilePathField,
                          SlugField, TypedChoiceField, TypedMultipleChoiceField, UUIDField,
                          ModelChoiceField, ModelMultipleChoiceField)

from django.forms import ValidationError


class EnsureField(Field):
    """
    Represents a Mapper field which ensures that a given property satisfies a condition.
    :param check: if a callable is passed, it is called with the property value as the only argument
    and should return a boolean; otherwise, the property value is checked on equality with the passed value
    """
    def __init__(self, check):
        self.check = check
        super(EnsureField, self).__init__()

    def clean(self, value):
        value = super(EnsureField, self).clean(value)
        if callable(self.check):
            valid = self.check(value)
        else:
            valid = (value == self.check)
        if not valid:
            raise ValidationError('Check failed.')
