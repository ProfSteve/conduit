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
import uuid

try:
    import pysyncml
except ImportError:
    Utils.dataprovider_add_dir_to_path(__file__)
    import pysyncml
import enums

MODULES = {
    "BluetoothSyncmlFactory": { "type": "dataprovider-factory"},
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

    _syncml_version_ = "1.1"
    _syncml_identifier_ = "PC Suite"

    def handle_event(self, sync_object, event, userdata, err):
        """ handle_event is called by libsyncml at different stages of a sync
            This includes when this connect and disconnect and when errors occur.

            It WILL happen in a different thread to whatever thread called syncobject.run()
        """
        if event == enums.SML_DATA_SYNC_EVENT_ERROR:
            log.error("An error has occurred: %s" % err.message)
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
                self._put_lock.clear()
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

        LUID = None
        for k, v in self.mapping.iteritems():
            if v == uid:
                LUID = k

        if LUID == None:
            LUID = str(uuid.uuid4())
            self.mapping[LUID] = uid

        log.debug("Got change: %s (LUID: %s)" % (uid, LUID))

        self._changes[LUID] = (type, data[:size])

        if self._session_type == enums.SML_SESSION_TYPE_CLIENT:
            log.debug("Adding mapping")
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

    def handle_change_status(self, sync_object, code, newuid, userdata, err):
        if code < 200 or 299 < code:
            return 0
        self.mapping[userdata] = newuid
        return 1

    def handle_get_anchor(self, sync_object, name, userdata, err):
        anchor = self.anchor[name] if name in self.anchor else None
        log.debug("get_anchor('%s') returns %s" % (name, anchor or "None"))
        return pysyncml.strdup(anchor) if anchor else None

    def handle_set_anchor(self, sync_object, name, value, userdata, err):
        log.debug("set_anchor('%s', '%s')" % (name, value))
        self.anchor[name] = value
        return 1

    def handle_get_alert_type(self, sync_object, source, alert_type, userdata, err):
        if alert_type == enums.SML_ALERT_SLOW_SYNC:
            log.debug("Remote requested slowsync")
            self.slowsync = True
        else:
            log.debug("Remote requested normal sync")
            self.slowsync = False

        if len(self.anchor) == 0:
            log.debug("We have no anchors, requesting slowsync")
            self.slowsync = True

        if self.slowsync == True:
            log.debug("Going to do a slowsync")
            alert_type = enums.SML_ALERT_SLOW_SYNC

        return alert_type

    def _syncml_sendall(self):
        err = pysyncml.Error()
        for t, LUID, uid, blob in self._queue:
            self.syncobj.add_change(self._store_, t, uid, blob if len(blob) > 0 else None, len(blob), LUID, pysyncml.byref(err))
        self.syncobj.send_changes(pysyncml.byref(err))
        self._queue = []

    def _syncml_run(self):
        err = pysyncml.Error()

        self._setup_connection()
        self._setup_datastore()

        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_VERSION, self._syncml_version_, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_IDENTIFIER, self._syncml_identifier_, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_USE_WBXML, "1", pysyncml.byref(err))

        self.slowsync = False
        self._changes = {}

        self.syncobj.register_event_callback(self._handle_event, None)
        self.syncobj.register_change_callback(self._handle_change, None)
        self.syncobj.register_handle_remote_devinf_callback(self._handle_devinf, None)
        self.syncobj.register_change_status_callback(self._handle_change_status)
        self.syncobj.register_set_anchor_callback(self._handle_set_anchor, None)
        self.syncobj.register_get_anchor_callback(self._handle_get_anchor, None)
        self.syncobj.register_get_alert_type_callback(self._handle_get_alert_type, None)

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

        self.running = False

        self.anchor = {}
        self.mapping = {}
        self.slowsync = False

        self._handle_event = pysyncml.EventCallback(self.handle_event)
        self._handle_change = pysyncml.ChangeCallback(self.handle_change)
        self._handle_devinf = pysyncml.HandleRemoteDevInfCallback(self.handle_devinf)
        self._handle_change_status = pysyncml.ChangeStatusCallback(self.handle_change_status)
        self._handle_get_anchor = pysyncml.GetAnchorCallback(self.handle_get_anchor)
        self._handle_set_anchor = pysyncml.SetAnchorCallback(self.handle_set_anchor)
        self._handle_get_alert_type = pysyncml.GetAlertTypeCallback(self.handle_get_alert_type)

        self._refresh_lock = threading.Event()
        self._put_lock = threading.Event()

        self._changes = None
        self._queue = None

    def refresh(self):
        self.running = True
        self._queue = []

        self._syncml_run()

        # block here. EventCallback will fire in other thread. When we get GOT_ALL_CHANGES we can unblock here..
        # then we block in the EventCallback until Conduit has queued all its changes. Then we unblock libsyncml.
        # Cripes. Stab my eyes out. NOW.
        self._refresh_lock.wait(60)
        self._refresh_lock.clear()

    def get_all(self):
        return [key for key, value in self._changes.items() if value[0] == enums.SML_CHANGE_ADD or value[0] == enums.SML_CHANGE_REPLACE]

    def get_changes(self):
        # If we end up doing a syncml slowsync we will end up getting all data from the device - so we can't use
        # the get_changes machinery.
        if self.slowsync == True:
            raise NotImplementedError

        # Just report changes to sync engine
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
            LUID = str(uuid.uuid4())
            log.debug("Adding data object with new LUID (%s)" % LUID)
            self._queue.append((enums.SML_CHANGE_ADD, LUID, "", blob))
            return conduit.datatypes.Rid(uid=LUID, hash=hash(blob))

        log.debug("Updating data object with existing LUID (%s)" % LUID)
        self._queue.append((enums.SML_CHANGE_REPLACE, LUID, self.mapping[LUID], blob))
        return conduit.datatypes.Rid(uid=LUID, hash=hash(blob))

    def delete(self, LUID):
        self._queue.append((enums.SML_CHANGE_DELETE, LUID, self.mapping[LUID], ""))

    def finish(self, a, b, c):
        if not self.running:
            return

        self._put_lock.set()
        self._refresh_lock.wait(60)
        self._refresh_lock.clear()
        self._changes
        self.syncobj.unref(pysyncml.byref(self.syncobj))

        if len(self._queue) > 0 and self._session_type == enums.SML_SESSION_TYPE_CLIENT:
            self._changes = {}
            self._syncml_run()
            self._refresh_lock.wait(60)
            self._refresh_lock.clear()
            self._refresh_lock.wait(60)
            self._refresh_lock.clear()
            self._changes = None
            self.syncobj.unref(pysyncml.byref(self.syncobj))

        self._queue = None
        self.running = False

    def get_UID(self):
        return self.address

    def _blob_to_obj(self, uid, data):
        raise NotImplementedError

    def _obj_to_blob(self, obj):
        raise NotImplementedError


