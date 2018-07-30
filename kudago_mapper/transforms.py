class MapperTransform(object):
    """
    Abstract base class for all mapper transforms.
    Subclasses should implement `__call__` method.

    Internal Meta class supports the following properties:
        - fields: mapper fields to be given as arguments to the __call__ method, defaults to all the fields.
    """
    def __init__(self, *args, **kwargs):
        try:
            self.fields = self.Meta.fields
        except AttributeError:
            self.fields = '__all__'

    def __call__(self, **kwargs):
        """
        Perform the transformation.
        :param **kwargs: mapper field values declared in Meta.
        :return: a dictionary which will be added to the mapper output (existing keys will be rewritten).
        """
        raise NotImplementedError("You should subclass MapperTransform and implement the __call__ method.")


class SplitMapperTransform(MapperTransform):
    """
    Map a single string-based field to multiple by splitting its value.
    :param from_field: source field name.
    :param to_fields: target fields names.
    :param sep: separator (default ',').
    """
    def __init__(self, from_field, to_fields, sep=','):
        super(SplitMapperTransform, self).__init__(from_field, to_fields, sep)
        self.from_field = from_field
        self.to_fields = to_fields
        self.sep = sep

    def __call__(self, **kwargs):
        elems = kwargs[self.from_field].split(self.sep)
        # ignoring possible mismatches in length
        return dict(zip(self.to_fields, elems))


class StackMapperTransform(MapperTransform):
    """
    Map multiple string-based fields to a single one by joining their values.
    :param from_fields: source fields names.
    :param to_field: target field name.
    :param sep: separator (default ',').
    """
    def __init__(self, from_fields, to_field, sep=','):
        super(StackMapperTransform, self).__init__(from_fields, to_field, sep)
        self.from_fields = from_fields
        self.to_field = to_field
        self.sep = sep

    def __call__(self, **kwargs):
        elems = [kwargs[from_field] for from_field in self.from_fields]
        return {self.to_field: self.sep.join(elems)}
