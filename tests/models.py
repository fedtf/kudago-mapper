from django.db import models


class Event(models.Model):
    category = models.CharField(max_length=120)
    hall = models.ForeignKey('Hall', to_field='ext_id', on_delete=models.CASCADE)
    action = models.ForeignKey('Action', to_field='ext_id', on_delete=models.CASCADE)
    price_min = models.DecimalField(max_digits=11, decimal_places=2)
    price_max = models.DecimalField(max_digits=11, decimal_places=2)
    url = models.URLField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    ext_id = models.IntegerField(unique=True, null=True)


class Hall(models.Model):
    name = models.CharField(max_length=120)
    url = models.URLField()
    ext_id = models.IntegerField(unique=True, null=True)


class Action(models.Model):
    name = models.CharField(max_length=120)
    url = models.URLField()
    category = models.CharField(max_length=120)
    ext_id = models.IntegerField(unique=True, null=True)


class Artist(models.Model):
    name = models.CharField(max_length=120)
    actions = models.ManyToManyField('Action')
    ext_id = models.IntegerField(unique=True, null=True)


class ActionThrough(models.Model):
    name = models.CharField(max_length=120)
    url = models.URLField()
    category = models.CharField(max_length=120)
    ext_id = models.IntegerField(unique=True, null=True)


class ArtistThrough(models.Model):
    name = models.CharField(max_length=120)
    actions = models.ManyToManyField('ActionThrough', through='ArtistToAction')
    ext_id = models.IntegerField(unique=True, null=True)


class ArtistToAction(models.Model):
    action = models.ForeignKey(ActionThrough, to_field='ext_id', on_delete=models.CASCADE)
    artist = models.ForeignKey(ArtistThrough, to_field='ext_id', on_delete=models.CASCADE)
