from django.conf import settings
from django.core.management.base import BaseCommand

from dmdp.apps.datastore.models import Event, Browser


class Command(BaseCommand):
    help = "Plays with partitions a bit."

    def out(self, msg):
        self.stdout.write(self.style.NOTICE(msg))

    def handle(self, *args, **options):
        # So SQL commands gets logged to console.
        settings.DEBUG = True

        CurBrowser = Browser.YM()
        CurEvent = Event.YM()

        browser, created = CurBrowser.objects.get_or_create(
            ua="That-Mozilla"
        )
        self.out("%s record: %r" % (CurBrowser._meta.object_name, browser))

        event, created = CurEvent.objects.get_or_create(
            browser=browser,
        )

        del browser

        event = CurEvent.objects.get(id=event.id)
        self.out("event.browser = %r" % event.browser)

        browser = CurBrowser.objects.get(ua="That-Mozilla")
        self.out('"That-Mozilla".event_set.all() = %r' % browser.event_set.all())
