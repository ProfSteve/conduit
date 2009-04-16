import conduit

import conduit.utils as Utils
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.dataproviders.BluetoothFactory as BluetoothFactory

import conduit.datatypes.Contact as Contact
import conduit.datatypes.Event as Event

import logging
log = logging.getLogger("modules.syncml")

import threading
import time

try:
    import pysyncml
except ImportError:
    Utils.dataprovider_add_dir_to_path(__file__)
    import pysyncml
import enums

MODULES = {
    "BluetoothSyncmlFactory": { "type": "dataprovider-factory"},
    "SyncmlContactTwoWay": { "type": "dataprovider"},
    "SyncmlEventsTwoWay" : { "type": "dataprovider"},
}


class BluetoothSyncmlFactory(BluetoothFactory.BluetoothFactory):

    def is_interesting(self, id, props):
        return True

    def get_category(self, id, **props):
        return DataProviderCategory.DataProviderCategory(
            props.get("Name", "Bluetooth Device"),
            "phone",
            id)

    def get_dataproviders(self, id, **props):
        return [
            BluetoothContactsProvider,
            BluetoothEventsProvider
        ]


class SyncmlDataProvider(DataProvider.TwoWay):

    def handle_event(self, sync_object, event, userdata, err):
        """ handle_event is called by libsyncml at different stages of a sync
            This includes when this connect and disconnect and when errors occur.

            It WILL happen in a different thread to whatever thread called syncobject.run()
        """
        if event == enums.SML_DATA_SYNC_EVENT_ERROR:
            log.error("An error has occurred")
            #FIXME: log error details
            return

        if event == enums.SML_DATA_SYNC_EVENT_CONNECT:
            log.info("Connect")
            return

        if event == enums.SML_DATA_SYNC_EVENT_DISCONNECT:
            log.info("Disconnect")
            return

        if event == enums.SML_DATA_SYNC_EVENT_FINISHED:
            log.info("Session complete")
            # Unlock the sync thread so it can do its cleanup
            self._refresh_lock.set()
            return

        if event == enums.SML_DATA_SYNC_EVENT_GOT_ALL_ALERTS:
            log.info("Got all alerts")
            if self._session_type == enums.SML_SESSION_TYPE_CLIENT:
                self._syncml_sendall()
                return

        if event == enums.SML_DATA_SYNC_EVENT_GOT_ALL_CHANGES:
            log.info("Got All Changes")
            # unlock the Conduit loop - this allows conduit to process the data we just fetched
            self._refresh_lock.set()
            if self._session_type == enums.SML_SESSION_TYPE_SERVER:
                # don't exit this callback - we want to inject the changes conduit tells us about
                # first.
                self._put_lock.wait(60)
                self._syncml_sendall()
            return

        if event == enums.SML_DATA_SYNC_EVENT_GOT_ALL_MAPPINGS:
            log.info("Got All Mappings")
            return

        log.error("An error has occurred (Unexpected event)")

    def handle_change(self, sync_object, source, type, uid, data, size, userdata, err):
        """ handle_change is called by libsyncml to tells us about changes on the server or device
            we are synchronising to.

            This WILL happen in a different thread to where sync is happening.
        """
        if self._changes == None:
            return 1

        self._changes[uid] = (type, data[:size])

        if self._session_type == enums.SML_SESSION_TYPE_CLIENT:
            err = pysyncml.Error()
            self.syncobj.add_mapping(source, uid, uid, pysyncml.byref(err))

        return 1

    def handle_devinf(self, sync_object, info, userdata, err):
        """ handle_devinf is called by libsyncml to tells us information such as device mfr and firmware
            version of whatever we are syncing against.

            This WILL happen in a different thread to where sync is happening.
            There is a known bug with SE C902 where this is called twice - ignore the 2nd one or crashes
            occur
        """
        return 1

    def _syncml_sendall(self):
        err = pysyncml.Error()
        for t, uid, blob in self._queue:
            self.syncobj.add_change(self.source, t, uid, blob, len(blob), None, pysyncml.byref(err))
        self.syncobj.send_changes(pysyncml.byref(err))
        self._queue = []

    def _syncml_run(self):
        err = pysyncml.Error()

        self._changs = {}

        self._setup_connection()
        self._setup_datastore()

        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_IDENTIFIER, "PC Suite", pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_USE_WBXML, "1", pysyncml.byref(err))

        self._changes = {}

        self.syncobj.register_event_callback(self._handle_event, None)
        self.syncobj.register_change_callback(self._handle_change, None)
        self.syncobj.register_handle_remote_devinf_callback(self._handle_devinf, None)

        if not self.syncobj.init(pysyncml.byref(err)):
            log.error("Unable to prepare synchronisation")
            return

        if not self.syncobj.run(pysyncml.byref(err)):
            log.error("Unable to synchronise")
            return

        log.info("running sync..")

    def __init__(self, address):
        DataProvider.TwoWay.__init__(self)
        self.address = address

        self._handle_event = pysyncml.EventCallback(self.handle_event)
        self._handle_change = pysyncml.ChangeCallback(self.handle_change)
        self._handle_devinf = pysyncml.HandleRemoteDevInfCallback(self.handle_devinf)

        self._refresh_lock = threading.Event()
        self._put_lock = threading.Event()

        self._changes = None
        self._queue = None

    def refresh(self):
        self._changes = {}
        self._queue = []

        self._syncml_run()

        # block here. EventCallback will fire in other thread. When we get GOT_ALL_CHANGES we can unblock here..
        # then we block in the EventCallback until Conduit has queued all its changes. Then we unblock libsyncml.
        # Cripes. Stab my eyes out. NOW.
        self._refresh_lock.wait(60)

    def get_all(self):
        return []

    def get_changes(self):
        a = [key for key, value in self._changes.items() if value[0] == enums.SML_CHANGE_ADD]
        r = [key for key, value in self._changes.items() if value[0] == enums.SML_CHANGE_REPLACE]
        d = [key for key, value in self._changes.items() if value[0] == enums.SML_CHANGE_DELETE]
        return a, r, d

    def get(self, uid):
        type, data = self._changes[uid]
        return self._blob_to_obj(uid, data)

    def put(self, obj, overwrite, LUID=None):
        blob = self._obj_to_blob(obj)

        if LUID == None:
            self._queue.append((enums.SML_CHANGE_ADD, "", blob))
            return conduit.datatypes.Rid(uid=str(hash(blob)), mtime=None, hash=None)

        self._queue.append((enums.SML_CHANGE_REPLACE, uid, blob))
        return conduit.datatypes.Rid(uid=uid, mtime=None, hash=None)

    def delete(self, uid):
        self._queue.append((enums.SML_CHANGE_DELETE, uid, ""))

    def finish(self, a, b, c):
        self._put_lock.set()
        self._refresh_lock.wait(60)
        self._changes
        #self.syncobj.unref(pysyncml.byref(self.syncobj))

        if len(self._queue) > 0 and self._session_type == enums.SML_SESSION_TYPE_CLIENT:
            self._changes = {}
            self._syncml_run()
            self._refresh_lock.wait(60)
            self._refresh_lock.wait(60)
            self._changes = None
            #self.syncobj.unref(pysyncml.byref(self.syncobj))

        time.sleep(10)

        self._queue = None

    def get_UID(self):
        return self.address

    def _blob_to_obj(self, uid, data):
        raise NotImplementedError

    def _obj_to_blob(self, obj):
        raise NotImplementedError


