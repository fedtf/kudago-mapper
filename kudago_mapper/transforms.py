class MapperTransform(object):
    def __init__(self, *args, **kwargs):
        try:
            self.fields = self.Meta.fields
        except AttributeError:
            self.fields = '__all__'

    def __call__(self, **kwargs):
        raise NotImplementedError("You should subclass MapperTransform and implement the __call__ method.")


class SplitMapperTransform(MapperTransform):
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
    def __init__(self, from_fields, to_field, sep=','):
        super(StackMapperTransform, self).__init__(from_fields, to_field, sep)
        self.from_fields = from_fields
        self.to_field = to_field
        self.sep = sep

    def __call__(self, **kwargs):
        elems = [kwargs[from_field] for from_field in self.from_fields]
        return {self.to_field: self.sep.join(elems)}
