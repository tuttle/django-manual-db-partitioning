import datetime

from django.conf import settings
from django.db.models import ForeignKey
from django.utils import timezone


class ForeignKeyToPartition(object):
    """
    A proxy "field" waiting to be transformed to the real models.ForeignKey pointing
    to the target model's partition of the same month.
    Example::

        @make_model_monthly_partitioned(globals())
        class Event(models.Model):
            ...
            browser = ForeignKeyToPartition(Browser, related_name='event_set')

    """
    def __init__(self, target_partitioned_model, *fk_args, **fk_kwargs):
        self.target_partitioned_model = target_partitioned_model
        self.fk_args = fk_args
        self.fk_kwargs = fk_kwargs


def resolve_month(ym):
    """
    >>> resolve_month(None)
    24204     # integer value of current month 2016-12
    >>> resolve_month(timezone.now())
    24204
    >>> resolve_month( (2017, 1) )
    24205
    >>> resolve_month(+6)
    24210     # six months in the future
    >>> resolve_month(-6)
    24198     # six months in the past
    """
    if isinstance(ym, (tuple, list)):
        y, m = ym
    elif isinstance(ym, (datetime.datetime, datetime.date)):
        y, m = ym.year, ym.month
    elif isinstance(ym, int) or ym is None:
        today = timezone.now()
        y, m = today.year, today.month + (ym or 0)
    else:
        raise RuntimeError("Unsupported argument %r" % ym)

    return y*12 + m


def iter_months(start_ym=None, end_ym=None):
    """
    Returns the iterator of the (year, month) tuples in range from start_ym (default taken from settings).
    Stops at current month by default, but could be overridden.
    Both parameters accept values accepted by resolve_month().

    >>> list(iter_months())   # depends on settings.TIMESTAMP_PARTITIONING_START_YM and current month
    [(2016, 10), (2016, 11), (2016, 12)]
    >>> list(iter_months(end_ym=+6))
    [(2016, 10), (2016, 11), (2016, 12), (2017, 1), (2017, 2), (2017, 3), (2017, 4), (2017, 5), (2017, 6)]
    """
    if not start_ym:
        start_ym = settings.TIMESTAMP_PARTITIONING_START_YM

    months = xrange(
        resolve_month(start_ym) - 1,
        resolve_month(end_ym),
    )

    for ym in months:
        yield (
            ym / 12,
            (ym % 12) + 1,
        )


def make_model_monthly_partitioned(module_globals, start_ym=None, end_ym=+6):
    """
    A model-class decorator. Example:

        @make_model_monthly_partitioned(globals())
        class Event(models.Model):
            ...
            class Meta:
                abstract = True

    This will dynamically create models for monthly partitions in the same module.
    Then it adds static method Event.YM to quickly get appropriate partition model.
    Also an iterator Event.iter_YMs is added to get multiple partitions.
    """
    def maker(model_class):
        name = model_class._meta.object_name

        for year, month in iter_months(start_ym, end_ym):
            model_name = '%s_%04d_%02d' % (name, year, month)

            if model_name in module_globals:
                raise RuntimeError("Model %s already exists!" % model_name)

            class Meta:
                verbose_name = verbose_name_plural = '%s (%04d/%02d)' % (name, year, month)

            attrs = {
                '__module__': module_globals['__name__'],
                'Meta': Meta,
            }

            # Reflect all the ForeignKeyToPartition promises as appropriate ForeignKey fields.

            for fk_field_name, proxy in model_class.__dict__.items():
                if isinstance(proxy, ForeignKeyToPartition):
                    attrs[fk_field_name] = ForeignKey(
                        to=proxy.target_partitioned_model.YM(year, month),
                        *proxy.fk_args,
                        **proxy.fk_kwargs
                    )

            # Dynamically create the model class in the module.

            module_globals[model_name] = type(
                model_name,
                (model_class,),
                attrs,
            )

        def YM(year=None, month=None):
            """
            A static method to retrieve specific model for month partition.
            Accepts either year and month integers or a date/datetime object.

            >>> Event.YM(2016, 12)
            <class 'dmdp.apps.datastore.models.Event_2016_12'>
            >>> Event.YM(timezone.now())
            <class 'dmdp.apps.datastore.models.Event_2016_12'>
            >>> Event.YM()  # for current month
            <class 'dmdp.apps.datastore.models.Event_2016_12'>
            """
            if month is None:
                if year is None:
                    year = timezone.now()

                month = year.month
                year = year.year

            return module_globals['%s_%04d_%02d' % (name, year, month)]

        model_class.YM = staticmethod(YM)

        def iter_YMs(cls, start_ym=None, end_ym=None):
            """
            Gets all partitions for the model
            from settings.TIMESTAMP_PARTITIONING_START_YM to the current month.
            Boundaries can be overridden.
            """
            for year, month in iter_months(start_ym, end_ym):
                yield cls.YM(year, month)

        model_class.iter_YMs = classmethod(iter_YMs)

        return model_class

    return maker
