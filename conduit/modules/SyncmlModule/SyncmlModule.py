import conduit.utils as Utils
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.dataproviders.BluetoothFactory as BluetoothFactory

import logging
log = logging.getLogger("modules.syncml")

import threading

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
            ContactsProvider
        ]


class SyncmlDataProvider(DataProvider.TwoWay):

    def handle_event(self, sync_object, event, userdata, err):
        if event == enums.SML_DATA_SYNC_EVENT_ERROR:
            log.error("An error has occurred")
        elif event == enums.SML_DATA_SYNC_EVENT_CONNECT:
            log.info("Connect")
        elif event == enums.SML_DATA_SYNC_EVENT_GOT_ALL_ALERTS:
            log.info("Got all alerts")
        elif event == enums.SML_DATA_SYNC_EVENT_GOT_ALL_CHANGES:
            log.info("Got All Changes")
            # unlock the Conduit loop - this allows conduit to process the data we just fetched
            self._refresh_lock.set()
            # don't exit this callback - we want to inject the changes conduit tells us about
            # first.
            #self._put_lock.wait(60)
            #self.syncobj.send_changes(byref(err))
        elif event == enums.SML_DATA_SYNC_EVENT_GOT_ALL_MAPPINGS:
            log.info("Got All Mappings")
        elif event == enums.SML_DATA_SYNC_EVENT_DISCONNECT:
            log.info("Disconnect")
        elif event == enums.SML_DATA_SYNC_EVENT_FINISHED:
            log.info("Finished")
        else:
            log.error("An error has occurred (Unexpected event)")

    def handle_change(self, sync_object, source, type, uid, data, size, userdata, err):
        self._changes[uid] = (type, data[:size])
        return 1

    def handle_devinf(self, sync_object, info, userdata, err):
        print "DEVINF!"
        return 1

    def __init__(self, address):
        DataProvider.TwoWay.__init__(self)
        self.address = address

        self._handle_event = pysyncml.EventCallback(self.handle_event)
        self._handle_change = pysyncml.ChangeCallback(self.handle_change)
        self._handle_devinf = pysyncml.HandleRemoteDevInfCallback(self.handle_devinf)

        self._refresh_lock = threading.Event()
        self._put_lock = threading.Event()

        self._changes = None

    def refresh(self):
        err = pysyncml.Error()
        self.syncobj = pysyncml.SyncObject.new(enums.SML_SESSION_TYPE_SERVER, enums.SML_TRANSPORT_OBEX_CLIENT, pysyncml.byref(err))

        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_CONNECTION_TYPE, enums.SML_DATA_SYNC_CONFIG_CONNECTION_BLUETOOTH, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_TRANSPORT_CONFIG_BLUETOOTH_ADDRESS, self.address, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_TRANSPORT_CONFIG_BLUETOOTH_CHANNEL, "10", pysyncml.byref(err))

        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_IDENTIFIER, "PC Suite", pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_USE_WBXML, "1", pysyncml.byref(err))

        self.syncobj.add_datastore("text/x-vcard", None, "Contacts", pysyncml.byref(err))
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

        # block here. EventCallback will fire in other thread. When we get GOT_ALL_CHANGES we can unblock here..
        # then we block in the EventCallback until Conduit has queued all its changes. Then we unblock libsyncml.
        # Cripes. Stab my eyes out. NOW.
        self._refresh_lock.wait(60)

    def get_all(self):
        return []

    def get_changes(self):
        return self._changes.keys()

    def get(self, uid):
        type, data = self._changes[uid]
        return self._blob_to_obj(uid, data)

    def put(self, obj, overwrite, LUID=None):
        err = syncml.Error()
        blob = self._obj_to_blob(obj)

        if LUID == None:
            self.syncobj.add_change(self.source, enums.SML_CHANGE_ADD, "", blob, len(blob), null, byref(err))
            return None

        self.syncobj.add_change(self.source, enums.SML_CHANGE_REPLACE, uid, blob, len(blob), null, byref(err))
        return None

    def delete(self, uid):
        err = syncml.Error()
        self.syncobj.add_change(self.source, enums.SML_CHANGE_DELETE, uid, "", 0, null, byref(err))

    def finish(self):
        self._put_lock.set()
        self._changes = None

    def get_UID(self):
        return self.address

    def _blob_to_obj(self, uid, data):
        raise NotImplementedError

    def _obj_to_blob(self, obj):
        raise NotImplementedError


class ContactsProvider(SyncmlDataProvider):

    _name_ = "Contacts"
    _description_ = "Contacts"
    _module_type_ = "twoway"
    _in_type_ = "contact"
    _out_type_ = "contact"
    _icon_ = "contact-new"
    _configurable_ = False
    
    def _blob_to_obj(self, uid, data):
        c = Contact.Contact()
        c.set_UID(c)
        c.set_from_vcard_string(data)
        return c

    def _obj_to_blob(self, obj):
        return obj.get_vcard_string()

