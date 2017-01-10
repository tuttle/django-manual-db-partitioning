from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic
from django.utils import timezone

from dmdp.apps.datastore.models import Event, Browser


class Command(BaseCommand):
    help = "Plays with partitions a bit."

    def out(self, msg=None):
        self.stdout.write(
            self.style.SUCCESS(msg) if msg else self.style.NOTICE('------------------------')
        )

    @atomic
    def handle(self, *args, **options):
        # So SQL commands gets logged to console.
        settings.DEBUG = True

        self.play_simple()
        self.play_many()

        # rolls back the database
        raise SystemExit

    def play_simple(self):
        CurBrowser = Browser.YM()
        CurEvent = Event.YM()

        browser = CurBrowser.objects.create(
            ua="That-Mozilla",
        )
        self.out("%s record: %r" % (CurBrowser._meta.object_name, browser))

        event = CurEvent.objects.create(
            timestamp=timezone.now(),
            browser=browser,
        )

        del browser
        self.out()

        event = CurEvent.objects.get(id=event.id)
        self.out("event.browser = %r" % event.browser)

        browser = CurBrowser.objects.get(ua="That-Mozilla")
        self.out('"That-Mozilla".event_set.all() = %r' % browser.event_set.all())

        self.out()

    def iter_last_days(self, number_of_days):
        day = timezone.now()
        delta = timedelta(days=1)
        for _ in xrange(number_of_days):
            yield day
            day -= delta

    def play_many(self):
        """
        Create events for the most recent 50 days pointing to the same browser.
        """

        # Individually

        for day in self.iter_last_days(50):
            browser_id = Browser.YM(day).get_or_create_cached_pk_for(ua='Wget')

            Event.YM(day).objects.create(
                timestamp=day,
                browser_id=browser_id,
            )

        self.out()

        # In bulk

        bulks = defaultdict(list)

        for day in self.iter_last_days(50):
            browser_id = Browser.YM(day).get_or_create_cached_pk_for(ua='Curl')

            EventYM = Event.YM(day)
            bulks[EventYM].append(
                EventYM(
                    timestamp=day,
                    browser_id=browser_id,
                )
            )

        for model, items in bulks.items():
            model.objects.bulk_create(items)

        self.out()

        for BrowserYM, EventYM in zip(Browser.iter_YMs(), Event.iter_YMs()):
            self.out('%s - %s items' % (BrowserYM._meta.object_name, BrowserYM.objects.count()))
            self.out('%s - %s items' % (EventYM._meta.object_name, EventYM.objects.count()))

        self.out()
