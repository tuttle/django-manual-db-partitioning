import datetime

from django.db import models

from . import caching, partitions


@partitions.make_model_monthly_partitioned(globals())
class Browser(models.Model, caching.GocPkCacheMixin):
    """
    A table for lookups. (referenced)
    """
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


@partitions.make_model_range_partitioned(5, globals())
class Session(models.Model, caching.GocPkCacheMixin):
    website_id = models.IntegerField()

    class Meta:
        abstract = True


@partitions.make_model_range_partitioned(5, globals())
class Action(models.Model):
    session = partitions.ForeignKeyToPartition(Session, related_name='action_set', null=True, blank=True)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    some_value = models.IntegerField(default=0)

    class Meta:
        abstract = True
