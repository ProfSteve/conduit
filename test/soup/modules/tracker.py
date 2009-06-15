
import soup
import soup.modules

from soup.data.contact import ContactWrapper
from soup.data.event import EventWrapper

import conduit.modules.TrackerModule.TrackerModule as TrackerModule

import tralchemy
from tralchemy import nco, ncal

class TrackerContacts(soup.modules.ModuleWrapper):

    klass = TrackerModule.TrackerContacts
    dataclass = ContactWrapper

    def create_dataprovider(self):
        for contact in nco.PersonContact.get():
            contact.delete()
        return self.klass()

    def destroy_dataprovider(self):
        pass

class TrackerCalendar(soup.modules.ModuleWrapper):

    klass = TrackerModule.TrackerCalendar
    dataclass = EventWrapper

    def create_dataprovider(self):
        for event in ncal.Event.get():
            event.delete()
        return self.klass()

    def destroy_dataprovider(self):
        pass
