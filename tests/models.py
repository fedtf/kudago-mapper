from django.db import models


class Event(models.Model):
    category = models.CharField(max_length=120)
    hall = models.ForeignKey('Hall', on_delete=models.CASCADE)
    action = models.ForeignKey('Action', on_delete=models.CASCADE)
    price_min = models.DecimalField(max_digits=11, decimal_places=2)
    price_max = models.DecimalField(max_digits=11, decimal_places=2)
    url = models.URLField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()


class Hall(models.Model):
    name = models.CharField(max_length=120)
    url = models.URLField()


class Action(models.Model):
    name = models.CharField(max_length=120)
    url = models.URLField()
    category = models.CharField(max_length=120)
