import hashlib

from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT


class GocPkCacheMixin(object):
    @classmethod
    def get_goccache_key(cls, params):
        """
        Create cache key from the object values.
        The dict is converted to a hash string first.
        """
        params_string = ' '.join(
            '%s=%s' % (k, params[k]) for k in sorted(params)
        )

        params_hash = hashlib.sha256(
            params_string.encode('UTF-8')
        ).hexdigest()

        key = 'gocpkcache-%s-%s' % (
            # a model name like 'Browser'
            cls._meta.object_name,
            # a hash of params, because the remote cache server may not support
            # all characters in raw string as key
            params_hash,
        )

        return key

    @classmethod
    def get_or_create_cached_pk_for(cls, gocpk_cache_timeout=DEFAULT_TIMEOUT, **kwargs):
        """
        Returns the cached primary key for unique object value.
        """
        key = cls.get_goccache_key(kwargs)
        pk = cache.get(key)

        if pk is None:
            pk = cls.objects.get_or_create(**kwargs)[0].pk
            cache.set(key, pk, timeout=gocpk_cache_timeout)

        return pk
