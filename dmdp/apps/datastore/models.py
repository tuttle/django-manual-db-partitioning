import datetime
import hashlib

from django.db import models
from django.core.cache import cache

from . import partitions


@partitions.make_model_monthly_partitioned(globals())
class Browser(models.Model):
    """
    A table for lookups. (referenced)
    """
    ua = models.CharField(max_length=100, unique=True)
    some_value = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.ua

    @classmethod
    def get_or_create_cached_pk_for(cls, ua):
        """
        Returns the cached primary key for unique object value.
        """
        key = 'idcache-%s-%s' % (
            # a string like 'Browser_2016_11'
            cls._meta.object_name,
            # a hash, because the remote cache server may not support all characters in raw string as key
            hashlib.sha256(ua.encode('UTF-8')).hexdigest(),
        )
        pk = cache.get(key)
        if pk is None:
            pk = cls.objects.get_or_create(ua=ua)[0].pk
            cache.set(key, pk)

        return pk


@partitions.make_model_monthly_partitioned(globals())
class Event(models.Model):
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    browser = partitions.ForeignKeyToPartition(Browser, related_name='event_set')
    value = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.timestamp.strftime("%F %T")
