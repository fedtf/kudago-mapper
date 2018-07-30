from django.forms import Field, ValidationError


class EnsureField(Field):
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
