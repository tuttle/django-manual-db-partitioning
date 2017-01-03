from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import rollback, atomic

from dmdp.apps.datastore.models import Event, Browser


CurBrowser = Browser.YM()
CurEvent = Event.YM()


class Command(BaseCommand):
    help = "Plays with partitions a bit."

    def out(self, msg):
        self.stdout.write(self.style.NOTICE(msg))

    def play_simple(self):
        browser = CurBrowser.objects.create(
            ua="That-Mozilla",
        )
        self.out("%s record: %r" % (CurBrowser._meta.object_name, browser))

        event = CurEvent.objects.create(
            browser=browser,
        )

        del browser

        event = CurEvent.objects.get(id=event.id)
        self.out("event.browser = %r" % event.browser)

        browser = CurBrowser.objects.get(ua="That-Mozilla")
        self.out('"That-Mozilla".event_set.all() = %r' % browser.event_set.all())

    @atomic
    def handle(self, *args, **options):
        # So SQL commands gets logged to console.
        settings.DEBUG = True

        self.play_simple()



        # rolls back the database
        raise SystemExit