class HttpClientProvider(SyncmlDataProvider):

    def _setup_connection(self):
        err = pysyncml.Error()
        self.syncobj = pysyncml.SyncObject.new(enums.SML_SESSION_TYPE_CLIENT, enums.SML_TRANSPORT_HTTP_CLIENT, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_TRANSPORT_CONFIG_URL, self.address, pysyncml.byref(err))

        self._session_type = enums.SML_SESSION_TYPE_CLIENT


class BluetoothClient(SyncmlDataProvider):

    def _setup_connection(self):
        err = pysyncml.Error()
        self.syncobj = pysyncml.SyncObject.new(enums.SML_SESSION_TYPE_SERVER, enums.SML_TRANSPORT_OBEX_CLIENT, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_CONNECTION_TYPE, enums.SML_DATA_SYNC_CONFIG_CONNECTION_BLUETOOTH, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_TRANSPORT_CONFIG_BLUETOOTH_ADDRESS, self.address, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_TRANSPORT_CONFIG_BLUETOOTH_CHANNEL, "10", pysyncml.byref(err))

        self._session_type = enums.SML_SESSION_TYPE_SERVER


class ContactsProvider(SyncmlDataProvider):

    _name_ = "Contacts"
    _description_ = "Contacts"
    _module_type_ = "twoway"
    _in_type_ = "contact"
    _out_type_ = "contact"
    _icon_ = "contact-new"
    _configurable_ = False

    def _setup_datastore(self):
        err = pysyncml.Error()
        self.syncobj.add_datastore("text/x-vcard", None, "Contacts", pysyncml.byref(err))
        self.source = "Contacts"

    def _blob_to_obj(self, uid, data):
        c = Contact.Contact()
        c.set_UID(uid)
        c.set_from_vcard_string(data)
        return c

    def _obj_to_blob(self, obj):
        return obj.get_vcard_string()


class EventsProvider(SyncmlDataProvider):

    _name_ = "Calendar"
    _description_ = "Calendar"
    _module_type_ = "twoway"
    _in_type_ = "event"
    _out_type_ = "event"
    _icon_ = "x-office-calendar"
    _configurable_ = False

    def _setup_datastore(self):
        err = pysyncml.Error()
        self.syncobj.add_datastore("text/x-vcalendar", None, "Calendar", pysyncml.byref(err))
        self.source = "Calendar"

    def _blob_to_obj(self, uid, data):
        e = Event.Event()
        e.set_UID(uid)
        e.set_from_ical_string(data)
        return e

    def _obj_to_blob(self, obj):
        return obj.get_ical_string()


#FIXME: Need a nicer design here!
class BluetoothContactsProvider(BluetoothClient, ContactsProvider):
    pass
class BluetoothEventsProvider(BluetoothClient, EventsProvider):
    pass

class SyncmlContactTwoWay(HttpClientProvider, ContactsProvider):

    def __init__(self, *args):
        SyncmlDataProvider.__init__(self, "http://localhost:1234")

class SyncmlEventsTwoWay(HttpClientProvider, EventsProvider):

    def __init__(self, *args):
        SyncmlDataProvider.__init__(self, "http://localhost:1234")

