import conduit.utils as Utils
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.dataproviders.BluetoothFactory as BluetoothFactory

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
            print "ERRROR"
        elif event == enums.SML_DATA_SYNC_EVENT_CONNECT:
            print "Connect"
        elif event == enums.SML_DATA_SYNC_EVENT_GOT_ALL_ALERTS:
            print "Got all alerts"
        elif event == enums.SML_DATA_SYNC_EVENT_GOT_ALL_CHANGES:
            print "Got All Changes"
        elif event == enums.SML_DATA_SYNC_EVENT_GOT_ALL_MAPPINGS:
            print "Got All Mappings"
        elif event == enums.SML_DATA_SYNC_EVENT_DISCONNECT:
            print "Disconnect"
        elif event == enums.SML_DATA_SYNC_EVENT_FINISHED:
            print "Finished"
        else:
            print "Unexpected error"

    def handle_change(self, sync_object, source, type, uid, data, size, userdata, err):
        if type == enums.SML_CHANGE_ADD:
            pass
        elif type == enums.SML_CHANGE_REPLACE:
            pass
        elif type == enums.SML_CHANGE_DELETE:
            pass
        print "CHANGE CHANGE CHANGE"
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

    def refresh(self):
        err = pysyncml.Error()
        self.syncobj = pysyncml.SyncObject.new(enums.SML_SESSION_TYPE_SERVER, enums.SML_TRANSPORT_OBEX_CLIENT, pysyncml.byref(err))

        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_CONNECTION_TYPE, enums.SML_DATA_SYNC_CONFIG_CONNECTION_BLUETOOTH, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_TRANSPORT_CONFIG_BLUETOOTH_ADDRESS, self.address, pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_TRANSPORT_CONFIG_BLUETOOTH_CHANNEL, "10", pysyncml.byref(err))

        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_IDENTIFIER, "PC Suite", pysyncml.byref(err))
        self.syncobj.set_option(enums.SML_DATA_SYNC_CONFIG_USE_WBXML, "1", pysyncml.byref(err))

        self.syncobj.add_datastore("text/x-vcard", None, "Contacts", pysyncml.byref(err))

        self.syncobj.register_event_callback(self._handle_event, None)
        self.syncobj.register_change_callback(self._handle_change, None)
        self.syncobj.register_handle_remote_devinf_callback(self._handle_devinf, None)

        if not self.syncobj.init(pysyncml.byref(err)):
            print "FAIL!!!"
            return

        if not self.syncobj.run(pysyncml.byref(err)):
            print "RUN FAIL!!!"
            return
        print "running..."

    def get_all(self):
        return []

    def get_UID(self):
        return self.address

class ContactsProvider(SyncmlDataProvider):

    _name_ = "Contacts"
    _description_ = "Contacts"
    _module_type_ = "twoway"
    _in_type_ = "contact"
    _out_type_ = "contact"
    _icon_ = "contact-new"
    _configurable_ = False
    
