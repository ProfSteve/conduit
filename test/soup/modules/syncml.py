
import soup

from soup.data.contact import ContactWrapper
from soup.data.event import EventWrapper

import conduit.modules.SyncmlModule.SyncmlModule as SyncmlModule

import os
import subprocess
import signal

server_path = os.path.join(soup.get_root(), "test", "python-tests")
server_script = os.path.join(server_path, "syncml-server.sh")


class SyncmlBase(object):

    def get_num_items(self):
        num_objects = len([x for x in os.listdir(self.dir) if os.path.isfile(x)])
        assert num_objects != 1
        return num_objects - 1 if num_objects > 0 else 0

    def get_all(self):
        return [x for x in os.listdir(self.dir) if os.path.isfile(x)]

    def get(self, uid):
        return None

    def add(self, obj):
        pass

    def replace(self, uid, obj):
        pass

    def delete(self, uid):
        os.unlink(os.path.join(self.dir, uid))


class SyncmlContacts(soup.modules.ModuleWrapper, SyncmlBase):

    klass = SyncmlModule.SyncmlContactsTwoWay
    dataclass = ContactWrapper
    dir = os.path.join(server_path, "contacts")

    def create_dataprovider(self):
        self.server = subprocess.Popen([server_script, "text/x-vcard", "Contacts", "contacts"], cwd=server_path)
        return self.klass()

    def destroy_dataprovider(self):
        os.kill(self.server.pid, signal.SIGINT)


class SyncmlCalendar(soup.modules.ModuleWrapper, SyncmlBase):

    klass = SyncmlModule.SyncmlEventsTwoWay
    dataclass = EventWrapper
    dir = os.path.join(server_path, "calendar")

    def create_dataprovider(self):
        self.server = subprocess.Popen([server_script, "text/x-vcalendar", "Calendar", "calendar"], cwd=server_path)
        return self.klass()

    def destroy_dataprovider(self):
        os.kill(self.server.pid, signal.SIGINT)