class HttpClient(SyncmlDataProvider):

    _configurable_ = True

    def __init__(self):
        SyncmlDataProvider.__init__(self, self._address_)
        self.update_configuration(
            username = "",
            password = ""
        )

    def _setup_connection(self):
        err = pysyncml.Error()
        self.syncobj = pysyncml.SyncObject.new(enums.SML_SESSION_TYPE_CLIENT, enums.SML_TRANSPORT_HTTP_CLIENT, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_TRANSPORT_CONFIG_URL, self._address_, pysyncml.byref(err))

        if self.username != None and len(self.username) > 0:
            self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_AUTH_USERNAME, self.username, pysyncml.byref(err))
            self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_AUTH_PASSWORD, self.password, pysyncml.byref(err))

        self._session_type = enums.SML_SESSION_TYPE_CLIENT

    def config_setup(self, config):
        config.add_section("Account details")
        config.add_item("Login", "text",
            config_name = "username"
        )
        config.add_item("Password", "text",
            config_name = "password",
            password = True
        )

    def is_configured(self, isSource, isTwoWay):
        if len(self.username) > 0 and len(self.password) > 0:
            return True
        return False

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

    _store_ = "Contacts"
    _mime_ = "text/x-vcard"

    def _setup_datastore(self):
        err = pysyncml.Error()
        self.syncobj.add_datastore(self._mime_, None, self._store_, pysyncml.byref(err))

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

    _store_ = "Calendar"
    _mime_ = "text/x-calendar"

    def _setup_datastore(self):
        err = pysyncml.Error()
        self.syncobj.add_datastore(self._mime_, None, self._store_, pysyncml.byref(err))

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

CATEGORY_SYNCMLTEST = DataProviderCategory.DataProviderCategory("Syncml Test")

class SyncmlContactsTwoWay(HttpClient, ContactsProvider):
    _address_ = "http://localhost:1234"
    _category_ = CATEGORY_SYNCMLTEST
MODULES['SyncmlContactsTwoWay'] = {"type":"dataprovider"}

class SyncmlEventsTwoWay(HttpClient, EventsProvider):
    _address_ = "http://localhost:1234"
    _category_ = CATEGORY_SYNCMLTEST
MODULES['SyncmlEventsTwoWay'] = {"type":"dataprovider"}

CATEGORY_SCHEDULEWORLD = DataProviderCategory.DataProviderCategory("ScheduleWorld", "applications-office")

class ScheduleWorldContacts(HttpClient, ContactsProvider):
    _address_ = "http://sync.scheduleworld.com/funambol/ds"
    _store_ = "card3"
    _mime_ = "text/vcard"
    _syncml_version_ = "1.2"
    _category_ = CATEGORY_SCHEDULEWORLD
MODULES['ScheduleWorldContacts'] = {"type":"dataprovider"}

class ScheduleWorldCalendar(HttpClient, EventsProvider):
    _address_ = "http://sync.scheduleworld.com/funambol/ds"
    _store_ = "cal2"
    _mime_ = "text/calendar"
    _syncml_version_ = "1.2"
    _category_ = CATEGORY_SCHEDULEWORLD
MODULES['ScheduleWorldCalendar'] = {"type":"dataprovider"}

