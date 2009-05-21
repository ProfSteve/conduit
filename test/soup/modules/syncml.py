
import soup

from soup.data.contact import ContactWrapper
from soup.data.event import EventWrapper

import conduit.modules.SyncmlModule as SyncmlModule

import os
import subprocess
import signal

server_path = os.path.join(soup.get_root(), "test", "python-tests", "syncml-server.sh")
server_script = os.path.join(server_path, "syncml-server.sh")


class SyncmlContacts(soup.modules.ModuleWrapper):

    klass = SyncmlModule.SyncmlContactsTwoWay
    dataclass = ContactWrapper

    def create_dataprovider(self):
        self.server = subprocess.Popen([server_script, "text/x-vcard", "Contacts", "contacts"], cwd=server_path)
        return self.klass()

    def destroy_dataprovider(self):
        os.kill(self.server.pid, signal.SIGINT)


class SyncmlCalendar(soup.modules.ModuleWrapper):

    klass = SyncmlModule.SyncmlEventsTwoWay
    dataclass = EventsWrapper

    def create_dataprovider(self):
        self.server = subprocess.Popen([server_script, "text/x-vcalendar", "Calendar", "calendar"], cwd=server_path)
        return self.klass()

    def destroy_dataprovider(self):
        os.kill(self.server.pid, signal.SIGINT)
