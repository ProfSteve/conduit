import gobject
import dbus

import conduit.dataproviders.SimpleFactory as SimpleFactory

class BluetoothFactory(SimpleFactory.SimpleFactory):

    def __init__(self, **kwargs):
        SimpleFactory.SimpleFactory.__init__(self, **kwargs)

        try:
            self.bus = dbus.SystemBus()
            self.bluez = dbus.Interface(self.bus.get_object("org.bluez", "/"), "org.bluez.Manager")

            adapter_path = self.bluez.DefaultAdapter()
            self.adapter = dbus.Interface(self.bus.get_object("org.bluez", adapter_path), "org.bluez.Adapter")

            self.adapter.connect_to_signal("DeviceCreated", self._device_created)
            # self.adapter.connect_to_signal("DeviceRemoved", self._device_removed)

            # FIXME: Need to listen to property changes and not show paired devices?
        except:
            pass

    def _maybe_new(self, device):
        properties = device.GetProperties()

        props = {}
        props['Name'] = str(properties['Name'])
        props['Alias'] = str(properties['Alias'])
        props['Address'] = str(properties['Address'])
        props['Paired'] = bool(properties['Paired'])
        props['Connected'] = bool(properties['Connected'])
        props['Trusted'] = bool(properties['Trusted'])
        props['Object'] = device

        if self.is_interesting(props['Address'], props):
            self.item_added(props['Address'], **props)

    def _device_created(self, device_path):
        device = dbus.Interface(self.bus.get_object("org.bluez", device_path), "org.bluez.Device")
        self._maybe_new(device)

    def probe(self):
        try:
            for device_path in self.adapter.ListDevices():
                device = dbus.Interface(self.bus.get_object("org.bluez", device_path), "org.bluez.Device")
                self._maybe_new(device) 
        except:
            pass

    def get_args(self, id, **kwargs):
        return (id, )

    def is_interesting(self, address, props):
        return props['Paired'] == true

