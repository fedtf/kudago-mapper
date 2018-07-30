from django.db import models


class EventBase(models.Model):
    name = models.CharField(max_length=240)
    category = models.CharField(max_length=240)
    price_min = models.DecimalField(max_digits=11, decimal_places=2)
    price_max = models.DecimalField(max_digits=11, decimal_places=2)
    url = models.URLField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    ext_id = models.IntegerField(unique=True, null=True)
    duration = models.DurationField(null=True)
    age_max = models.PositiveIntegerField(null=True)
    age_min = models.PositiveIntegerField(null=True)
    hall = models.ForeignKey('Hall', to_field='ext_id', on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Event(EventBase):
    action = models.ForeignKey('Action', to_field='ext_id', on_delete=models.CASCADE)


class Hall(models.Model):
    name = models.CharField(max_length=240)
    url = models.URLField()
    ext_id = models.IntegerField(unique=True, null=True)


class Action(models.Model):
    name = models.CharField(max_length=240)
    url = models.URLField()
    category = models.CharField(max_length=240)
    ext_id = models.IntegerField(unique=True, null=True)


class Artist(models.Model):
    name = models.CharField(max_length=120)
    actions = models.ManyToManyField('Action')
    ext_id = models.IntegerField(unique=True, null=True)


class ActionThrough(models.Model):
    name = models.CharField(max_length=240)
    url = models.URLField()
    category = models.CharField(max_length=240)
    ext_id = models.IntegerField(unique=True, null=True)


class ArtistThrough(models.Model):
    name = models.CharField(max_length=240)
    actions = models.ManyToManyField('ActionThrough', through='ArtistToAction')
    ext_id = models.IntegerField(unique=True, null=True)


class EventThrough(EventBase):
    action = models.ForeignKey('ActionThrough', to_field='ext_id', on_delete=models.CASCADE)


class ArtistToAction(models.Model):
    action = models.ForeignKey(ActionThrough, to_field='ext_id', on_delete=models.CASCADE)
    artist = models.ForeignKey(ArtistThrough, to_field='ext_id', on_delete=models.CASCADE)
