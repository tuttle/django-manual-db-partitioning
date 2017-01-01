import datetime

from django.db import models

from . import partitions


@partitions.make_model_monthly_partitioned(globals())
class Browser(models.Model):
    ua = models.CharField(max_length=100, unique=True)
    some_value = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.ua


@partitions.make_model_monthly_partitioned(globals())
class Event(models.Model):
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    browser = partitions.ForeignKeyToPartition(Browser, related_name='event_set')
    value = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.timestamp.strftime("%F %T")
