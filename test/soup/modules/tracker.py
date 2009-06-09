
import soup
import soup.modules

from soup.data.contact import ContactWrapper
from soup.data.event import EventWrapper

import conduit.modules.TrackerModule.TrackerModule as TrackerModule

class TrackerContacts(soup.modules.ModuleWrapper):

    klass = TrackerModule.TrackerContacts
    dataclass = ContactWrapper

    def create_dataprovider(self):
        return self.klass()


class TrackerCalendar(soup.modules.ModuleWrapper):

    klass = TrackerContacts.TrackerCalendar
    dataclass = EventWrapper

    def create_dataprovider(self):
        return self.klass()


