from django.db import models

from . import partitions


@partitions.make_model_monthly_partitioned(globals())
class Browser(models.Model):
    ua = models.CharField(max_length=100)
    some_value = models.IntegerField(default=0)

    class Meta:
        abstract = True


@partitions.make_model_monthly_partitioned(globals())
class Event(models.Model):
    timestamp = models.DateTimeField()
    browser = partitions.ForeignKeyToPartition(Browser)
    value = models.IntegerField()

    class Meta:
        abstract = True
